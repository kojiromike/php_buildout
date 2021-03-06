import hexagonit.recipe.download
import imp
import logging
import os
import shutil
import zc.buildout

class PhpExt(object):
    """zc.buildout recipe for compiling and installing software"""

    def __init__(self, buildout, name, options):
        self.options = options
        self.buildout = buildout
        self.name = name

        log = logging.getLogger(self.name)

        options['location'] = os.path.join(
            buildout['buildout']['parts-directory'],
            self.name)
        options['prefix'] = options.get('prefix', options['location'])
        options['url'] = options.get('url', '').strip()
        options['path'] = options.get('path', '').strip()

        if options['url'] and options['path']:
            raise zc.buildout.UserError('You must use either "url" or "path", not both!')
        if not (options['url'] or options['path']):
            raise zc.buildout.UserError('You must provide either "url" or "path".')

        if options['url']:
            options['compile-directory'] = '%s__compile__' % options['location']
        else:
            options['compile-directory'] = options['path']
        
        self.environ = {}
        environment_section = self.options.get('environment-section', '').strip()
        if environment_section and environment_section in buildout:
            # Use environment variables from the designated config section.
            self.environ.update(buildout[environment_section])
        for variable in self.options.get('environment', '').splitlines():
            if variable.strip():
                try:
                    key, value = variable.split('=', 1)
                    self.environ[key.strip()] = value
                except ValueError:
                    raise zc.buildout.UserError('Invalid environment variable definition: %s', variable)
        for key in self.environ:
            self.environ[key] = self.environ[key] % os.environ

    def update(self):
        pass

    def run(self, cmd):
        log = logging.getLogger(self.name)
        if os.system(cmd):
            log.error('Error executing command: %s' % cmd)
            raise zc.buildout.UserError('System error')

    def install(self):
        log = logging.getLogger(self.name)
        parts = []

        php_location = self.options.get('php-location', '/usr').strip()
        phpize_cmd = php_location + '/bin/phpize'

        make_cmd = self.options.get('make-binary', 'make').strip()
        make_targets = ' '.join(self.options.get('make-targets', 'install').split())

        configure_cmd = self.options.get('configure-command', './configure')
        configure_options = self.options.get('configure-options','').split()

        # Add the prefix only if we're using a configure script
        if 'configure' in configure_cmd:
            configure_options.insert(0, '--prefix=%s' % php_location)
            php_config = php_location + '/bin/php-config'
            configure_options.insert(1, '--with-php-config=%s' % php_config)

        patch_cmd = self.options.get('patch-binary', 'patch').strip()
        patch_options = ' '.join(self.options.get('patch-options', '-p0').split())
        patches = self.options.get('patches', '').split()
        
        if self.environ:
            for key in sorted(self.environ.keys()):
                log.info('[ENV] %s = %s', key, self.environ[key])
            os.environ.update(self.environ)

        # Download the source using hexagonit.recipe.download
        if self.options['url']:
            compile_dir = self.options['compile-directory']
            os.mkdir(compile_dir)
        
            try:
                opt = self.options.copy()
                opt['destination'] = compile_dir
                hexagonit.recipe.download.Recipe(
                    self.buildout, self.name, opt).install()
            except:
                shutil.rmtree(compile_dir)
                raise
        else:
            log.info('Using local source directory: %s' % self.options['path'])
            compile_dir = self.options['path']


        def is_build_dir():
            return os.path.isfile('configure') or os.path.isfile('Makefile.PL')

        if not os.path.isfile(compile_dir + os.sep + 'package.xml'):
            log.error('Unable to find the package.xml')
            raise zc.buildout.UserError('Invalid pecl/pear package contents')

        for entry in os.listdir(compile_dir):
            if not entry.endswith('.xml'):
                compile_dir += os.sep + entry

        os.chdir(compile_dir)


        try:
            if patches:
                log.info('Applying patches')
                for patch in patches:
                    self.run('%s %s < %s' % (patch_cmd, patch_options, patch))

            self.run('%s' % phpize_cmd)

            if 'pre-configure-hook' in self.options and len(self.options['pre-configure-hook'].strip()) > 0:
                log.info('Executing pre-configure-hook')
                self.call_script(self.options['pre-configure-hook'])

            if not is_build_dir():
                contents = os.listdir(compile_dir)
                if len(contents) == 1:
                    os.chdir(contents[0])
                    if not is_build_dir():
                        log.error('Unable to find the configure script')
                        raise zc.buildout.UserError('Invalid package contents')
                else:
                    log.error('Unable to find the configure script')
                    raise zc.buildout.UserError('Invalid package contents')
            
            self.run('%s %s' % (configure_cmd, ' '.join(configure_options)))

            if 'pre-make-hook' in self.options and len(self.options['pre-make-hook'].strip()) > 0:
                log.info('Executing pre-make-hook')
                self.call_script(self.options['pre-make-hook'])

            self.run(make_cmd)
            self.run('%s %s' % (make_cmd, make_targets))

            if 'post-make-hook' in self.options and len(self.options['post-make-hook'].strip()) > 0:
                log.info('Executing post-make-hook')
                self.call_script(self.options['post-make-hook'])

        except:
            log.error('Compilation error. The package is left as is at %s where '
                      'you can inspect what went wrong' % os.getcwd())
            raise

        if self.options['url']:
            if self.options.get('keep-compile-dir', '').lower() in ('true', 'yes', '1', 'on'):
                # If we're keeping the compile directory around, add it to
                # the parts so that it's also removed when this recipe is
                # uninstalled.
                parts.append(self.options['compile-directory'])
            else:
                shutil.rmtree(self.options['compile-directory'])
                del self.options['compile-directory']

        return parts

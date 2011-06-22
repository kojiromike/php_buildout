"""
Recipe for setting up ejabberd.
Derived from rod.recipe.ejabberd.
"""

import logging
import os
import string
from glob import glob
import random
import shutil
import subprocess
import sys
import stat
import tempfile
import urllib
import zc.recipe.egg
import py

logger = logging.getLogger(__name__)


class Recipe(zc.recipe.egg.Eggs):
    """Buildout recipe for installing ejabberd."""

    def __init__(self, buildout, name, options):
        """Standard constructor for zc.buildout recipes."""
        options['location'] = os.path.join(
            buildout['buildout']['parts-directory'],
            name)

        options['compile-directory'] = '%s__compile__' % options['location']
        super(Recipe, self).__init__(buildout, name, options)

    def gen_scripts(self):
        """Generates ejabberd and ejabberdctl scripts."""

        bindir = self.buildout['buildout']['bin-directory']
        prefix = self.options.get('prefix', os.getcwd())
        erlang_path = self.options.get(
            'erlang-path', '/usr/local/lib/erlang/bin')
        ejabberd_part = os.path.join(
            self.buildout['buildout']['parts-directory'], self.name)
        ejabberd_node = self.name + '@' + 'localhost'

        ejabberd_template = """#!/bin/sh
ERL=%(erlang_path)s/erl
ROOT=%(prefix)s
PART=%(ejabberd_part)s

[ -d $ROOT/var/ejabberd ] || mkdir -p $ROOT/var/ejabberd

[ -f $ROOT/etc/ejabberd.cfg ] || EJABBERD_CONFIG_PATH=$PART/etc/ejabberd/ejabberd.cfg
[ -f $ROOT/etc/ejabberd.cfg ] && EJABBERD_CONFIG_PATH=$ROOT/etc/ejabberd.cfg

export EJABBERD_CONFIG_PATH
export EJABBERD_LOG_PATH=$ROOT/var/ejabberd/ejabberd.log
export ERL_INETRC=$PART/etc/ejabberd/inetrc
export HOME=$ROOT/var/ejabberd

exec $ERL \\
    -pa $PART/lib/ejabberd/ebin $PART/lib/modules/*/ebin \\
    -sname ejabberd@localhost \\
    -noinput \\
    -s ejabberd \\
    -boot start_sasl \\
    -sasl sasl_error_logger '{file,"'$HOME/ejabberd_sasl.log'"}' \\
    +W w \\
    +K true \\
    -smp auto \\
    +P 250000 \\
    -mnesia dir "\\"${HOME}\\""
""" % locals()

        script_path = os.path.join(bindir, 'ejabberd')
        script = open(script_path, "w")
        script.write(ejabberd_template)
        script.close()
        os.chmod(script_path, 0755)

        ejabberdctl_template = """#!/bin/sh
ERL=%(erlang_path)s/erl
ROOT=%(prefix)s
PART=%(ejabberd_part)s

[ -d $ROOT/var/ejabberd ] || mkdir -p $ROOT/var/ejabberd

[ -f $ROOT/etc/ejabberd.cfg ] || EJABBERD_CONFIG_PATH=$PART/etc/ejabberd/ejabberd.cfg
[ -f $ROOT/etc/ejabberd.cfg ] && EJABBERD_CONFIG_PATH=$ROOT/etc/ejabberd.cfg

export EJABBERD_CONFIG_PATH
export EJABBERD_LOG_PATH=$ROOT/var/ejabberd/ejabberd.log
export ERL_INETRC=$PART/etc/ejabberd/inetrc
export HOME=$ROOT/var/ejabberd

ARGS=$@
sh -c "$ERL -sname ctl-%(ejabberd_node)s -hidden -pa $PART/lib/ejabberd/ebin -s ejabberd_ctl -extra %(ejabberd_node)s $ARGS"
""" % locals()

        script_path = os.path.join(bindir, 'ejabberdctl')
        script = open(script_path, "w")
        script.write(ejabberdctl_template)
        script.close()
        os.chmod(script_path, 0755)

        rest_connect_location = os.path.join(ejabberd_part, 'rest_connect')
        rest_connect_template = """#!/bin/sh
cd %(rest_connect_location)s
exec erl -sname rest_connect -pa $PWD/ebin $PWD/deps/*/ebin -boot start_sasl -s rest_connect -extra %(prefix)s/etc/rest_connect.cfg $@
""" % locals()

        script_path = os.path.join(bindir, 'ejabberd_rest_connect')
        script = open(script_path, "w")
        script.write(rest_connect_template)
        script.close()
        os.chmod(script_path, 0755)

    def run(self, cmd):
        log = logging.getLogger(self.name)
        if os.system(cmd):
            log.error('Error executing command: %s' % cmd)
            raise zc.buildout.UserError('System error')

    def install_svn_module(self, name, url):
        """Export and install an ejabberd module from svn"""
        logger.info("Installing ejabberd module '%s'..." % name)
        build_dir = tempfile.mkdtemp("buildout-ejabberd-module-" + name)
        os.chdir(build_dir)
        wc = py.path.svnwc('svn_export')
        out = wc.checkout(url)
        if out:
            logger.info(out)
        os.chdir('svn_export')
        self.run('./build.sh')
        ignore_pat = shutil.ignore_patterns('.svn', '.git', 'src',
                                            'Makefile', '*.template'
                                            'build.sh', 'build.bat',
                                            'Emakefile', 'INSTALL'
                                            )
        modules_dir = os.path.join(self.options['location'], 'lib', 'modules')
        if not os.path.exists(modules_dir):
            os.makedirs(modules_dir)
        shutil.copytree(os.path.join(build_dir, 'svn_export'),
                        os.path.join(modules_dir, name), ignore=ignore_pat)

    def install_ejabberd(self):
        """Downloads and installs ejabberd."""
        parts = []

        arch_filename = self.options['url'].split(os.sep)[-1]
        if os.path.isdir(self.options.get('url')):
            src = self.options.get('url')
        else:
            downloads_dir = os.path.join(os.getcwd(), 'downloads')
            if not os.path.isdir(downloads_dir):
                os.mkdir(downloads_dir)
                src = os.path.join(downloads_dir, arch_filename)
                if not os.path.isfile(src):
                    logger.info("downloading ejabberd distribution...")
                    urllib.urlretrieve(self.options['url'], src)
                else:
                    logger.info("ejabberd distribution already downloaded.")


        extract_dir = self.options['compile-directory']
        remove_after_install = [extract_dir]
        is_ext = arch_filename.endswith
        is_archive = True
        if is_ext('.tar.gz') or is_ext('.tgz'):
            call = ['tar', 'xzf', src, '-C', extract_dir]
        elif is_ext('.zip'):
            call = ['unzip', src, '-d', extract_dir]
        else:
            is_archive = False

        if is_archive:
            retcode = subprocess.call(call)
            if retcode != 0:
                raise Exception("extraction of file %r failed (compile-dir: %r)" %
                                (arch_filename, extract_dir))
        else:
            shutil.copytree(src, os.path.join(extract_dir, arch_filename))

        erlang_path = self.options.get('erlang-path',
                                       '/usr/local/lib/erlang/bin')

        part_dir = self.buildout['buildout']['parts-directory']
        dst = os.path.join(part_dir, self.name)
        self.options['location'] = dst

        if not os.path.isdir(dst):
            os.mkdir(dst)

        old_cwd = os.getcwd()
        os.chdir(os.path.join(extract_dir, os.listdir(extract_dir)[0], 'src'))

        configure_cmd = self.options.get('configure-command', './configure')
        configure_options = self.options.get('configure-options','').split()

        # Add the prefix only if we're using a configure script
        if 'configure' in configure_cmd:
            configure_options.insert(0, '--prefix=%s' % dst)
            configure_options.insert(1, '--with-erlang=%s' % erlang_path)

        self.run('%s %s' % (configure_cmd, ' '.join(configure_options)))

        self.run('make install')

        shutil.rmtree(os.path.join(dst, 'www'), ignore_errors=True)
        shutil.copytree(os.path.join(extract_dir,
                                     os.listdir(extract_dir)[0],
                                     'www'),
                        os.path.join(dst, 'www'))

        # compile and install rest_connect
        rest_connect_dir = os.path.join(extract_dir,
                                        os.listdir(extract_dir)[0],
                                        'rest_connect')
        rest_connect_dst = os.path.join(dst, 'rest_connect')

        os.chdir(rest_connect_dir)
        if subprocess.call(['build.sh']) != 0:
            raise Exception("building ejabberd-rest-connect failed")

        shutil.rmtree(os.path.join(dst, 'rest_connect'), ignore_errors=True)
        ignore_pat = shutil.ignore_patterns('.svn', '.git', 'src',
                                            'Makefile', '*.template'
                                            )
        shutil.copytree(rest_connect_dir, rest_connect_dst, ignore=ignore_pat)

        # create ejabberd var dir if not exists
        var_dir = os.path.join(self.buildout['buildout']['directory'],
                               'var', 'ejabberd')
        if not os.path.exists(var_dir):
            os.makedirs(var_dir)

        # erlang.cookie related
        cookie = os.path.join(os.path.expanduser("~"), '.erlang.cookie')
        if not os.path.isfile(cookie):
            cookie_str = ''.join([i for i in random.sample(string.ascii_letters,
                                                           20)])
            f = open(cookie, 'w')
            f.write(cookie_str)
            f.close()
        os.chmod(cookie, stat.S_IRUSR | stat.S_IWUSR)
        shutil.copy2(cookie, var_dir)

        os.chdir(old_cwd)

        self.gen_scripts()

        for path in remove_after_install:
            shutil.rmtree(path)

        # install options modules from svn
        svn_modules = self.options.get('svn_modules', '').split('\n')
        for name_url in svn_modules:
            name, url = name_url.split('=')
            self.install_svn_module(name, url)

        if self.options.get('keep-compile-dir', '').lower() in ('true', 'yes', '1', 'on'):
            # If we're keeping the compile directory around, add it to
            # the parts so that it's also removed when this recipe is
            # uninstalled.
            parts.append(self.options['compile-directory'])
        else:
            shutil.rmtree(compile_dir)
            del self.options['compile-directory']

        parts.append(self.options['location'])
        return parts

    def install(self):
        """Creates the part."""

        return self.install_ejabberd()

    def update(self):
        """Updates the part."""

        dst = os.path.join(self.buildout['buildout']['parts-directory'],
                           self.name)
        return (dst,)

import logging
import os
import imp
import zc.buildout

def call_script(script, options, buildout):
    """This method is copied from z3c.recipe.runscript.

    See http://pypi.python.org/pypi/z3c.recipe.runscript for details.
    """
    filename, callable = script.split(':')
    filename = os.path.abspath(filename)
    module = imp.load_source('script', filename)
    # Run the script with all options
    getattr(module, callable.strip())(options, buildout)


class Hooks(object):
    """zc.buildout recipe for running hooks"""

    def __init__(self, buildout, name, options):
        self.options = options
        self.buildout = buildout
        self.name = name
        self.log = logging.getLogger(self.name)

        options['location'] = os.path.join(
            buildout['buildout']['parts-directory'],
            self.name)
        options['prefix'] = options['location']

    def install(self):
        hooks = self.options.get('install-hooks', '')
        self.options['executed_on_install'] = 'true'
        for hook in hooks.strip().split():
            self.log.info('Executing install-hook=%s' % hook)
            try:
                call_script(hook, self.options, self.buildout)
            except Exception, e:
                self.log.error('Error while running install-hook="%s". Exception=%s' % (hook, e))
                raise
        return tuple()

    def update(self):
        hooks = self.options.get('update-hooks', '')
        self.options['executed_on_update'] = 'true'
        for hook in hooks.strip().split():
            self.log.info('Executing update-hook=%s' % hook)
            try:
                call_script(hook, self.options, self.buildout)
            except Exception, e:
                self.log.error('Error while running update-hook="%s". Exception=%s' % (hook, e))
                raise
        return tuple()


def uninstall(name, options):
    uninstall_hooks = options.get('uninstall-hooks', '')
    options['executed_on_uninstall'] = 'true'
    for hook in uninstall_hooks.strip().split():
        self.log.info('Executing uninstall-hook=%s' % hook)
        try:
            call_script(hook, options, {})
        except Exception, e:
            self.log.error('Error while running uninstall-hook="%s". Exception=%s' % (hook, e))
            raise
    return tuple()

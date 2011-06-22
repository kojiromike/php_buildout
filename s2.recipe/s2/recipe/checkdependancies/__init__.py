import zc.buildout
import logging
import os
import re
import distutils

PORTS_VERSION_REGEXP = re.compile(r'^.*? @([-_.a-zA-Z0-9]+)')

class CheckDependancies(object):
    """zc.buildout recipe to check for required dependancies"""

    def __init__(self, buildout, name, options):
        self.options = options
        self.buildout = buildout
        self.name = name
        self.log = logging.getLogger(self.name)

        options['location'] = os.path.join(
            buildout['buildout']['parts-directory'],
            self.name)
        options['prefix'] = options['location']
        
        platform = distutils.util.get_platform()
        if platform.find('macosx') != -1:
            if os.system('which -s port') != 0:
                raise zc.buildout.UserError('Install MacPorts first: http://www.macports.org')
            self.platform = 'macosx'
        else:
            raise zc.buildout.UserError('Only Mac OS X is currently supported!')

    def run(self, cmd):
        try:
            return os.popen(cmd).read().strip()
        except Exception, e:
            self.log.error('Error executing command: %s. Exception: %s' % (cmd, e))
            raise zc.buildout.UserError('System error')

    def find_installed_version(self, lib):
        try:
            if self.platform == 'macosx':
                s = self.run("port -q installed %s" % lib)
                match = PORTS_VERSION_REGEXP.search(s)
            else:
                raise zc.buildout.UserError('Only Mac OS X is currently supported!')
                
            if not match: return None
            return distutils.version.LooseVersion(match.group(1))
        except Exception, e:
            self.log.error('Error while running checklib="%s". Exception=%s' % (lib, e))
            raise

    def install(self):
        required_dependancies = self.options.get('required-dependancies', '')
        missing_dependancies = []
        old_dependancies     = []
        
        for dependancy in distutils.util.split_quoted(required_dependancies.strip()):
            # find minimum required version
            required_version = None
            parts = dependancy.split()
            if len(parts) == 2:
                dependancy = parts[0]
                required_version = distutils.version.LooseVersion(parts[1])
            
            # find the installed version
            self.log.info('Checking for: %s' % dependancy)
            installed_version = self.find_installed_version(dependancy)
            if not installed_version:
                missing_dependancies.append(dependancy)
                continue

            if required_version and required_version > installed_version:
                old_dependancies.append(dependancy)
                continue
                
        if len(missing_dependancies) > 0:
            ds = ' '.join(missing_dependancies)
            self.log.error('Missing dependancies!\nRun this command:\n\n  sudo port install %s\n' % ds)
            raise zc.buildout.UserError('Missing dependancies: %s' % ds)
            
        if len(old_dependancies) > 0:
            ds = ' '.join(old_dependancies)
            self.log.error('Outdated versions!\nRun this command:\n\n  sudo port upgrade %s\n' % ds)
            raise zc.buildout.UserError('Upgrade needed: %s' % ds)
            
        return tuple()
    
    def update(self):
        self.install()

import appdirs
import six

try:
    from configparser import SafeConfigParser
except ImportError:
    from ConfigParser import SafeConfigParser


class ConfigFile(object):
    def __init__(self, options):
        self.options = options

        self.config = SafeConfigParser()
        if not options.config_file:
            options.config_file = appdirs.user_data_dir('rfclint', 'IETF') + "/rfclint.cfg"
        self.config.read(options.config_file)

        if options.abnf_program:
            self.set('abnf', 'program', options.abnf_program)

    def get(self, section, field):
        return self.config.get(section, field)

    def set(self, section, field, value):
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, field, value)

    def save(self):
        with open(self.options.config_file, 'w') as f:
            self.config.write(f)

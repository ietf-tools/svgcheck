import appdirs
import six

try:
    from configparser import SafeConfigParser, NoSectionError, NoOptionError, ConfigParser
except ImportError:
    from ConfigParser import SafeConfigParser, NoSectionError, NoOptionError


class ConfigFile(object):
    def __init__(self, options):
        self.options = options

        if six.PY2:
            self.config = SafeConfigParser()
        else:
            self.config = ConfigParser()

        if options:
            if not options.config_file:
                options.config_file = appdirs.user_data_dir('rfclint', 'IETF') + "/rfclint.cfg"
            self.config.read(options.config_file)

            if options.abnf_program:
                self.set('abnf', 'program', options.abnf_program)
            if options.abnf_add:
                self.set('abnf', 'addRules', options.abnf_add)

            # Spelling options
            if options.spell_program:
                self.set('spell', 'program', options.spell_program)
            if options.spell_window:
                self.set('spell', 'window', options.spell_window)
            if options.dict_list:
                self.set('spell', 'dictionaries', options.dict_list)

    def get(self, section, field):
        try:
            return self.config.get(section, field)
        except NoSectionError:
            return None
        except NoOptionError:
            return None

    def getList(self, section, field):
        value = self.get(section, field)
        if not value:
            return value
        value = value.split(',')
        value = [v.strip() for v in value]
        return value

    def set(self, section, field, value):
        if not self.config.has_section(section):
            self.config.add_section(section)
        if type(value) is list:
            value = ",".join(value)
        self.config.set(section, field, value)

    def save(self):
        with open(self.options.config_file, 'w') as f:
            self.config.write(f)

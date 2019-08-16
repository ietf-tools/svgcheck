# ----------------------------------------------------
# Copyright The IETF Trust 2018-9, All Rights Reserved
# ----------------------------------------------------

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
            if options.spell_window is not None:
                self.setInt('spell', 'window', options.spell_window)
            if options.dict_list:
                self.set('spell', 'dictionaries', options.dict_list)
            if options.spell_suggest is not None:
                self.setBoolean('spell', 'suggest', options.spell_suggest)
            if options.spell_color:
                self.set('spell', 'color', options.spell_color)
            if options.dict_personal:
                self.set('spell', 'personal', options.dict_personal)

    def get(self, section, field):
        try:
            return self.config.get(section, field)
        except NoSectionError:
            return None
        except NoOptionError:
            return None

    def getBoolean(self, section, field, default):
        v = self.get(section, field)
        if v is None:
            return default
        return v != '0'

    def getInt(self, section, field, default):
        v = self.get(section, field)
        if v is None:
            return default
        return int(v)

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

    def setBoolean(self, section, field, value):
        self.set(section, field, '1' if value else '0')

    def setInt(self, section, field, value):
        self.set(section, field, str(value))

    def save(self):
        with open(self.options.config_file, 'w') as f:
            self.config.write(f)

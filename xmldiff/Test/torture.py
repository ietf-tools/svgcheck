#
#  Before running this program execute the command
#
#  $ rsync rsync.ietf.org::id-archive/*.xml Torture
#
#  

import os
import subprocess
import optparse
from rfctools_common.parser import XmlRfcParser
from rfctools_common.parser import XmlRfcError, CACHES
from xmldiff.EditItem import EditItem
from xmldiff.zzs2 import distance
from xmldiff.DiffNode import DiffRoot, BuildDiffTree, DecorateSourceFile, diffCount, AddParagraphs
from rfctools_common import log


def main():
    # Populate options
    formatter = optparse.IndentedHelpFormatter(max_help_position=40)
    optionparser = optparse.OptionParser(usage='rfclint SOURCE [OPTIONS] '
                                         '...\nExample: rfclint '
                                         'draft.xml',
                                         formatter=formatter)

    parser_options = optparse.OptionGroup(optionparser, "Parser Options")
    parser_options.add_option('-c', '--cache', dest='cache',
                              help='specify a primary cache directory to'
                              ' write to; default: try [ %s ]' % ', '.join(CACHES))
    parser_options.add_option('-N', '--no-network', action='store_true', default=False,
                              help='don\'t use the network to resolve references')
    parser_options.add_option('-n', '--no-rng', action='store_true',
                              help='disable RNG validation step')
    parser_options.add_option('-r', '--rng', action='store_true',
                              help='Specify an alternate RNG file')
    parser_options.add_option('-X', '--no-xinclude', action='store_true', dest='no_xinclude',
                              help='don\'t resolve any xi:include elements')

    optionparser.add_option_group(parser_options)

    general_options = optparse.OptionGroup(optionparser, "General Options")
    general_options.add_option('-o', '--out', dest='output_filename', metavar='FILE',
                               help='specify an explicit output filename')
    optionparser.add_option_group(general_options)

    plain_options = optparse.OptionGroup(optionparser, 'Plain Options')

    plain_options.add_option('-q', '--quiet', action='store_true',
                             help='dont print anything')
    plain_options.add_option('-v', '--verbose', action='store_true',
                             help='print extra information')
    plain_options.add_option('--debug', action='store_true',
                             help='Show debugging output')
    plain_options.add_option('--extract', dest='extract',
                             help='Extract all items of the given type')
    optionparser.add_option_group(plain_options)

    spell_options = optparse.OptionGroup(optionparser, 'Spell Options')
    spell_options.add_option('--no-spell', dest='no_spell', default=False, action='store_true',
                             help='Don\'t run the spell checking')
    spell_options.add_option('--dictionary', dest='dict_list', action='append',
                             help='Use this addition dictionary when spell checking')
    spell_options.add_option('--personal', dest='dict_personal',
                             help='use this dictionary as the personal dictionary')
    spell_options.add_option('--spell-window', dest='spell_window', action='store',
                             type='int',
                             help='Set the number of words to appear around spelling errors')
    spell_options.add_option('--no-dup-detection', dest='no_dups', action='store_true',
                             help='Don\'t do duplication detection.')
    spell_options.add_option('--spell-program', dest='spell_program', metavar='NAME',
                             help='Name of spelling program to use')
    spell_options.add_option('--no-suggest', dest='spell_suggest', action='store_false',
                             help='Do not provide suggestions')
    spell_options.add_option('--suggest', dest='spell_suggest', action='store_true',
                             help='provide suggestions (default)')
    optionparser.add_option_group(spell_options)

    abnf_options = optparse.OptionGroup(optionparser, 'ABNF Options')
    abnf_options.add_option('--abnf-program', dest='abnf_program', metavar='NAME',
                            help='Name of ABNF checker program to use')
    abnf_options.add_option('--no-abnf', dest='no_abnf', action='store_true',
                            help='Don\'t perform ABNF checking')
    abnf_options.add_option('--abnf-add-rules', dest='abnf_add',
                            help='ABNF file to append during evaluation.')

    config_options = optparse.OptionGroup(optionparser, 'Configuration Options')
    config_options.add_option('--configfile', dest='config_file', metavar='NAME',
                              help="Specify the name of the configuration file.")
    config_options.add_option('--save-config', dest='save_config', default=False,
                              action='store_true', help='Save configuration back to file')

    # --- Parse and validate arguments ---------------------------------

    (options, args) = optionparser.parse_args()

    files = [os.path.join('Torture', f) for f in os.listdir('Torture') if os.path.isfile(os.path.join('Torture', f))
             and f[-4:] == '.xml']

    for i in range(len(files)-1):
        DistanceTest(files[i], files[i+1], options)



def DistanceTest(leftFile, rightFile, options):
    try:
        left = XmlRfcParser(leftFile, quiet=True).parse()
        left = BuildDiffTree(left.tree, options)
        left = AddParagraphs(left)
        right = XmlRfcParser(rightFile, quiet=True).parse()
        right = BuildDiffTree(right.tree, options)
        right = AddParagraphs(right)

        editSet = distance(left, right, DiffRoot.get_children,
                           DiffRoot.InsertCost, DiffRoot.DeleteCost, DiffRoot.UpdateCost)

        c = left.applyEdits(editSet)

        if c > 0:
            log.error("Fail applying edits for '{0}' and '{1}', # edits = {2}".
                      format(leftFile, rightFile, c))
    except Exception as e:
        log.exception("Fail applying edits for '{0}' and '{1}'".
                  format(leftFile, rightFile), e)
                                                     

if __name__ == '__main__':
    main()

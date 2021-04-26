# Copyright: (c) 2012, Jan-Piet Mens <jpmens () gmail.com>
# Copyright: (c) 2012-2014, Michael DeHaan <michael@ansible.com> and others
# Copyright: (c) 2017, Ansible Project

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import datetime
import glob
import json
import os
import re
import sys
import warnings
from collections import defaultdict
from copy import deepcopy
from distutils.version import LooseVersion
from functools import partial
from pprint import PrettyPrinter

try:
    from html import escape as html_escape
except ImportError:
    # Python-3.2 or later
    import cgi


    def html_escape(text, quote=True):
        return cgi.escape(text, quote)

import jinja2
import yaml
from jinja2 import Environment, FileSystemLoader

from ansible.errors import AnsibleError
from ansible.module_utils._text import to_bytes
from ansible.module_utils.common.collections import is_sequence
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.module_utils.six import iteritems, string_types
from ansible.plugins.loader import fragment_loader
from ansible.utils import plugin_docs
from ansible.utils.display import Display

# Pylint doesn't understand Python3 namespace modules.
from ..change_detection import update_file_if_different  # pylint: disable=relative-beyond-top-level
from ..commands import Command  # pylint: disable=relative-beyond-top-level
from ..jinja2.filters import do_max, documented_type, html_ify, rst_fmt, rst_ify, \
    rst_xline, quote_backslash, html_desc, get_type  # pylint: disable=relative-beyond-top-level

#####################################################################################
# constants and paths

# if a module is added in a version of Ansible older than this, don't print the version added information
# in the module documentation because everyone is assumed to be running something newer than this already.
TOO_OLD_TO_BE_NOTABLE = 2.4

# Get parent directory of the directory this script lives in
MODULEDIR = os.path.abspath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)), os.pardir, 'lib', 'ansible', 'modules'
))

# The name of the DOCUMENTATION template
EXAMPLE_YAML = os.path.abspath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)), os.pardir, 'examples', 'DOCUMENTATION.yml'
))

DEPRECATED = b" (D)"

pp = PrettyPrinter()
display = Display()

# kludge_ns gives us a kludgey way to set variables inside of loops that need to be visible outside
# the loop.  We can get rid of this when we no longer need to build docs with less than Jinja-2.10
# http://jinja.pocoo.org/docs/2.10/templates/#assignments
# With Jinja-2.10 we can use jinja2's namespace feature, restoring the namespace template portion
# of: fa5c0282a4816c4dd48e80b983ffc1e14506a1f5
NS_MAP = {}


def to_kludge_ns(key, value):
    NS_MAP[key] = value
    return ""


def from_kludge_ns(key):
    return NS_MAP[key]


test_list = partial(is_sequence, include_strings=False)


def normalize_options(value):
    """Normalize boolean option value."""

    if value.get('type') == 'bool' and 'default' in value:
        try:
            value['default'] = boolean(value['default'], strict=True)
        except TypeError:
            pass
    return value


def write_data(text, output_dir, outputname, module=None):
    ''' dumps module output to a file or the screen, as requested '''

    if output_dir is not None:
        if module:
            outputname = outputname % module

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        fname = os.path.join(output_dir, outputname)
        fname = fname.replace(".py", "")

        try:
            updated = update_file_if_different(fname, to_bytes(text))
        except Exception as e:
            display.display("while rendering %s, an error occured: %s" % (module, e))
            raise
        if updated:
            display.display("rendering: %s" % module)
    else:
        print(text)


IS_STDOUT_TTY = sys.stdout.isatty()


def show_progress(progress):
    '''Show a little process indicator.'''
    if IS_STDOUT_TTY:
        sys.stdout.write('\r%s\r' % ("-/|\\"[progress % 4]))
        sys.stdout.flush()


def get_plugin_info(module_dir, limit_to=None, verbose=False):
    '''
    Returns information about plugins and the categories that they belong to

    :arg module_dir: file system path to the top of the plugin directory
    :kwarg limit_to: If given, this is a list of plugin names to
        generate information for.  All other plugins will be ignored.
    :returns: Tuple of two dicts containing module_info, categories, and
        aliases and a set listing deprecated modules:

        :module_info: mapping of module names to information about them.  The fields of the dict are:

            :path: filesystem path to the module
            :deprecated: boolean.  True means the module is deprecated otherwise not.
            :aliases: set of aliases to this module name
            :metadata: The modules metadata (as recorded in the module)
            :doc: The documentation structure for the module
            :seealso: The list of dictionaries with references to related subjects
            :examples: The module's examples
            :returndocs: The module's returndocs

        :categories: maps category names to a dict.  The dict contains at
            least one key, '_modules' which contains a list of module names in
            that category.  Any other keys in the dict are subcategories with
            the same structure.

    '''

    categories = dict()
    module_info = defaultdict(dict)

    # * windows powershell modules have documentation stubs in python docstring
    #   format (they are not executed) so skip the ps1 format files
    # * One glob level for every module level that we're going to traverse
    files = (
            glob.glob("%s/*.py" % module_dir) +
            glob.glob("%s/*/*.py" % module_dir) +
            glob.glob("%s/*/*/*.py" % module_dir) +
            glob.glob("%s/*/*/*/*.py" % module_dir)
    )

    module_index = 0
    for module_path in files:
        # Do not list __init__.py files
        if module_path.endswith('__init__.py'):
            continue

        display.display("Processing %s ..." % module_path)

        # Do not list blacklisted modules
        module = os.path.splitext(os.path.basename(module_path))[0]
        display.display("Base %s " % module)

        if module == 'base':
            continue

        try:
            if module in plugin_docs.BLACKLIST['MODULE']:
                continue
        except:
            dummy = 0

        try:
            if module in plugin_docs.REJECTLIST['MODULE']:
                continue
        except:
            dummy = 0


        # If requested, limit module documentation building only to passed-in
        # modules.
        if limit_to is not None and module.lower() not in limit_to:
            continue

        deprecated = False
        if module.startswith("_"):
            if os.path.islink(module_path):
                # Handle aliases
                source = os.path.splitext(os.path.basename(os.path.realpath(module_path)))[0]
                module = module.replace("_", "", 1)
                if source.startswith("_"):
                    source = source.replace("_", "", 1)
                aliases = module_info[source].get('aliases', set())
                aliases.add(module)
                aliases_deprecated = module_info[source].get('aliases_deprecated', set())
                aliases_deprecated.add(module)
                # In case we just created this via get()'s fallback
                module_info[source]['aliases'] = aliases
                module_info[source]['aliases_deprecated'] = aliases_deprecated
                continue
            else:
                # Handle deprecations
                module = module.replace("_", "", 1)
                deprecated = True

        #
        # Regular module to process
        #

        module_index += 1
        show_progress(module_index)

        # use ansible core library to parse out doc metadata YAML and plaintext examples
        try:
            doc, examples, returndocs, metadata = plugin_docs.get_docstring(
                module_path, fragment_loader, verbose=verbose, collection_name='ansible.builtin')
        except Exception as e:
            display.error("Error parsing module: %s" % e)
            continue

        if metadata and 'removed' in metadata.get('status', []):
            continue

        category = categories

        # Start at the second directory because we don't want the "vendor"
        mod_path_only = os.path.dirname(module_path[len(module_dir):])

        # Find the subcategory for each module
        relative_dir = mod_path_only.split('/')[1]
        sub_category = mod_path_only[len(relative_dir) + 2:]

        primary_category = ''
        module_categories = []
        # build up the categories that this module belongs to
        for new_cat in mod_path_only.split('/')[1:]:
            if new_cat not in category:
                category[new_cat] = dict()
                category[new_cat]['_modules'] = []
            module_categories.append(new_cat)
            category = category[new_cat]

        category['_modules'].append(module)

        # the category we will use in links (so list_of_all_plugins can point to plugins/action_plugins/*'
        if module_categories:
            primary_category = module_categories[0]

        if not doc:
            display.error("*** ERROR: DOCUMENTATION section missing for %s. ***" % module_path)
            continue

        if 'options' in doc and doc['options'] is None:
            display.error("*** ERROR: DOCUMENTATION.options must be a dictionary/hash when used. ***")
            pos = getattr(doc, "ansible_pos", None)
            if pos is not None:
                display.error("Module position: %s, %d, %d" % doc.ansible_pos)
            doc['options'] = dict()

        for key, opt in doc.get('options', {}).items():
            doc['options'][key] = normalize_options(opt)

        fqdn_start = module_path.index("ansible_collections/")
        fqdn_prefix = module_path[fqdn_start + 20:]
        fqdn_names = fqdn_prefix.split('/')
        fqdn = '.'.join(fqdn_names[0:2])

        # save all the information
        module_info[module] = {'path': module_path,
                               'source': os.path.relpath(module_path, module_dir),
                               'deprecated': deprecated,
                               'aliases': module_info[module].get('aliases', set()),
                               'aliases_deprecated': module_info[module].get('aliases_deprecated', set()),
                               'metadata': metadata,
                               'doc': doc,
                               'examples': examples,
                               'returndocs': returndocs,
                               'categories': module_categories,
                               'primary_category': primary_category,
                               'sub_category': sub_category,
                               'namespace': fqdn
                               }

    # keep module tests out of becoming module docs
    if 'test' in categories:
        del categories['test']

    return module_info, categories


def jinja2_environment(template_dir, typ, plugin_type):
    env = Environment(loader=FileSystemLoader(template_dir),
                      variable_start_string="@{",
                      variable_end_string="}@",
                      trim_blocks=True)
    env.globals['xline'] = rst_xline

    # Can be removed (and template switched to use namespace) when we no longer need to build
    # with <Jinja-2.10
    env.globals['to_kludge_ns'] = to_kludge_ns
    env.globals['from_kludge_ns'] = from_kludge_ns
    if 'max' not in env.filters:
        # Jinja < 2.10
        env.filters['max'] = do_max

    if 'tojson' not in env.filters:
        # Jinja < 2.9
        env.filters['tojson'] = json.dumps

    templates = {}
    if typ == 'json':
        env.filters['rst_ify'] = rst_ify
        env.filters['html_ify'] = html_ify
        env.filters['quote_backslash'] = quote_backslash
        env.filters['html_desc'] = html_desc
        env.filters['type'] = get_type
        # env.filters['quote_newline'] = quote_newline
        env.filters['fmt'] = rst_fmt
        env.filters['xline'] = rst_xline
        env.filters['documented_type'] = documented_type
        env.tests['list'] = test_list
        templates['plugin'] = env.get_template('plugin.json.j2')
        templates['orchide'] = env.get_template('orchide.json.j2')
        #templates['plugin_deprecation_stub'] = env.get_template('plugin_deprecation_stub.rst.j2')

        if plugin_type == 'module':
            name = 'modules'
        else:
            name = 'plugins'

        templates['category_list'] = env.get_template('%s_by_category.json.j2' % name)
        templates['category_full_list'] = env.get_template('%s_by_category_groups.json.j2' % name)
        #templates['support_list'] = env.get_template('%s_by_support.rst.j2' % name)
        # list of modules for parser
        templates['list_of_CATEGORY_modules'] = env.get_template('list_of_CATEGORY_%s.json.j2' % name)

    else:
        raise Exception("Unsupported format type: %s" % typ)

    return templates


def process_version_added(version_added):
    if not isinstance(version_added, string_types):
        return version_added
    if ':' not in version_added:
        return version_added
    # Strip tag from version_added. It suffices to do this here since
    # this is only used for ansible-base, and there the only valid tag
    # is `ansible.builtin:`.
    return version_added[version_added.index(':') + 1:]


def too_old(added):
    if not added:
        return False
    try:
        added_tokens = str(added).split(".")
        readded = added_tokens[0] + "." + added_tokens[1]
        added_float = float(readded)
    except ValueError as e:
        warnings.warn("Could not parse %s: %s" % (added, str(e)))
        return False
    return False # collections might have 1.0.0, added_float < TOO_OLD_TO_BE_NOTABLE


def process_options(module, options, full_key=None):
    option_names = []
    if full_key is None:
        full_key = []

    if options:
        for (k, v) in iteritems(options):
            # Make sure that "full key" is contained
            full_key_k = full_key + [k]
            v['full_key'] = full_key_k

            # display.v(pp.pformat(v['description']))
            # Error out if there's no description
            if 'description' not in v:
                # TODO Check description
                v['description'] = "Missing description"
                display.warning(msg="Missing required description for parameter '%s' in '%s' " % (k, module))
                # raise AnsibleError("Missing required description for parameter '%s' in '%s' " % (k, module))


            # Make sure description is a list of lines for later formatting
            if isinstance(v['description'], string_types):
                v['description'] = [v['description']]
            elif not isinstance(v['description'], (list, tuple)):
                # TODO reenable it
                display.warning(msg="Invalid type for options['%s']['description'].Must be string or list of strings.  Got %s" %
                                   (k, type(v['description'])))
                # raise AnsibleError("Invalid type for options['%s']['description']."
                #                   " Must be string or list of strings.  Got %s" %
                #                   (k, type(v['description'])))

            # Error out if required isn't a boolean (people have been putting
            # information on when something is required in here.  Those need
            # to go in the description instead).
            required_value = v.get('required', False)
            if not isinstance(required_value, bool):
                raise AnsibleError("Invalid required value '%s' for parameter '%s' in '%s' (must be truthy)" % (
                required_value, k, module))

            # Strip old version_added information for options
            if 'version_added' in v:
                v['version_added'] = process_version_added(v['version_added'])
                if too_old(v['version_added']):
                    del v['version_added']

            if 'suboptions' in v and v['suboptions']:
                if isinstance(v['suboptions'], dict):
                    process_options(module, v['suboptions'], full_key=full_key_k)
                elif isinstance(v['suboptions'][0], dict):
                    process_options(module, v['suboptions'][0], full_key=full_key_k)

            option_names.append(k)

    option_names.sort()

    return option_names


def process_returndocs(returndocs, full_key=None):
    if full_key is None:
        full_key = []

    if returndocs:
        for (k, v) in iteritems(returndocs):
            # Make sure that "full key" is contained
            full_key_k = full_key + [k]
            v['full_key'] = full_key_k

            # Strip old version_added information for options
            if 'version_added' in v:
                v['version_added'] = process_version_added(v['version_added'])
                if too_old(v['version_added']):
                    del v['version_added']

            # Process suboptions
            suboptions = v.get('contains')
            if suboptions:
                if isinstance(suboptions, dict):
                    process_returndocs(suboptions, full_key=full_key_k)
                elif is_sequence(suboptions):
                    process_returndocs(suboptions[0], full_key=full_key_k)


def process_plugins(module_map, templates, outputname, output_dir, ansible_version, plugin_type, custom=True, collection_version="", orchideOnly=False):
    for module_index, module in enumerate(module_map):

        show_progress(module_index)

        fname = module_map[module]['path']
        display.vvvvv(pp.pformat(('process_plugins info: ', module_map[module])))

        # if module is missing documentation and not explicitly hidden from docs index
        if module_map[module]['doc'] is None:
            display.error("%s MISSING DOCUMENTATION" % (fname,))
            _doc = {plugin_type: module,
                    'version_added': '2.4',
                    'filename': fname}
            module_map[module]['doc'] = _doc
            continue

        # Going to reference this heavily so make a short name to reference it by
        doc = module_map[module]['doc']
        display.vvvvv(pp.pformat(('process_plugins doc: ', doc)))

        # add some defaults for plugins that dont have most of the info
        doc['module'] = doc.get('module', module)
        doc['version_added'] = process_version_added(doc.get('version_added', 'historical'))

        doc['plugin_type'] = plugin_type

        doc['namespace'] = module_map[module]['namespace']
        doc['categorygroup'] = module_index
        doc['category'] = module_map[module]
        doc['custom'] = custom.lower() in ['true', 'yes', 'on']
        doc['collection_version'] = collection_version
        if module_map[module]['deprecated'] and 'deprecated' not in doc:
            display.warning("%s PLUGIN MISSING DEPRECATION DOCUMENTATION: %s" % (fname, 'deprecated'))

        required_fields = ('short_description',)
        for field in required_fields:
            if field not in doc:
                display.warning("%s PLUGIN MISSING field '%s'" % (fname, field))

        not_nullable_fields = ('short_description',)
        for field in not_nullable_fields:
            if field in doc and doc[field] in (None, ''):
                print(
                    "%s: WARNING: MODULE field '%s' DOCUMENTATION is null/empty value=%s" % (fname, field, doc[field]))

        if 'description' in doc:
            if isinstance(doc['description'], string_types):
                doc['description'] = [doc['description']]
            elif not isinstance(doc['description'], (list, tuple)):
                raise AnsibleError("Description must be a string or list of strings.  Got %s"
                                   % type(doc['description']))
        else:
            doc['description'] = []

        if 'version_added' not in doc:
            # Will never happen, since it has been explicitly inserted above.
            raise AnsibleError("*** ERROR: missing version_added in: %s ***\n" % module)

        #
        # The present template gets everything from doc so we spend most of this
        # function moving data into doc for the template to reference
        #

        if module_map[module]['aliases']:
            doc['aliases'] = module_map[module]['aliases']

        # don't show version added information if it's too old to be called out
        added = 0
        if doc['version_added'] == 'historical':
            del doc['version_added']
        else:
            added = doc['version_added']

        # Strip old version_added for the module
        if too_old(added):
            del doc['version_added']

        doc['option_keys'] = process_options(module, doc.get('options'))
        doc['filename'] = fname
        doc['source'] = module_map[module]['source']
        doc['docuri'] = doc['module'].replace('_', '-')
        doc['now_date'] = datetime.date.today().strftime('%Y-%m-%d')
        doc['ansible_version'] = ansible_version

        # check the 'deprecated' field in doc. We expect a dict potentially with 'why', 'version', and 'alternative' fields
        # examples = module_map[module]['examples']
        # print('\n\n%s: type of examples: %s\n' % (module, type(examples)))
        # if examples and not isinstance(examples, (str, unicode, list)):
        #    raise TypeError('module %s examples is wrong type (%s): %s' % (module, type(examples), examples))

        # use 'examples' for 'plainexamples' if 'examples' is a string
        if isinstance(module_map[module]['examples'], string_types):
            doc['plainexamples'] = module_map[module]['examples'] # plain text
        else:
            doc['plainexamples'] = ''

        doc['metadata'] = module_map[module]['metadata']

        display.vvvvv(pp.pformat(module_map[module]))
        if module_map[module]['returndocs']:
            doc['returndocs'] = module_map[module]['returndocs']
            process_returndocs(doc['returndocs'])
        else:
            doc['returndocs'] = None

        doc['author'] = doc.get('author', ['UNKNOWN'])
        if isinstance(doc['author'], string_types):
            doc['author'] = [doc['author']]

        display.v('about to template %s' % module)
        display.vvvvv(pp.pformat(doc))
        display.v('Is Orchide mode = %s' % orchideOnly)
        if orchideOnly == "true":
            try:
                text = templates['orchide'].render(doc)
            except Exception as e:
                display.warning(msg="Could not parse %s due to %s" % (module, e))
                continue

        else:
            try:
                text = templates['plugin'].render(doc)
            except Exception as e:
                display.warning(msg="Could not parse %s due to %s" % (module, e))
                continue

        if LooseVersion(jinja2.__version__) < LooseVersion('2.10'):
            # jinja2 < 2.10's indent filter indents blank lines.  Cleanup
            text = re.sub(' +\n', '\n', text)

        write_data(text, output_dir, outputname, module)

        # Create deprecation stub pages for deprecated aliases
        if module_map[module]['aliases']:
            for alias in module_map[module]['aliases']:
                if alias in module_map[module]['aliases_deprecated']:
                    doc['alias'] = alias

                    display.v('about to template %s (deprecation alias %s)' % (module, alias))
                    display.vvvvv(pp.pformat(doc))
                    try:
                        text = templates['plugin_deprecation_stub'].render(doc)
                    except Exception as e:
                        display.warning(msg="Could not parse %s (deprecation alias %s) due to %s" % (module, alias, e))
                        continue

                    if LooseVersion(jinja2.__version__) < LooseVersion('2.10'):
                        # jinja2 < 2.10's indent filter indents blank lines.  Cleanup
                        text = re.sub(' +\n', '\n', text)

                    write_data(text, output_dir, outputname, alias)


def process_categories(plugin_info, categories, templates, output_dir, output_name, plugin_type):
    # For some reason, this line is changing plugin_info:
    # text = templates['list_of_CATEGORY_modules'].render(template_data)
    # To avoid that, make a deepcopy of the data.
    # We should track that down and fix it at some point in the future.
    plugin_info = deepcopy(plugin_info)
    for category in sorted(categories.keys()):
        module_map = categories[category]
        category_filename = output_name % category

        display.display("*** recording category %s in %s ***" % (category, category_filename))

        # start a new category file

        category_name = category.replace("_", " ")
        category_title = category_name.title()

        subcategories = dict((k, v) for k, v in module_map.items() if k != '_modules')
        template_data = {'title': category_title,
                         'category_name': category_name,
                         'category': module_map,
                         'subcategories': subcategories,
                         'module_info': plugin_info,
                         'plugin_type': plugin_type
                         }

        text = templates['list_of_CATEGORY_modules'].render(template_data)
        write_data(text, output_dir, category_filename)


def get_categories_templatedata(plugin_info, categories, plugin_type):
    category_groups = []
    for category in sorted(categories.keys()):
        module_map = categories[category]
        # start a new category file

        category_name = category.replace("_", " ")
        category_title = category_name.title()

        subcategories = dict((k, v) for k, v in module_map.items() if k != '_modules')
        template_data = {'title': category_title,
                         'category_name': category_name,
                         'category': module_map,
                         'subcategories': subcategories,
                         'module_info': plugin_info,
                         'plugin_type': plugin_type
                         }
        category_groups.append(template_data)
    return category_groups

def process_support_levels(plugin_info, categories, templates, output_dir, plugin_type):
    supported_by = {'Ansible Core Team': {'slug': 'core_supported',
                                          'modules': [],
                                          'output': 'core_maintained.rst',
                                          'blurb': "These are :doc:`modules maintained by the"
                                                   " Ansible Core Team<core_maintained>` and will always ship"
                                                   " with Ansible itself."},
                    'Ansible Network Team': {'slug': 'network_supported',
                                             'modules': [],
                                             'output': 'network_maintained.rst',
                                             'blurb': "These are :doc:`modules maintained by the"
                                                      " Ansible Network Team<network_maintained>` in"
                                                      " a relationship similar to how the Ansible Core Team"
                                                      " maintains the Core modules."},
                    'Ansible Partners': {'slug': 'certified_supported',
                                         'modules': [],
                                         'output': 'partner_maintained.rst',
                                         'blurb': """
Some examples of :doc:`Certified Modules<partner_maintained>` are those submitted by other
companies. Maintainers of these types of modules must watch for any issues reported or pull requests
raised against the module.

The Ansible Core Team will review all modules becoming certified.  Core committers will review
proposed changes to existing Certified Modules once the community maintainers of the module have
approved the changes. Core committers will also ensure that any issues that arise due to Ansible
engine changes will be remediated.  Also, it is strongly recommended (but not presently required)
for these types of modules to have unit tests.

These modules are currently shipped with Ansible, but might be shipped separately in the future.
"""},
                    'Ansible Community': {'slug': 'community_supported',
                                          'modules': [],
                                          'output': 'community_maintained.rst',
                                          'blurb': """
These are :doc:`modules maintained by the Ansible Community<community_maintained>`.  They **are
not** supported by the Ansible Core Team or by companies/partners associated to the module.

They are still fully usable, but the response rate to issues is purely up to the community.  Best
effort support will be provided but is not covered under any support contracts.

These modules are currently shipped with Ansible, but will most likely be shipped separately in the future.
                                          """},
                    }

    # only gen support pages for modules for now, need to split and namespace templates and generated docs
    if plugin_type == 'plugins':
        return
    # Separate the modules by support_level
    for module, info in plugin_info.items():
        if not info.get('metadata', None):
            display.warning('no metadata for %s' % module)
            continue
        if info['metadata']['supported_by'] == 'core':
            supported_by['Ansible Core Team']['modules'].append(module)
        elif info['metadata']['supported_by'] == 'network':
            supported_by['Ansible Network Team']['modules'].append(module)
        elif info['metadata']['supported_by'] == 'certified':
            supported_by['Ansible Partners']['modules'].append(module)
        elif info['metadata']['supported_by'] == 'community':
            supported_by['Ansible Community']['modules'].append(module)
        else:
            raise AnsibleError('Unknown supported_by value: %s' % info['metadata']['supported_by'])

    # Render the module lists based on category and subcategory
    for maintainers, data in supported_by.items():
        subcategories = {}
        subcategories[''] = {}
        for module in data['modules']:
            new_cat = plugin_info[module]['sub_category']
            category = plugin_info[module]['primary_category']
            if category not in subcategories:
                subcategories[category] = {}
                subcategories[category][''] = {}
                subcategories[category]['']['_modules'] = []
            if new_cat not in subcategories[category]:
                subcategories[category][new_cat] = {}
                subcategories[category][new_cat]['_modules'] = []
            subcategories[category][new_cat]['_modules'].append(module)

        template_data = {'maintainers': maintainers,
                         'subcategories': subcategories,
                         'modules': data['modules'],
                         'slug': data['slug'],
                         'module_info': plugin_info,
                         'plugin_type': plugin_type
                         }
        text = templates['support_list'].render(template_data)
        write_data(text, output_dir, data['output'])


def validate_options(options):
    ''' validate option parser options '''

    if not options.module_dir:
        sys.exit("--module-dir is required")
    if not os.path.exists(options.module_dir):
        sys.exit("--module-dir does not exist: %s" % options.module_dir)
    if not options.template_dir:
        sys.exit("--template-dir must be specified")


class DocumentPlugins(Command):
    name = 'document-plugins'

    @classmethod
    def init_parser(cls, add_parser):
        parser = add_parser(cls.name, description='Generate module documentation from metadata')

        parser.add_argument("-A", "--ansible-version", action="store", dest="ansible_version",
                            default="unknown", help="Ansible version number")
        parser.add_argument("-M", "--module-dir", action="store", dest="module_dir",
                            default=MODULEDIR, help="Ansible library path")
        parser.add_argument("-P", "--plugin-type", action="store", dest="plugin_type",
                            default='module', help="The type of plugin (module, lookup, etc)")
        parser.add_argument("-T", "--template-dir", action="append", dest="template_dir",
                            help="directory containing Jinja2 templates")
        parser.add_argument("-t", "--type", action='store', dest='type', choices=['rst', 'json'],
                            default='json', help="Document type")
        parser.add_argument("-o", "--output-dir", action="store", dest="output_dir", default=None,
                            help="Output directory for module files")
        parser.add_argument("-I", "--includes-file", action="store", dest="includes_file",
                            default=None, help="Create a file containing list of processed modules")
        parser.add_argument("-l", "--limit-to-modules", '--limit-to', action="store",
                            dest="limit_to", default=None, help="Limit building module documentation"
                                                                " to comma-separated list of plugins. Specify non-existing plugin name"
                                                                " for no plugins.")
        parser.add_argument('-V', action='version', help='Show version number and exit')
        parser.add_argument('-v', '--verbose', dest='verbosity', default=0, action="count",
                            help="verbose mode (increase number of 'v's for more)")

        parser.add_argument("-c", "--custom-definitions", action='store', dest='custom', default=True, help="Create custom module definitions for OrchidE")
        parser.add_argument("-r", "--collection-version", action='store', dest='collection_version', default="", help="Collection version")

        parser.add_argument('-m', action='store', dest="orchide", default="false", help='Limit building to raw data')

    @staticmethod
    def main(args):
        if not args.template_dir:
            args.template_dir = ["hacking/templates"]
        validate_options(args)
        display.verbosity = args.verbosity
        plugin_type = args.plugin_type

        display.display("Evaluating %s files..." % plugin_type)

        # prep templating
        templates = jinja2_environment(args.template_dir, args.type, plugin_type)

        # set file/directory structure
        if plugin_type == 'module':
            # trim trailing s off of plugin_type for plugin_type=='modules'. ie 'copy_module.rst'
            outputname = '%s' + '.%s' % args.type
            output_dir = args.output_dir
        else:
            # for plugins, just use 'ssh.rst' vs 'ssh_module.rst'
            outputname = '%s.%s' % args.type
            output_dir = '%s/plugins/%s' % (args.output_dir, plugin_type)

        display.vv('output name: %s' % outputname)
        display.vv('output dir: %s' % output_dir)

        # Convert passed-in limit_to to None or list of modules.
        if args.limit_to is not None:
            args.limit_to = [s.lower() for s in args.limit_to.split(",")]

        plugin_info, categories = get_plugin_info(args.module_dir, limit_to=args.limit_to, verbose=(args.verbosity > 0))

        categories['all'] = {'_modules': plugin_info.keys()}
        if display.verbosity >= 3:
            display.vvv(pp.pformat(categories))
        if display.verbosity >= 5:
            display.vvvvv(pp.pformat(plugin_info))

        # Transform the data
        if args.type == 'rst':
            display.v('Generating rst')
            for key, record in plugin_info.items():
                display.vv(key)
                if display.verbosity >= 5:
                    display.vvvvv(pp.pformat(('record', record)))
                if record.get('doc', None):
                    short_desc = record['doc']['short_description'].rstrip('.')
                    if short_desc is None:
                        display.warning('short_description for %s is None' % key)
                        short_desc = ''
                    record['doc']['short_description'] = rst_ify(short_desc)
        if args.type == 'json':
            display.v('Generating json')
            for key, record in plugin_info.items():
                display.vv(key)
                if display.verbosity >= 5:
                    display.vvvvv(pp.pformat(('record', record)))
                if record.get('doc', None):
                    short_desc = record['doc']['short_description'].rstrip('.')
                    if short_desc is None:
                        display.warning('short_description for %s is None' % key)
                        short_desc = ''
                    record['doc']['short_description'] = short_desc

            category_group = get_categories_templatedata(plugin_info, categories, plugin_type)
            category_list_text = templates['category_full_list'].render(category_groups=category_group)
            category_index_name = '_%ss_by_categorygroup.json' % plugin_type
            write_data(category_list_text, output_dir, category_index_name)

        if plugin_type == 'module':
            display.v('Generating Categories')
            # Write module master category list
            #category_list_text = templates['category_list'].render(categories=sorted(categories.keys()))
            #category_index_name = '_%ss_by_category.rst' % plugin_type
            #write_data(category_list_text, output_dir, category_index_name)



        # Render all the categories for modules
        if plugin_type == 'module':
            display.v('Generating Category lists - disabled')
            #category_list_name_template = 'list_of_%s_' + '%ss.rst' % plugin_type
            # TODO Check if required
            category_list_name_template = '_list_of_%s_' + '%ss.json' % plugin_type
            display.display('Generating list of all modules per collection.')
            process_categories(plugin_info, categories, templates, output_dir, category_list_name_template, plugin_type)

            # Render all the categories for modules
            # process_support_levels(plugin_info, categories, templates, output_dir, plugin_type)

        # Render all the individual plugin pages
        display.v('Generating module/plugin pages')
        process_plugins(plugin_info, templates, outputname, output_dir, args.ansible_version, plugin_type, args.custom, args.collection_version, args.orchide)


        return 0

# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

import re
import collections

try:
    from html import escape as html_escape
except ImportError:
    # Python-3.2 or later
    import cgi


    def html_escape(text, quote=True):
        return cgi.escape(text, quote)

from jinja2.runtime import Undefined

from ansible.errors import AnsibleError
from ansible.module_utils._text import to_text
from ansible.module_utils.six import string_types

_ITALIC = re.compile(r"I\(([^)]+)\)")
_BOLD = re.compile(r"B\(([^)]+)\)")
_MODULE = re.compile(r"M\(([^)]+)\)")
_URL = re.compile(r"U\(([^)]+)\)")
_LINK = re.compile(r"L\(([^)]+), *([^)]+)\)")
_CONST = re.compile(r"C\(([^)]+)\)")
_RULER = re.compile(r"HORIZONTALLINE")

_QUOTE_CR = re.compile(r"\r")
_QUOTE_BS = re.compile(r"\\")
_QUOTE_TAB = re.compile(r"\t")
_QUOTE_NL = re.compile(r"\n")


def html_ify(text):
    ''' convert symbols like I(this is in italics) to valid HTML '''

    if not isinstance(text, string_types):
        text = to_text(text)

    t = html_escape(text)
    t = _ITALIC.sub(r"<em>\1</em>", t)
    t = _BOLD.sub(r"<b>\1</b>", t)
    t = _MODULE.sub(r"<pre>\1</pre>", t)
    t = _URL.sub(r"<a href='\1'>\1</a>", t)
    t = _LINK.sub(r"<a href='\2'>\1</a>", t)
    t = _CONST.sub(r"<code>\1</code>", t)
    t = _RULER.sub(r"<hr/>", t)

    return t.strip()


def quote_backslash(text):
    '''Quotes backslashes for use in data strings in JSON'''

    t = _QUOTE_BS.sub(r"\\\\", text)
    t = _QUOTE_CR.sub(r"\\r", t)
    t = _QUOTE_TAB.sub(r"\\t", t)
    t = _QUOTE_NL.sub(r"\\n", t)

    return t.strip()


def documented_type(text):
    ''' Convert any python type to a type for documentation '''

    if isinstance(text, Undefined):
        return '-'
    if text == 'str':
        return 'string'
    if text == 'bool':
        return 'boolean'
    if text == 'int':
        return 'integer'
    if text == 'dict':
        return 'dictionary'
    return text


# The max filter was added in Jinja2-2.10.  Until we can require that version, use this
def do_max(seq):
    return max(seq)


def rst_ify(text):
    ''' convert symbols like I(this is in italics) to valid restructured text '''

    try:
        t = _ITALIC.sub(r"*\1*", text)
        t = _BOLD.sub(r"**\1**", t)
        t = _MODULE.sub(r":ref:`\1 <\1_module>`", t)
        t = _LINK.sub(r"`\1 <\2>`_", t)
        t = _URL.sub(r"\1", t)
        t = _CONST.sub(r"``\1``", t)
        t = _RULER.sub(r"------------", t)
    except Exception as e:
        raise AnsibleError("Could not process (%s) : %s" % (text, e))

    return t


def rst_fmt(text, fmt):
    ''' helper for Jinja2 to do format strings '''

    return fmt % (text)


def rst_xline(width, char="="):
    ''' return a restructured text line of a given length '''

    return char * width


def html_desc(description_lines):
    if description_lines is None:
        return ""

    if isinstance(description_lines, bool):
        return to_text(description_lines)

    if isinstance(description_lines, int):
        return to_text(description_lines)

    if isinstance(description_lines, float):
        return to_text(description_lines)

    if isinstance(description_lines, string_types):
        return html_ify(quote_backslash(description_lines))

    if isinstance(description_lines, collections.abc.Iterable):
        t = ""
        for line in description_lines:
            ht = html_ify(quote_backslash(line))
            t = t + "<p>" + ht + "</p>"
        return t

    return to_text(description_lines)


def get_type(instance):
    return type(instance)

# coding: utf-8
# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class DependencyError(Exception):
    """A dependency was unmet"""


class MissingUserInput(Exception):
    """The user failed to provide input (via cli arg or interactively"""


class InvalidUserInput(Exception):
    """The user provided invalid input"""

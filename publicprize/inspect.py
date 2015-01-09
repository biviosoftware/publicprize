# -*- coding: utf-8 -*-
""" Enhanced functions based on :py:mod:`inspect`

    :copyright: (c) 2014 Bivio Software, Inc.
    :license: Apache, see LICENSE for more details.
"""

import inspect
import sys

def class_has_classmethod(cls, method):
    """Does cls or its ancestors implement method?"""
    for name in inspect.getmro(cls):
        if hasattr(name, method) and inspect.ismethod(getattr(name, method)):
            return True
    return False

def package_name_tail(name):
    """Last component in a package's name ( __name__), e.g. x.y.module yields 'y'"""
    m = sys.modules[name]
    if m.__package__ is None:
        return ''
    p = m.__package__.split('.')
    if m.__name__ == m.__package__:
        p.pop()
    if len(p) > 0:
        return p.pop()
    return ''

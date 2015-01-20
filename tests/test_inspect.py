# -*- coding: utf-8 -*-
""" pytest for :mod:publicprize.inspect

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import pytest
import inspect

from publicprize import inspect as ppi

class Class1(object):
    var1 = 3
    @classmethod
    def class_method1():
        pass

    def method1():
        pass

    # There is no difference between method1 and lambda1. You can't test an unbound
    # method (that is a method defined but bound to an instance)
    lambda1 = lambda self: None

def test_class_has_classmethod():
    assert ppi.class_has_classmethod(Class1, 'class_method1')
    assert not ppi.class_has_classmethod(Class1, 'method1')
    assert not ppi.class_has_classmethod(Class1, 'lambda1')
    assert not ppi.class_has_classmethod(Class1, 'var1')
    assert not ppi.class_has_classmethod(Class1, 'not_a_method')

def test_package_name_tail():
    import publicprize
    import publicprize.inspect
    assert ppi.package_name_tail('publicprize.inspect') == 'publicprize'
    assert ppi.package_name_tail('publicprize') == ''
    assert ppi.package_name_tail('__main__') == ''

# -*- coding: utf-8 -*-
""" pytest for :mod:publicprize.biv

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import pytest
from publicprize import biv
# Needed to initialize known biv.ids
import publicprize.general.task
import publicprize.general.model
import werkzeug.exceptions

def test_marker():
    assert biv.Marker(1) == 1
    assert biv.Marker(899) == 899
    for v in -1, 0, 900:
        with pytest.raises(AssertionError):
            biv.Marker(v)

def test_index():
    assert biv.Index(9) == 9
    assert biv.Index(1e15 - 1) == 1e15 - 1
    for v in 0, int(1e15):
        with pytest.raises(werkzeug.exceptions.NotFound):
            biv.Index(v)

def test_id():
    assert biv.Id(1001) == 1001
    i = biv.Id(13001)
    assert i.biv_marker == 1
    assert i.biv_index == 13
    assert i.to_biv_uri() == '_D01'
    for v in (1000, 1):
        with pytest.raises(AssertionError):
            biv.Id(v)

def test_uri():
    assert biv.URI('index') == 'index'
    assert biv.URI('index').biv_id == 4001
    assert biv.URI('_401') == '_401'
    assert biv.URI('_401').biv_id == 4001

def test_load_obj():
    assert biv.load_obj('_101').format_uri() == '/pub'
    assert biv.load_obj('').format_uri() == '/index'
    assert biv.load_obj('_101').format_uri('logout') == '/pub/logout'


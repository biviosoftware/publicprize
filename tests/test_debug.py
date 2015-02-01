# -*- coding: utf-8 -*-
""" pytest for :mod:publicprize.debug

    :copyright: Copyright (c) 2015 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import glob
import inspect
import os.path
import pytest
import re
import shutil

from publicprize import debug as ppd
from publicprize import config
from publicprize.debug import pp_t

_request_logger = None

_expect = {
    'environ': 'some environ',
    'status': 'some status',
    'response_headers': 'some headers',
    'response_data': 'some write',
    'other': 'hello'
}

def _init_debug(test_mode, regex):
    ppd._request_logger = None
    ppd._trace_printer = None
    ppd._app = None
    mock = MockApp()
    mock.config = {
        'PUBLICPRIZE': {
            'TRACE': regex,
            'TEST_MODE': test_mode}}
    ppd.init(mock)
    return mock

class MockApp(object):
    
    def __init__(self):
        self.wsgi_app = self
        self.called__call__ = 0
        
    def __call__(self, environ, start_response):
        global _expect
        global _request_logger
        self.called__call__ += 1
        start_response(_expect['status'], _expect['response_headers'])
        return _expect['response_data']

def test_nothing():
    global _request_logger
    mock = _init_debug(0, None)
    assert mock.wsgi_app == mock
    
def test_log():
    global _expect
    global _request_logger
    if os.path.exists('debug'):
        shutil.rmtree('debug')
    os.mkdir('debug')
    called_start_response = 0
    mock = _init_debug(1, None)
    _request_logger = ppd.get_request_logger()
    def start_response(status, response_headers, exc_info=None):
        nonlocal called_start_response
        called_start_response += 1
    
    def assert_file(index, suffix):
        name = os.path.join('debug', index + '-' + suffix)
        assert os.path.exists(name), name
        with open(name, 'r') as f:
            actual = f.read()
            assert actual == _expect[suffix], suffix + '=' + actual

    response = mock.wsgi_app(_expect['environ'], start_response)
    assert '00000003-response_headers' in _request_logger.last_file_name()
    _request_logger.set_log_dir('new_dir')
    for ignore in response:
        pass
    assert '00000001-response_data' in _request_logger.last_file_name() 
    response.close()
    _request_logger.log('hello', 'other')

    assert mock.called__call__ == 1
    assert called_start_response == 1
    assert_file('00000001', 'environ')
    assert_file('00000002', 'status')
    assert_file('00000003', 'response_headers')
    assert_file('new_dir/00000001', 'response_data')
    assert_file('new_dir/00000002', 'other')
    _request_logger.log('not written', 'invalid/suffix')
    assert list(glob.glob('debug/*invalid*')) == [], 'found invalid/suffix'

def test_trace():
    _last_msg = None
    def _init(regex):
        nonlocal _last_msg
        _last_msg = None
        _init_debug(0, regex)
        ppd._trace_printer.write = _write

    def _write(msg):
        nonlocal _last_msg
        _last_msg = msg

    def expect(msg):
        return './tests/test_debug.py:{}:test_trace {}\n'.format(inspect.currentframe().f_back.f_lineno - 1, msg)

    _init(None)
    pp_t('hello')
    assert None == _last_msg

    _init('.')
    pp_t('hello')
    assert expect('hello') == _last_msg 
    pp_t('x{}x', ['y'])
    assert expect('xyx') == _last_msg 

    _init('goodbye')
    pp_t('hello')
    assert None == _last_msg 
    pp_t('goodbye')
    assert expect('goodbye') == _last_msg 
    

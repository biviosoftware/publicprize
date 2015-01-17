# -*- coding: utf-8 -*-
""" pytest for :mod:publicprize.debug

    :copyright: Copyright (c) 2015 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import os.path
import pytest
import shutil

from publicprize import debug as ppd

_expect = {
    'environ': 'some environ',
    'status': 'some status',
    'response_headers': 'some headers',
    'response_data': 'some write'
}

class MockApp(object):
    
    def __init__(self, test_mode):
        self.config = {'PUBLICPRIZE': {'TEST_MODE': test_mode}}
        self.wsgi_app = self
        self.called__call__ = 0
        
    def __call__(self, environ, start_response):
        global _expect
        self.called__call__ += 1
        start_response(_expect['status'], _expect['response_headers'])
        return _expect['response_data']

def test_nothing():
    mock = MockApp(0)
    ppd.RequestLogger(mock)
    assert mock.wsgi_app == mock
    
def test_log():
    global _expect
    if os.path.exists('debug'):
        shutil.rmtree('debug')
    os.mkdir('debug')
    called_start_response = 0
    mock = MockApp(1)
    ppd.RequestLogger(mock)
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
    for ignore in response:
        pass
    response.close()

    assert mock.called__call__ == 1
    assert called_start_response == 1
    assert_file('00000001', 'environ')
    assert_file('00000002', 'status')
    assert_file('00000003', 'response_headers')
    assert_file('00000004', 'response_data')

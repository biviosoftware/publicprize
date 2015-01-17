# -*- coding: utf-8 -*-
""" Debugging support

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import os
import os.path
import shutil
import sys

class RequestLogger(object):
    """Log all requests and responses if in test mode"""
    
    def __init__(self, _app):
        """If in test mode, create the log dir and then set _app.wsgi_app to self"""
        if not _app.config['PUBLICPRIZE']['TEST_MODE']:
            return
        d = os.path.abspath('debug')
        try:
            try:
                shutil.rmtree(d, ignore_errors=True)
            except:
                pass
            os.makedirs(d)
        except:
            sys.stderr.write(d + ': cannot create log directory\n')
            return
        self._wsgi_app = _app.wsgi_app
        self._index = 0
        self._file = os.path.join(d, '{:08d}-{}')
        _app.wsgi_app = self

    def __call__(self, environ, start_response):
        """Catch request and pass it on"""
        self._log(str(environ), 'environ')

        def _start_response(status, response_headers, exc_info=None):
            """Return _write"""
            self._log(str(status), 'status')
            self._log(str(response_headers), 'response_headers')
            if exc_info is not None:
                self._log(str(exc_info), 'exc_info')
            start_response(status, response_headers, exc_info)

        return _Response(
            self,
            self._wsgi_app(environ, _start_response))

    def _open(self, suffix):
        self._index += 1;
        return open(self._file.format(self._index, suffix), 'w')

    def _log(self, data, suffix):
        """Write data to a log file, ignoring any errors"""
        try:
            with self._open(suffix) as f:
                f.write(data)
        except:
            sys.stderr.write("unable log " + suffix + ":" + logger._index)

class _Response(object):
    def __init__(self, logger, response):
        self.response = response
        self.handle = None
        self.logger = logger

    def close(self):
        if self.handle:
            self.handle.close()
        if hasattr(self.response, "close"):
            self.response.close()

    def __iter__(self):
        self.response_iter = self.response.__iter__()
        try:
            self.handle = self.logger._open('response_data')
        except:
            sys.stderr.write("unable to open response_data:" + logger._index)
        return self

    def __next__(self):
        data = self.response_iter.__next__()
        if data:
            try:
                if self.handle:
                    self.handle.write(str(data))
            except:
                sys.stderr.write("unable to write response_data:" + logger._index)
        return data

# -*- coding: utf-8 -*-
""" Debugging support

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import os
import os.path
import shutil

_BASE_DIR = 'debug'
_BASE_NAME = '{:08d}-{}'

class RequestLogger(object):
    """Log all requests and responses to files (in test mode only)"""
    
    def __init__(self, _app):
        """If in test mode, create the log dir and then set _app.wsgi_app to self"""
        if not _app.config['PUBLICPRIZE']['TEST_MODE']:
            return
        self._app = _app
        self._wsgi_app = _app.wsgi_app
        self._root_dir = os.getcwd()
        self._root_dir = self.set_log_dir(_BASE_DIR)
        if self._root_dir:
            # Only register if was able to create directory
            _app.wsgi_app = self

    def __call__(self, environ, start_response):
        """Catch request and pass it on"""
        self.log(str(environ), 'environ')

        def _start_response(status, response_headers, exc_info=None):
            """Return _write"""
            self.log(str(status), 'status')
            self.log(str(response_headers), 'response_headers')
            if exc_info is not None:
                self.log(str(exc_info), 'exc_info')
            start_response(status, response_headers, exc_info)

        return _Response(
            self,
            self._wsgi_app(environ, _start_response))

    def last_file_name(self):
        """Last file name written by logger"""
        return self._last_file_name

    def log(self, data, suffix):
        """Write data to a log file, ignoring any errors"""
        try:
            with self._open(suffix) as f:
                f.write(data)
        except:
            self._app.logger.warn("unable log " + suffix + ":" + logger._index)

    def set_log_dir(self, relpath):
        """Set the log diretory to relpath (relative to root_dir), resets the index"""
        d = self._mkdir(relpath)
        if d:
            self._curr_dir = d
            self._index = 0
        return d
        
        
    def _mkdir(self, relpath):
        rp = os.path.normpath(relpath)
        assert not rp.startswith('.')
        d = os.path.join(self._root_dir, rp)
        try:
            try:
                shutil.rmtree(d, ignore_errors=True)
            except:
                pass
            os.makedirs(d)
        except:
            self._app.logger.warn(d + ': cannot create log directory')
            return None
        return d

    def _open(self, suffix):
        self._index += 1;
        fn = os.path.join(
            self._curr_dir,
            _BASE_NAME.format(self._index, suffix))
        self._last_file_name = fn
        return open(self._last_file_name, 'w')

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
            self._app.logger.warn("unable to open response_data:" + logger._index)
        return self

    def __next__(self):
        data = self.response_iter.__next__()
        if data:
            try:
                if self.handle:
                    self.handle.write(data)
            except:
                self._app.logger.warn("unable to write response_data:" + logger._index)
        return data

# -*- coding: utf-8 -*-
""" Debugging support

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import inspect
import os
import os.path
import re
import sys
import shutil

_BASE_DIR = 'debug'
_BASE_NAME = '{:08d}-{}'

_request_logger = None
_trace_printer = None
_cwd = os.getcwd()
_app = None

def get_request_logger():
    """Current request logger"""
    return _request_logger

def init(app):
    global _app
    _app = app
    RequestLogger()
    TracePrinter()

def pp_t(fmt_or_msg, fmt_params=None):
    """Print a message to trace log based on caller context and current
    value of config.PUBLICPRIZE.TRACE ($PUBLICPRIZE_TRACE) regular expression.
    """
    _trace_printer._debug_write(fmt_or_msg, fmt_params)

class RequestLogger(object):
    """Log all requests and responses to files (in test mode only)"""


    def __init__(self):
        """If in test mode, create the log dir and then set _app.wsgi_app to self"""
        global _request_logger
        assert _request_logger == None, 'RequestLogger already initialized'
        _request_logger = self
        if not _app.config['PUBLICPRIZE']['TEST_MODE']:
            self._root_dir = None
            return
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
        except Exception:
            sys.stderr.write('unable log ' + suffix + ':' + str(self._index) + '\n')

    def set_log_dir(self, relpath):
        """Set the log diretory to relpath (relative to root_dir), resets the index"""
        if not self._root_dir:
            return None
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
            except Exception:
                pass
            os.makedirs(d)
        except IOError as e:
            pp_d('{}: makedirs failed: {}', [d, e])
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
        self._response = response
        self._handle = None
        self._logger = logger

    def close(self):
        if self._handle:
            self._handle.close()
        if hasattr(self._response, 'close'):
            self._response.close()

    def __iter__(self):
        self._response_iter = self._response.__iter__()
        try:
            self._handle = self._logger._open('response_data')
        except IOError as e:
            pp_d('{}: open failed: {}', [self._logger.last_file_name(), e])
        return self

    def __next__(self):
        data = self._response_iter.__next__()
        if data:
            try:
                if self._handle:
                    self._handle.write(str(data))
            except IOError as e:
                pp_d('{}: write failed: {}', self._logger.last_file_name(), e)
        return data


class TracePrinter(object):
    """Prints message to sys.stderr. TODO: Use Logger interface"""

    def __init__(self):
        global _trace_printer
        assert _trace_printer == None, 'TracePrinter already initialized'
        _trace_printer = self
        self._regex = None
        try:
            regex = _app.config['PUBLICPRIZE']['TRACE']
            self._regex = re.compile(regex, flags=re.IGNORECASE)

        except Exception:
            pass

    def _debug_write(self, fmt_or_msg, fmt_params):
        """Use pp_t() instead"""
        frame = None
        try:
            if not self._regex:
                return
            frame = inspect.currentframe()
            if not frame:
                #TODO: Could this test be static? only dependent on interpreter?
                return

            frame = frame.f_back.f_back
            filename = frame.f_code.co_filename.replace(_cwd, '.')
            line = frame.f_lineno
            name = frame.f_code.co_name
            prefix = '{}:{}:{} '.format(filename, line, name)

        except Exception:
            return
        finally:
            # Avoid cycles in the stack (according to manual)
            del frame

        try:
            msg = fmt_or_msg.format(*fmt_params) if fmt_params else str(fmt_or_msg)
            if self._regex.search(msg):
                _trace_printer.write(prefix + msg + '\n')
        except Exception:
            _trace_printer.write('format error: ' + prefix + fmt_or_msg + str(fmt_params))

    def write(self, msg):
        """Write a trace message. TODO: subject to change"""
        sys.stderr.write(msg)

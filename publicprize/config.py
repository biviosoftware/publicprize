# -*- coding: utf-8 -*-
""" Flask configuration.

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""
import os

def _config_from_environ(cfg, prefix):
    for k in cfg.keys():
        ek = prefix + '_' + k.upper()
        if isinstance(cfg[k], dict):
            _config_from_environ(cfg[k], ek)
        elif ek in os.environ:
            t = type(cfg[k])
            v = os.environ[ek]
            if issubclass(t, (int, bool)):
                v = t(v)
            cfg[k] = v


def _read_json(filename):
    """Read filename for json"""
    with open(filename) as f:
        import json
        return json.load(f)


class Config(object):
    """Configuration driven off environment variables"""
    import locale
    locale.setlocale(locale.LC_ALL, '')
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    PUBLICPRIZE = _read_json(os.environ.get('PUBLICPRIZE_JSON', 'config.json'))
    _config_from_environ(PUBLICPRIZE, 'PUBLICPRIZE')
    for k in ['DEBUG', 'ALL_PUBLIC_CONTESTANTS', 'TEST_USER', 'MAIL_DEBUG', 'MAIL_SUPPRESS_SEND']:
        if PUBLICPRIZE.get(k, None) is None:
            PUBLICPRIZE[k] = PUBLICPRIZE['TEST_MODE']
    MAIL_SUPPRESS_SEND = PUBLICPRIZE['MAIL_SUPPRESS_SEND']
    import paypalrestsdk
    paypalrestsdk.configure(PUBLICPRIZE['PAYPAL'])
    SECRET_KEY = PUBLICPRIZE['SECRET_KEY']
    DEBUG = PUBLICPRIZE['TEST_MODE']
    # Avoid message: "adds significant overhead..."
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = \
        'postgresql://{user}:{password}@/{name}'.format(**PUBLICPRIZE['DATABASE'])
    if PUBLICPRIZE.get('SQLALCHEMY_ECHO') is not None:
        SQLALCHEMY_ECHO = PUBLICPRIZE['SQLALCHEMY_ECHO']
    if PUBLICPRIZE.get('WTF_CSRF_TIME_LIMIT') is not None:
        WTF_CSRF_TIME_LIMIT = PUBLICPRIZE['WTF_CSRF_TIME_LIMIT']
    if PUBLICPRIZE.get('WTF_CSRF_ENABLED') is not None:
        WTF_CSRF_ENABLED = PUBLICPRIZE['WTF_CSRF_ENABLED']
    MAIL_DEFAULT_SENDER = PUBLICPRIZE['SUPPORT_EMAIL']
    MAIL_DEBUG = PUBLICPRIZE['MAIL_DEBUG']

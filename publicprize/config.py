# -*- coding: utf-8 -*-
""" Flask configuration.

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

def _read_json(filename):
    """Read filename for json"""
    with open(filename) as f:
        import json
        return json.load(f)

class Config(object):
    """Configuration driven off environment variables"""

    import os
    import locale
    locale.setlocale(locale.LC_ALL, '')
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    PUBLICPRIZE = _read_json(os.environ.get('PUBLICPRIZE_JSON', 'config.json'))
    for x in ('DEBUG', 'ALL_PUBLIC_CONTESTANTS', 'TEST_USER', 'MAIL_DEBUG'):
        if not x in PUBLICPRIZE:
            PUBLICPRIZE[x] = PUBLICPRIZE['TEST_MODE']

    import paypalrestsdk
    paypalrestsdk.configure(PUBLICPRIZE['PAYPAL'])

    SECRET_KEY = PUBLICPRIZE['SECRET_KEY']
    DEBUG = PUBLICPRIZE['TEST_MODE']
    SQLALCHEMY_DATABASE_URI = \
        'postgresql://{user}:{password}@{host}/{name}'.format(**PUBLICPRIZE['DATABASE'])
    if 'SQLALCHEMY_ECHO' in PUBLICPRIZE:
        SQLALCHEMY_ECHO = PUBLICPRIZE['SQLALCHEMY_ECHO']
    MAIL_DEFAULT_SENDER = PUBLICPRIZE['SUPPORT_EMAIL']
    MAIL_DEBUG = PUBLICPRIZE['MAIL_DEBUG']
    if 'WTF_CSRF_TIME_LIMIT' in PUBLICPRIZE:
        WTF_CSRF_TIME_LIMIT = PUBLICPRIZE['WTF_CSRF_TIME_LIMIT']
    if 'WTF_CSRF_ENABLED' in PUBLICPRIZE:
        WTF_CSRF_ENABLED = PUBLICPRIZE['WTF_CSRF_ENABLED']

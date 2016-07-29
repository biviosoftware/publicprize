# -*- coding: utf-8 -*-
u"""Date routines

:copyright: Copyright (c) 2016 Bivio Software, Inc.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function


def now_before_start(start):
    """Is current time before start

    Args:
        start (db.DateTime): beginning
    Returns:
        bool: True if before start
    """
    return start.utcnow() < start


def now_in_range(start, end):
    """Is current time between start and end date

    Args:
        start (db.DateTime): beginning
        end (db.DateTime): end of period
    Returns:
        bool: True if within these days
    """
    return start <= start.utcnow() <= end

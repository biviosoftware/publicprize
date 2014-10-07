# -*- coding: utf-8 -*-
""" Common model classes.

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import publicprize.controller as controller
import sqlalchemy


class ModelWithDates(controller.Model):
    """Model superclass with create/update datetime fields.

    Fields:
        creation_date_time: date the record was inserted
        modified_date_time: date the record was last updated
    """

    creation_date_time = controller.db.Column(
        controller.db.DateTime,
        nullable=False,
        server_default=sqlalchemy.text('current_timestamp')
    )
    modified_date_time = controller.db.Column(
        controller.db.DateTime,
        onupdate=sqlalchemy.text('current_timestamp')
    )

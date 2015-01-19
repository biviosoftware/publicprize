# -*- coding: utf-8 -*-
""" Common model classes.

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import publicprize.controller as ppc
import sqlalchemy
import flask

class ModelWithDates(ppc.Model):
    """Model superclass with create/update datetime fields.

    Fields:
        creation_date_time: date the record was inserted
        modified_date_time: date the record was last updated
    """

    creation_date_time = ppc.db.Column(
        ppc.db.DateTime,
        nullable=False,
        server_default=sqlalchemy.text('current_timestamp')
    )
    modified_date_time = ppc.db.Column(
        ppc.db.DateTime,
        onupdate=sqlalchemy.text('current_timestamp')
    )

class Template(object):
    """Render html templates based on the template_dir.
    """

    def __init__(self, template_dir):
        self.template_dir = template_dir

    def base_template(self, name):
        """Get base defaults to contest"""
        return ppc.app().jinja_env.get_template(
            self.template_dir + '/' + name + '.html')

    def render_template(self, biv_obj, name, **kwargs):
        """Render the page, putting the selected menu and contest in env"""
        if 'selected' not in kwargs:
            kwargs['selected'] = name
        print('template name: ', self._template_name(name))
        return flask.render_template(
            self._template_name(name),
            contest=biv_obj,
            base_template=self.base_template('contest'),
            **kwargs
        )

    def _template_name(self, name):
        """Render template name based on local package"""
        return '{pkg}/{base}.html'.format(base=name, pkg=self.template_dir)


# -*- coding: utf-8 -*-
""" Acceptance testing.

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import os.path
import re
import unittest

from bs4 import BeautifulSoup

import publicprize.controller as ppc
import publicprize.debug
from publicprize.debug import pp_t
import workflow_data as wd
from contest_common import ParseData, FlaskTestClientProxy, DbCheck, TestCaseHelpers

CONTEST_NAME = 'Next Up'


class PublicPrizeTestCase(unittest.TestCase, TestCaseHelpers):
    def setUp(self):
        ppc.init()
        app = ppc.app()
        app.wsgi_app = FlaskTestClientProxy(app.wsgi_app)
        self.client = app.test_client()
        self.current_page = None


    def tearDown(self):
        pass

    def setup_method(self, method):
        pp_t('here')
        publicprize.debug.get_request_logger().set_log_dir(
            os.path.join('test_workflow', method.__name__)
        )

    def test_admin(self):
        self._visit_uri('/')
        self._visit_uri('/pub/new-test-admin')
        self._follow_link('{}'.format(CONTEST_NAME))
        self._verify_text('Admin')
        self._follow_link('Admin')
        self._verify_text('Review Nominees')

    def test_review_nominees_security(self):
        self._visit_uri('/pub/logout')
        self._visit_uri('/_10D/admin-review-nominees')
        self._verify_text('Please log in')
        self._visit_uri('/pub/new-test-user')

    def test_not_found(self):
        self._visit_uri('/x')
        self._verify_text('Page Not Found')
        self._visit_uri('/_102/x')
        self._verify_text('Page Not Found')
        self._visit_uri('/_10299/')
        self._verify_text('Page Not Found')

    def test_submit_website_conf_entries(self):
        self._visit_uri('/')
        self._follow_link(CONTEST_NAME)
        conf_websites_gen = ParseData(wd.WEBSITE_SUBMISSION_FIELDS).get_data_variations('conf')
        #TODO(mda): the current_uri tracking doesn't notice redirects
        nominate_website_uri = self.current_uri
        submitted_websites_uri = self.current_uri + '/nominees'
        for data_variation in conf_websites_gen:
            url_and_name = data_variation['websites'].split('-')
            self._visit_uri(nominate_website_uri)
            self._submit_form({
                'url': url_and_name[0],
                'company_name': url_and_name[1],
                'submitter_name':'x'
            })
            self._verify_text('Thanks for Nominating')
            self._visit_uri(submitted_websites_uri)
            self._verify_text(url_and_name[1], "website '{}' not at {}".format(
                url_and_name[1], self.current_uri))
            #TODO(mda): get current time
            #TODO(mda): check the database directly

    def test_submit_website_dev_entries(self):
        self._visit_uri('/')
        self._follow_link('Next Up')
        dev_websites_gen = ParseData(wd.WEBSITE_SUBMISSION_FIELDS).get_data_variations('dev')
        for data_variation in dev_websites_gen:
            self._submit_form({
                'url': data_variation['websites'],
                'company_name':'x',
                'submitter_name':'x'
            })
            self._verify_text('Website invalid or unavailable')
            #TODO(mda): be certain that the website is not in the database

if __name__ == '__main__':
    unittest.main()

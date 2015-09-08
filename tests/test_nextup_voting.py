# -*- coding: utf-8 -*-
""" Acceptance testing.

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import unittest

import publicprize.controller as ppc
from contest_common import FlaskTestClientProxy, TestCaseHelpers

CONTEST_NAME = 'Next Up'


class PublicPrizeTestCase(unittest.TestCase, TestCaseHelpers):
    def setUp(self):
        ppc.init()
        app = ppc.app()
        app.wsgi_app = FlaskTestClientProxy(app.wsgi_app)
        self.client = app.test_client()
        self.current_page = None

    def test_logged_out_vote(self):
        self._visit_uri('/')
        self._follow_link(CONTEST_NAME)
        self._verify_text('Log in')
        # votes = self._parse_votes()
        # self._visit_uri(votes['Test Pint 1 Nominee'][1])
        # self._verify_text('Please log in')

    def test_logged_in_vote(self):
        self._visit_uri('/pub/new-test-user')
        self._follow_link(CONTEST_NAME)
        # votes = self._parse_votes()
        # self._visit_uri(votes['Test Pint 2 Nominee'][1])
        # votes2 = self._parse_votes()
        # assert votes['Test Pint 2 Nominee'][0] == \
        #     votes2['Test Pint 2 Nominee'][0] - 1
        # self._verify_text('Thanks for voting')
        # self._visit_uri(votes2['Test Pint 1 Nominee'][1])
        # votes3 = self._parse_votes()
        # assert votes['Test Pint 1 Nominee'][0] == \
        #     votes2['Test Pint 1 Nominee'][0]
        # self._verify_text('Change Vote')
        # self._visit_uri(self._find_ok_link()['href'])
        # votes4 = self._parse_votes()
        # self._verify_text('Thanks for voting')
        # assert votes['Test Pint 1 Nominee'][0] == \
        #     votes4['Test Pint 1 Nominee'][0] - 1
        # assert votes['Test Pint 2 Nominee'][0] == \
        #     votes4['Test Pint 2 Nominee'][0]
        # self._follow_link('Pitchers')
        # self._verify_text('Test Pitcher 1 Nominee')

    def _find_ok_link(self):
        """Returns the link which has OK for text"""
        for link in self.current_page.find_all('a'):
            if link.get_text() == 'OK':
                return link
        assert False

    def _parse_votes(self):
        """Returns a dictionary of name => (vote count, href)"""
        self._verify_text('Vote For a Pint and a Pitcher')
        res = {}
        for link in self.current_page.find_all('a'):
            if link.get('class') and 'pp-vote-button' in link['class']:
                link_pair = link.parent.find_all('a')
                res[link_pair[1].get_text()] = [
                    int(link_pair[0].get_text()),
                    link_pair[0]['href']
                    ]
        return res



if __name__ == '__main__':
    unittest.main()

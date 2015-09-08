# -*- coding: utf-8 -*-
""" Acceptance testing.

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import unittest
import json

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

    def test_judging(self):
        judge_score = self._find_judge_score('Test Pint 17 Nominee')
        print('judge_score = {}'.format(judge_score))
        self._visit_uri('/')
        self._follow_link(CONTEST_NAME)
        base_url = self.current_uri
        self._visit_uri(base_url + '/new-test-judge')
        self._follow_link(CONTEST_NAME)
        # self._follow_link('Judging')
        # self._verify_text('rank the top 10')
        # nominees = self._parse_nominees_from_buttons()
        # print(nominees)
        # self.client.post(
        #     '{}/judge-ranking'.format(base_url),
        #     data={
        #         'ranks': json.dumps(['pint', nominees['Test Pint 17 Nominee']])
        #     })
        # judge_score2 = self._find_judge_score('Test Pint 17 Nominee')
        # if int(judge_score2) != int(judge_score) + 10:
        #     raise AssertionError('unexpected score: {}'.format(judge_score2))

    def _find_judge_score(self, text):
        self._visit_uri('/pub/new-test-admin')
        self._follow_link(CONTEST_NAME)
        self._follow_link('Review Scores')
        score = None
        for td in self.current_page.find_all('td'):
            if td.get_text() != text:
                continue
            score = td.find_next_sibling('td').find_next_sibling('td') \
                .get_text()
        if score:
            return float(score)
        raise AssertionError('no score found for: {}'.format(text))

    def _parse_nominees_from_buttons(self):
        res = {}
        for button in self.current_page.find_all('button'):
            nominee_id = button.get('data-nominee')
            if not nominee_id:
                continue
            name = button.find_next_sibling('a')
            res[name.text] = nominee_id
        return res


if __name__ == '__main__':
    unittest.main()

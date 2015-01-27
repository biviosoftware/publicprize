# -*- coding: utf-8 -*-
""" Acceptance testing.

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import decimal
import os.path
import random
import re
import unittest

from bs4 import BeautifulSoup

import publicprize.controller as ppc
import publicprize.debug
from publicprize.debug import pp_t
import workflow_data as wd
from contest_common import ParseData, FlaskTestClientProxy, DbCheck


class PublicPrizeTestCase(unittest.TestCase):
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

    def test_contribution(self):
        self._visit_uri('/')
        self._follow_link('Esprit Venture Challenge')
        self._follow_link('Contestants')
        self._follow_link('gazeMetrix')
        self._submit_form({
        })
        self._verify_text('Please enter an amount.')
        self._submit_form({
            'amount': 1,
        })
        self._verify_text('Amount must be at least $10')
        self._submit_form({
            'amount': 10000001,
        })
        self._verify_text('Amount too large')

    def test_index(self):
        self._visit_uri('/')
        self._verify_text('Empty Contest')
        self._follow_link('Empty Contest')

    def test_not_found(self):
        self._visit_uri('/x')
        self._verify_text('Page Not Found')
        self._visit_uri('/_102/x')
        self._verify_text('Page Not Found')
        self._visit_uri('/_10299/')
        self._verify_text('Page Not Found')

    def test_conf_submit_entries(self):
        conf_entry_gen = ParseData(wd.SUBMIT_ENTRY_FIELDS).get_data_variations('conf')
        for data_variation in conf_entry_gen:
            num = int(random.random() * 10000)
            base_name = data_variation['display_name']
            display_name = '{0}{1}'.format(base_name, num)

            self._visit_uri('/')
            self._visit_uri('/pub/new-test-user')
            self._verify_text('Log out')
            self._follow_link('Esprit Venture Challenge')
#            self._follow_link('How to Enter')
            self._visit_uri(self.current_uri + '/submit-contestant')
            self._submit_form({
                'display_name': display_name,
                'contestant_desc': data_variation['contestant_desc'],
                'youtube_url': data_variation['youtube_url'],
                'slideshow_url': data_variation['slideshow_url'],
                'website': data_variation['website'],
                'founder_desc': data_variation['founder_desc'],
                'tax_id': data_variation['tax_id'],
                'business_phone': data_variation['business_phone'],
                'business_address': data_variation['business_address'],
                'founder2_name': data_variation['founder2_name'],
                'agree_to_terms': data_variation['agree_to_terms']
            })
            self._verify_text('Thank you for submitting your entry')
            self._verify_text(display_name)
            self._follow_link(display_name)
            dont_verify = [
                'youtube_url',
                'slideshow_url',
                'website',
                'tax_id',
                'business_phone',
                'business_address',
                'agree_to_terms']
            for data_item in data_variation:
                if not data_item in dont_verify:
                    pp_t(
                        'verifying string for {0} contents:\n{1}\n...', [
                            data_item,
                            data_variation[data_item]])
                    self._verify_text(
                        data_variation[data_item],
                        'item={} variation={}: data_item not found'.format(
                            data_item,
                            data_variation[data_item]))
                    pp_t('verified')

    def test_dev_submit_entries(self):
        """ Try a bunch of submissions with mostly good data, and a single
            bad piece of data. No submissions should be accepted by the
            How To Enter page. This test assumes that test_good_submit_entries
            passed, otherwise it's possible that a submission won't be
            accepted because of the supposedly conforming data that it contains
        """
        main_subtype = 'conf'
        dev_entry_gen = ParseData(wd.SUBMIT_ENTRY_FIELDS).get_mostly_one_type_single_other_type_variations(main_subtype)
        for data_variation, deving_field in dev_entry_gen:
            self._visit_uri('/')
            self._visit_uri('/pub/new-test-user')
            self._verify_text('Log out')
            self._follow_link('Esprit Venture Challenge')
#            self._follow_link('How to Enter')
            self._visit_uri(self.current_uri + '/submit-contestant')

            if deving_field != 'display_name': # we're not testing display_name
                num = int(random.random() * 10000)
                base_name = data_variation['display_name']
                display_name = '{0}{1}'.format(base_name, num)
            else:  # we are testing display_name
                display_name = data_variation['display_name']

            self._submit_form({
                'display_name': display_name,
                'contestant_desc': data_variation['contestant_desc'],
                'youtube_url': data_variation['youtube_url'],
                'slideshow_url': data_variation['slideshow_url'],
                'website': data_variation['website'],
                'founder_desc': data_variation['founder_desc'],
                'tax_id': data_variation['tax_id'],
                'business_phone': data_variation['business_phone'],
                'business_address': data_variation['business_address'],
                'founder2_name': data_variation['founder2_name'],
                'agree_to_terms': data_variation['agree_to_terms']
            })
            # It should not work, so we should still be on the
            # 'Submit Your Entry' page
            self._verify_text('Submit Your Entry', ('Error: expected submission to fail\n'
                                                    'deviating field: {}\n'
                                                    "field_contents: '{}'\n"
                                                    "".format(deving_field,
                                                              data_variation[deving_field])))

    def test_judging_math(self):
        dataParser = ParseData(wd.JUDGING_FIELDS)
        self._visit_uri('/')
        self._follow_link('Esprit Venture Challenge')
        self._visit_uri(self.current_uri + '/new-test-judge')
        self._follow_link('Esprit Venture Challenge')
        self._follow_link('Judging')

        # Try 15 random judging variations
        for _ in range(15):
            conf_data = dataParser.get_random_variation('conf')
            self._follow_link('gazeMetrix')

            expected_points = decimal.Decimal('0.00')
            multipliers = {
                1: decimal.Decimal(0),
                2: decimal.Decimal(1) / decimal.Decimal(3),
                3: decimal.Decimal(2) / decimal.Decimal(3),
                4: decimal.Decimal(1)
            }
            for i in range(1, 7):  # [1, 6]
                key = 'question{}'.format(i)
                base_points = wd.JUDGING_POINTS[key]
                multiplier = multipliers[conf_data[key]]
                expected_points += base_points * multiplier

            self._submit_form({
                'question1': conf_data['question1'],
                'question2': conf_data['question2'],
                'question3': conf_data['question3'],
                'question4': conf_data['question4'],
                'question5': conf_data['question5'],
                'question6': conf_data['question6'],
            })

            # round to 2 decimal places
            rounded_expected_points = expected_points.quantize(decimal.Decimal('0.01'))
            expected_points_text = str(rounded_expected_points)

            errorstring = ("\nquestion1: {}\n"
                           "question2: {}\n"
                           "question3: {}\n"
                           "question4: {}\n"
                           "question5: {}\n"
                           "question6: {}\n"
                           "Expected result:{}".format(conf_data['question1'],
                                                       conf_data['question2'],
                                                       conf_data['question3'],
                                                       conf_data['question4'],
                                                       conf_data['question5'],
                                                       conf_data['question6'],
                                                       expected_points_text)
                           )

            self._verify_text(expected_points_text, errorstring)

    def test_judging_security(self):
        # Test that public users cannot visit the judging page
        self._visit_uri('/')
        self._visit_uri('/pub/new-test-user')
        self._verify_text('Log out')
        self._follow_link('Esprit Venture Challenge')
        self._visit_uri(self.current_uri + '/judging')
        self._verify_text('Forbidden', 'public users should not be able to visit the judging page')
        # Test that judges from another contest cannot visit the judging page
        self._visit_uri('/')
        self._follow_link('Empty Contest')
        self._visit_uri(self.current_uri + '/new-test-judge')
        self._follow_link('Esprit Venture Challenge')
        self._visit_uri(self.current_uri + '/judging')
        self._verify_text('Forbidden', 'judges from another contest should not be able to visit the judging page')

    def test_judging_and_admin(self):
        self._visit_uri('/')
        self._follow_link('Esprit Venture Challenge')
        self._visit_uri(self.current_uri + '/new-test-judge')
        self._follow_link('Esprit Venture Challenge')
        self._follow_link('Judging')
        self._follow_link('gazeMetrix')
        self._submit_form({
            'question1_comment': 'comments for question 1',
            'question2': 3,
            'general_comment': 'my general comments'
        })
        self._follow_link('Partial Score')
        self._verify_text('comments for question 1')
        self._submit_form({
            'question1': 4,
            'question2': 4,
            'question3': 4,
            'question4': 4,
            'question5': 4,
            'question5_comment': 'comments for question 5',
            'question6': 4,
            'general_comment': 'new comments'
        })
        self._verify_text('60.00')
        self._follow_link('gazeMetrix')
        self._verify_text('new comments')
        self._visit_uri('/pub/new-test-admin')
        self._follow_link('Esprit Venture Challenge')
        self._follow_link('Admin')
        self._follow_link('gazeMetrix')
        self._verify_text('15.00 / 15')

    def test_submit_entry(self):
        self._visit_uri('/')
        self._visit_uri('/pub/new-test-user')
        self._verify_text('Log out')
        self._follow_link('Esprit Venture Challenge')
#        self._follow_link('How to Enter')
        self._visit_uri(self.current_uri + '/submit-contestant')
        num = int(random.random() * 10000)
        name = 'Test Entry {}, WÜN'.format(num)
        self._submit_form({
            'display_name': name,
            'contestant_desc': 'Description for entry {}'.format(num),
            'youtube_url': 'https://www.youtube.com/watch?v=K5pZlBgXBu0',
            'slideshow_url': 'http://www.slideshare.net/Experian_US/how-to-juggle-debt-retirement',
            'website': 'www.google.com',
            'founder_desc': 'Founder bio for entry {}'.format(num),
            'tax_id': '22-7777777',
            'business_phone': '303-123-4567',
            'business_address': '123 Pearl St\nBoulder CO 80303',
            'founder2_name': 'Founder Two',
            'founder2_desc': 'Founder Two bio entry',
            'agree_to_terms': True
        })
        self._verify_text('Thank you for submitting your entry')
        self._verify_text(name)
        self._follow_link('My Entry')
        self._verify_text(name)

    def _follow_link(self, link_text):
        url = None
        # exact match
        for link in self.current_page.find_all('a'):
            if link.get_text() == link_text:
                url = link['href']
                break
        # partial match
        if not url:
            regexp = re.compile(re.escape(link_text))
            for link in self.current_page.find_all('a'):
                if re.search(regexp, link.get_text()):
                    url = link['href']
                    break

        assert url
        self._visit_uri(url)

    def _set_current_page(self, response):
        self.current_response = response
        self.current_page = BeautifulSoup(response.data)

    def _submit_form(self, data):
        pp_t(self.current_page)
        url = self.current_page.find('form')['action']
        assert url
        # data['csrf_token'] = self.current_page.find(id='csrf_token')['value']
        # assert data['csrf_token']
        self._set_current_page(self.client.post(
            url,
            data=data,
            follow_redirects=True))
        self.current_uri = url

    def _verify_text(self, text, msg=""):
        if not self.current_page.find(text=re.compile(re.escape(text))):
            if not msg:
                msg = text + ': text not found in '
            pp_t(msg)
            pp_t(str(self.current_page))
            raise AssertionError(msg)

    def _visit_uri(self, uri):
        assert uri
        self._set_current_page(self.client.get(uri, follow_redirects=True))
        self.current_uri = uri

if __name__ == '__main__':
    unittest.main()

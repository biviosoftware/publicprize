# -*- coding: utf-8 -*-
""" Acceptance testing.

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

from bs4 import BeautifulSoup
import random
import re
import unittest
import publicprize.controller
import itertools
import test_data

class ParseData(object):
    """ Takes in a data set of the form:
        SET = {
            'item': {
                'conf': []
                'dev': []
            }, ...
        }

       Then returns various dev and conf options
    """
    def __init__(self, data):
        """ good_data and bad_data should be lists of lists of data, containing
        at least one item each """
        assert len(data) > 0
        for key, item in data.items():
            item = data[key]
            assert item.__contains__('conf'), 'item: {0}'.format(item)
            assert len(item['conf']) > 0
            assert item.__contains__('dev'), 'item: {0}'.format(item)
            assert len(item['dev']) > 0
        self.data = data

    def get_data_variations(self, data_subtype):
        """ Efficiently returns sets of the form:
            SET = {
                'item': some_value,
                'item2': some_value,
                ...
            },

            such that all members of in either the 'conf' or 'dev' subset of
            'item', 'item2', ..., are eventually returned.

            -- data_subtype: subtype for data, either 'conf' or 'dev'
        """
        positions = {}
        data = {}

        # initialization
        for key, item in self.data.items():
            positions[key] = 0
            data[key] = item[data_subtype][positions[key]]
        yield data

        # main loop
        done = False
        while done is False:
            done = True
            for key, item in self.data.items():
                if len(item[data_subtype]) > positions[key] + 1:
                    positions[key] += 1
                    data[key] = item[data_subtype][positions[key]]
                    done = False
            yield data


class PublicPrizeTestCase(unittest.TestCase):
    def setUp(self):
        publicprize.controller.init()
        self.client = publicprize.controller.app().test_client()
        self.current_page = None

    def tearDown(self):
        pass

    def test_contribution(self):
        self._visit_uri('/')
        self._follow_link('Esprit Venture Challenge 2014')
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
        self._visit_uri('/_102/x');
        self._verify_text('Page Not Found')
        self._visit_uri('/_10299/');
        self._verify_text('Page Not Found')

    def test_good_submit_entries(self):
        data_gen = ParseData(test_data.FIELDS).get_data_variations('conf')
        for data_variation in data_gen:
            num = int(random.random() * 10000)
            base_name = data_variation['display_name']
            display_name = '{0}{1}'.format(base_name, num)

            self._visit_uri('/')
            self._visit_uri('/pub/new-test-user')
            self._verify_text('Log out')
            self._follow_link('Esprit Venture Challenge 2014')
            self._follow_link('How to Enter')
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
                'founder2_desc': data_variation['founder2_desc'],
                'agree_to_terms': data_variation['agree_to_terms']
            })
            self._verify_text('Thank you for submitting your entry')
            self._verify_text(display_name)
            self._follow_link(display_name)
            dont_verify = {'youtube_url',
                           'slideshow_url',
                           'website',
                           'tax_id',
                           'business_phone',
                           'business_address',
                           'agree_to_terms'}
            for data_item in data_variation:
                if dont_verify.__contains__(data_item):
                    pass
                else:
                    print("verifying string for {0} contents:\n"
                          "{1}\n...".format(data_item,
                                            data_variation[data_item]))
                    self._verify_text(data_variation[data_item])
                    print("verified")

    def test_submit_entry(self):
        self._visit_uri('/')
        self._visit_uri('/pub/new-test-user')
        self._verify_text('Log out')
        self._follow_link('Esprit Venture Challenge 2014')
        self._follow_link('How to Enter')
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
        self.current_page = BeautifulSoup(response.data)

    def _submit_form(self, data):
        url = self.current_page.find('form')['action']
        assert url
        # data['csrf_token'] = self.current_page.find(id='csrf_token')['value']
        # assert data['csrf_token']
        self._set_current_page(self.client.post(
            url,
            data=data,
            follow_redirects=True))

    def _verify_text(self, text):
        assert self.current_page.find(text=re.compile(re.escape(text)))

    def _visit_uri(self, uri):
        assert uri
        self._set_current_page(self.client.get(uri, follow_redirects=True))

if __name__ == '__main__':
    unittest.main()

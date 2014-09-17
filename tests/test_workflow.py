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


class PublicPrizeTestCase(unittest.TestCase):
    def setUp(self):
        publicprize.controller.init()
        self.client = publicprize.controller.app().test_client()
        self.current_page = None

    def tearDown(self):
        pass

    def test_index(self):
        self._visit_uri('/')
        self._verify_text('Empty Contest')
        self._follow_link('Empty Contest')

    def test_submit_entry(self):
        self._visit_uri('/')
        self._visit_uri('/pub/new-test-user')
        self._verify_text('Log out')
        self._follow_link('Esprit Venture Prize 2014')
        self._follow_link('How to Enter')
        num = int(random.random() * 10000)
        name = 'Test Entry {}'.format(num)
        self._submit_form({
            'display_name': name,
            'contestant_desc': 'Description for entry {}'.format(num),
            'youtube_url': 'https://www.youtube.com/watch?v=K5pZlBgXBu0',
            'slideshow_url': 'http://www.slideshare.net/Experian_US/how-to-juggle-debt-retirement',
            'website': 'www.google.com',
            'founder_desc': 'Founder bio for entry {}'.format(num)
        })
        self._verify_text('Thank you for submitting your entry')
        self._verify_text(name)
        self._follow_link('My Entry')
        self._verify_text(name)

    def _follow_link(self, link_text):
        url = None
        for link in self.current_page.find_all('a'):
            if link.get_text() == link_text:
                url = link['href']
                break
        assert url
        self._visit_uri(url)

    def _set_current_page(self, response):
        self.current_page = BeautifulSoup(str(response.data))

    def _submit_form(self, data):
        url = self.current_page.find('form')['action']
        assert url
        data['csrf_token'] = self.current_page.find(id='csrf_token')['value']
        assert data['csrf_token']
        self._set_current_page(self.client.post(
            url,
            data=data,
            follow_redirects=True))

    def _verify_text(self, text):
        assert self.current_page.find(text=re.compile(text))

    def _visit_uri(self, uri):
        assert uri
        self._set_current_page(self.client.get(uri, follow_redirects=True))

if __name__ == '__main__':
    unittest.main()

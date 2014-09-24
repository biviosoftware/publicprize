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
    """ Get a list of lists of good and bad data, and return various
    combinations of these lists """
    def __init__(self, good_data, bad_data):
        """ good_data and bad_data should be lists of lists of data, containing
        at least one item each """
        assert len(good_data) > 0
        assert len(good_data) == len(bad_data)
        for data_list in good_data:
            assert len(data_list) > 0
        for data_list in bad_data:
            assert len(data_list) > 0
        self.good_data = good_data
        self.bad_data = bad_data

    def get_basic_good_entry(self):
        return [data[0] for data in self.good_data]

    def get_basic_bad_entry(self):
        return [data[0] for data in self.bad_data]

    def gen_all_possible_good_entries(self):
        for possible_combination in itertools.product(*self.good_data):
            yield possible_combination  # note: this yields a tuple, not a list

    def gen_all_possible_bad_entries(self):
        for possible_combination in itertools.product(*self.bad_data):
            yield possible_combination  # note: this yields a tuple, not a list

    def _efficient_gen_possible_entries(self, entries_list):
        """ generating every possible combination of data is probably overkill
        in most cases. This just makes sure that every possible entry is
        entered at some point (but not every single different combination of
        entries is)
        """
        # initialization stuff
        num_items = len(entries_list)
        positions = []  # store position in each list
        for i in range(num_items):
            positions.append(0) # position in each list starts at 0

        # now generate different possibilities
        done = False
        while done is False:
            # we're done when no additional possible entries are left
            # this is assumed, and the assumption is only revoke if one is
            # found
            done = True
            ret = []
            for i in range(num_items):
                ret.append(entries_list[i][positions[i]])
                # if that sub_list has more data in it
                if positions[i] < len(entries_list[i])-1:
                    positions[i] += 1
                    done = False
            yield ret

    def efficiently_gen_possible_good_entries(self):
        for good_entry in self._efficient_gen_possible_entries(self.good_data):
            yield good_entry

    def efficiently_gen_possible_bad_entries(self):
        for bad_entry in self._efficient_gen_possible_entries(self.bad_data):
            yield bad_entry

    def _gen_single_one_type_all_else_other_type_variations(self, primary_data, secondary_data):
        """ spit out lists that are almost all from primary_data, with a single
        entry from secondary_data. One list per each possible different sub-entry
        in secondary_data
        primary_data = list of lists of primary data
        secondary_data = list of lists of secondary data"""
        assert len(primary_data) == len(secondary_data)
        variation = [data[0] for data in primary_data]
        for i in range(len(primary_data)):
            for j in range(len(secondary_data[i])):
                variation[i] = secondary_data[i][j]
                yield variation
            variation[i] = primary_data[i][0]  # reset back to primary default

    def gen_mostly_good_with_single_bad_variations(self):
        for mostly_good_entry in self._gen_single_one_type_all_else_other_type_variations(self.good_data, self.bad_data):
            yield mostly_good_entry

    def gen_mostly_bad_with_single_good_variations(self):
        for mostly_bad_entry in self._gen_single_one_type_all_else_other_type_variations(self.bad_data, self.good_data):
            yield mostly_bad_entry


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
        self._verify_text('Amount must be at least \$10')
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
        self.good_data = test_data.SubmitEntryData().get_good_data()
        self.bad_data = test_data.SubmitEntryData().get_bad_data()
        for good_entry_variation in ParseData(self.good_data, self.bad_data).efficiently_gen_possible_good_entries():
            num = int(random.random() * 10000)
            display_name = '{0}{1}'.format(good_entry_variation[0], num)
            print(display_name)
            self._visit_uri('/')
            self._visit_uri('/pub/new-test-user')
            self._verify_text('Log out')
            self._follow_link('Esprit Venture Challenge 2014')
            self._follow_link('How to Enter')
            self._submit_form({
                'display_name': display_name,
                'contestant_desc': good_entry_variation[1],
                'youtube_url': good_entry_variation[2],
                'slideshow_url': good_entry_variation[3],
                'website': good_entry_variation[4],
                'founder_desc': good_entry_variation[5],
                'tax_id': good_entry_variation[6],
                'business_phone': good_entry_variation[7],
                'business_address': good_entry_variation[8],
                'founder2_name': good_entry_variation[9],
                'founder2_desc': good_entry_variation[10],
                'agree_to_terms': good_entry_variation[11]  # True
            })
            self._verify_text('Thank you for submitting your entry')
            self._verify_text(display_name)
            self._follow_link(display_name)
            dont_verify = {2, 3, 4, 6, 7, 8, 11}
            for i, string in enumerate(good_entry_variation):
                if dont_verify.__contains__(i):
                    pass
                else:
                    print("verifying string #{0} contents:\n {1}\n...".format(i, string))
                    self._verify_text(string)
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
        # regexp match
        if not url:
            regexp = re.compile(link_text)
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
        assert self.current_page.find(text=re.compile(text))

    def _visit_uri(self, uri):
        assert uri
        self._set_current_page(self.client.get(uri, follow_redirects=True))

if __name__ == '__main__':
    unittest.main()

# -*- coding: utf-8 -*-
""" Acceptance testing.

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""
import random

import publicprize.controller as ppc

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
        for _, item in data.items():
            assert 'conf' in item, 'item: {0}'.format(item)
            if item['conf'] is not None:
                assert len(item['conf']) > 0
            assert 'dev' in item, 'item: {0}'.format(item)
            if item['dev'] is not None:
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
            'item', 'item2', ..., are eventually returned. Does not guarantee
            that every possible permutation is considered, but does guarantee
            that each unique item in each 'conf' or 'dev' subset is considered.

            -- data_subtype: subtype for data, either 'conf' or 'dev'
        """
        positions = {}
        data = {}

        # initialization
        for key, item in self.data.items():
            if item[data_subtype] is None:
                continue  # ignore null fields
            positions[key] = 0
            data[key] = item[data_subtype][positions[key]]
        yield data

        # main loop
        done = False
        while not done:
            done = True
            for key, item in self.data.items():
                if item[data_subtype] is None:
                    continue  # ignore null fields
                if len(item[data_subtype]) > positions[key] + 1:
                    positions[key] += 1
                    data[key] = item[data_subtype][positions[key]]
                    done = False
            yield data

    # TODO: this name is way too long
    def get_mostly_one_type_single_other_type_variations(self, main_subtype):
        """ Get sets that are almost entirely one subtype, with a single
            element from the other subtype. Only one set of items from the main
            subtype is returned, while all items in the secondary subtype
            are eventually returned in separate sets.

            -- main_subtype: 'conf' or 'dev'. Whichever one you want your data
               to be mostly comprised of.
        """
        assert main_subtype == 'conf' or main_subtype == 'dev'
        secondary_subtype = 'dev' if main_subtype == 'conf' else 'conf'
        ret_data = next(self.get_data_variations(main_subtype))
        full_data = self.data

        for field in ret_data:
            if full_data[field][secondary_subtype] is None:
                continue  # skip empty fields
            for item in full_data[field][secondary_subtype]:
                ret_data[field] = item
                yield ret_data, field
            ret_data[field] = full_data[field][main_subtype]

    def get_random_variation(self, data_subtype):
        """ Gets a single random variation of self.data['data_subtype']
            fields with None values are skipped
        """
        assert data_subtype == 'conf' or data_subtype == 'dev'
        data = {}
        for key, item in self.data.items():
            if item is None:
                continue  # ignore empty fields
            data[key] = random.sample(item[data_subtype], 1)[0]  # random.sample returns a list
        return data


class FlaskTestClientProxy(object):
    """proxy class to set browser environment variables for testing.

    Courtesy of stackoverflow answer at:
    http://stackoverflow.com/questions/15278285/setting-mocking-request-headers-for-flask-app-unit-test
    """
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        environ['REMOTE_ADDR'] = environ.get('REMOTE_ADDR', '127.0.0.1')
        environ['HTTP_USER_AGENT'] = environ.get('HTTP_USER_AGENT', 'Chrome')
        return self.app(environ, start_response)


class DbCheck(object):
    ''' Helper to construct questions for the database '''
    # refactor warning: db_item used in eval's.
    def exists(self, db_item, **filters):
        filters_str = self._construct_filters_str(**filters)
        query_object = self._filter(db_item, filters_str)
        item_is_present = ppc.db.session.query(query_object.exists()).scalar()
        return item_is_present

    def count(self, db_item, **filters):
        filters_str = self._construct_filters_str(**filters)
        query_object = self._filter(db_item, filters_str)
        return query_object.count()

    def _construct_filters_str(self, **filters):
        filters_str = ''
        for test, val in filters.items():
            if type(val) == str:  # keep strings, strings
                val = "'{}'".format(val)
            filters_str += 'db_item.{} == {}, '.format(test, val)
        return filters_str

    def _filter(self, db_item, filters_str):
        return eval('db_item.query.filter({})'.format(filters_str))

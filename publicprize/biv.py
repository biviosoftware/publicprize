# -*- coding: utf-8 -*-
""" biv operations: converting to/from uri's.  Loading objects, etc.

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import numconv
import publicprize.inspect as ppi
import werkzeug.exceptions

URI_FOR_GENERAL_TASKS = 'pub'
URI_FOR_NONE = 'index'
URI_FOR_ERROR = 'error'
URI_FOR_STATIC_FILES = 'static'


class Id(int):
    """Represents a biv_id"""
    def __new__(cls, biv_id_or_marker, biv_index=None):
        """Pass in an int, str, or existing biv_id"""
        if isinstance(biv_id_or_marker, cls):
            return biv_id_or_marker
        if isinstance(biv_id_or_marker, Marker):
            assert isinstance(biv_index, Index), repr(biv_index) \
                + ': not Index'
            bi = biv_index * _MARKER_MODULUS + biv_id_or_marker
            self = super().__new__(cls, bi)
            self.__marker = biv_id_or_marker
            self.__index = biv_index
        else:
            bi = int(biv_id_or_marker)
            assert _MARKER_MODULUS < bi <= _MAX_ID, str(bi) + ': range'
            self = super().__new__(cls, bi)
            self.__marker = Marker(bi % _MARKER_MODULUS)
            self.__index = Index(bi // _MARKER_MODULUS)
        return self

    @property
    def biv_marker(self):
        """Marker object for this Id"""
        return self.__marker

    @property
    def biv_index(self):
        """Index object for this Id"""
        return self.__index

    def to_biv_uri(self, use_alias=True):
        """Converts a biv_id to a biv_uri.

        :param use_alias: If False, creates encoded uri, always
        """
        if use_alias and self.__int__() in _id_to_alias:
            return _id_to_alias[self.__int__()][0]
        return URI(self)


class Index(int):
    """The sequenced part of an Id"""
    def __new__(cls, biv_index):
        if isinstance(biv_index, cls):
            return biv_index
        bi = int(biv_index)
        if 0 < bi <= _MAX_INDEX:
            return super().__new__(cls, bi)
        werkzeug.exceptions.abort(404)


class Marker(int):
    """The type part of the Id"""
    def __new__(cls, biv_marker):
        if isinstance(biv_marker, cls):
            return biv_marker
        bm = int(biv_marker)
        assert 0 < bm <= _MAX_MARKER, str(biv_marker) + ': range'
        return super().__new__(cls, bm)

    def to_biv_id(self, biv_index):
        "Convert an index value to a biv_id"
        return Id(self, Index(biv_index))


class URI(str):
    """Parses and stores an encoded biv_uri or an alias"""
    def __new__(cls, biv_uri_or_id):
        if isinstance(biv_uri_or_id, cls):
            return biv_uri_or_id
        if isinstance(biv_uri_or_id, Id):
            self = super().__new__(cls, cls.__encode(biv_uri_or_id))
            self.__id = biv_uri_or_id
            return self
        bu = str(biv_uri_or_id)
        self = super().__new__(cls, bu)
        if bu[0] == _ENC_PREFIX:
            self.__id = cls.__decode(bu)
        else:
            if bu not in _alias_to_id:
                import publicprize.auth.model
                alias = publicprize.auth.model.BivAlias.query.filter_by(
                    alias_name=bu
                ).first_or_404()
                register_alias(bu, alias.biv_id)
            self.__id = _alias_to_id[bu]
        return self

    @property
    def biv_id(self):
        """Returns Id for this URI"""
        return self.__id

    @staticmethod
    def __decode(biv_uri):
        bu = biv_uri[1:]
        assert len(bu) >= _MARKER_ENC_LEN, biv_uri + ': too short'
        bm = Marker(_CONV.str2int(bu[-_MARKER_ENC_LEN:]))
        i = _CONV.str2int(bu[:-_MARKER_ENC_LEN])
        return bm.to_biv_id(i)

    @staticmethod
    def __encode(biv_id):
        bm = _CONV.int2str(biv_id.biv_marker).zfill(_MARKER_ENC_LEN)
        bi = _CONV.int2str(biv_id.biv_index)
        return _ENC_PREFIX + bi + bm


def load_obj(biv_uri):
    """Loads the object identified by biv_uri"""
    if biv_uri is None or len(biv_uri) == 0:
        biv_uri = URI_FOR_NONE
    bi = URI(biv_uri).biv_id
    if bi.biv_marker not in _marker_to_class:
        werkzeug.exceptions.abort(404)
    return _marker_to_class[bi.biv_marker].load_biv_obj(bi)


def register_alias(uri, biv_id):
    """Registers biv_id with non-encoded uri"""
    assert uri not in _alias_to_id, uri + ': exists'
    assert not uri[0] == _ENC_PREFIX, uri + ': encoded uri'
    bi = Id(biv_id)
    _alias_to_id[uri] = bi
    bu = URI(uri)
    if bi not in _id_to_alias:
        _id_to_alias[bi] = []
    _id_to_alias[bi].append(bu)
    return bu


def register_marker(biv_marker, cls):
    """Registers a marker in a global table for a model, which can
    load_biv_obj"""
    biv_marker = Marker(biv_marker)
    assert ppi.class_has_method(cls, 'load_biv_obj'), str(cls) \
        + ': missing method'
    assert biv_marker not in _marker_to_class, str(biv_marker) + ': exists'
    _marker_to_class[biv_marker] = cls
    return Marker(biv_marker)

_CONV = numconv.NumConv(radix=62, alphabet=numconv.BASE62)
_ENC_PREFIX = '_'
_IDEMPOTENT_URI = None
_MARKER_MODULUS = 1000
_MAX_ID = int(1e18) - 1
_MAX_INDEX = _MAX_ID // _MARKER_MODULUS
# We reserve 900 and above for versioning and growth
_MAX_MARKER = _MARKER_MODULUS - 101
_MARKER_ENC_LEN = len(_CONV.int2str(_MAX_MARKER))
_marker_to_class = {}
_alias_to_id = {}
_id_to_alias = {}

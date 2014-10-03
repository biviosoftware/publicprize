""" Test_data: Stores data for the acceptance tests """
MAX = {
    'display_name': 100,
    'url_length': 100  # MA: just picking something arbitrary
}

# Store re-used values
GENERIC_FIELDS = {
    'generic_name': {
        'conf': [
            'Generic Name',
            'Name with 123 Numbers',
            '123',  #only numbers
            # special characters currently break the
            # text parser
            '@#$%^&*()',
            # calculated to maximum length string.
            # TODO(pjm): hacked in -4 because some tests add random suffix
            'x' * (MAX['display_name'] - 4),
            #RN Not sure if we should be using 'SingleWord',\n] or this way.
            # what's your opinion?  I prefer first way, but not sure it
            # works in all Python or is "pythonic"
            #MA I think 'SingleWord',\n] is probably best, as it will be easier
            # to add additional entries
            'SingleWord'
            'Unicode monster: «ταБЬℓσ»: 1<2 & 4+1>3, now 20% off!',
            'Escaped \' quotes \"'
        ],
        'dev': [
            '',
            #RN Another thing I like to do is annotate the value so that
            # we can know that the error produced is what we expect.  I
            # do this with a regex, but it isn't always easy and we don't
            # have the framework for it now.
            'x' * (MAX['display_name'] + 1)
        ]
    },
    'generic_desc': {
        'dev': [''],
        'conf': [
            'Generic description',
            '!@#$%^&*()_+=-',  # test special characters
            'Unicode monster: «ταБЬℓσ»: 1<2 & 4+1>3, now 20% off!',
            'Escaped \' quotes \"',
            # test a long description
            ('150 blaas: blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa'
            ),
            # test a very long description
            ('1000 blaas: blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
             'blaa blaa blaa blaa blaa blaa'
            )
        ]
    }
}

FIELDS = {
    #RN
    'display_name': GENERIC_FIELDS['generic_name'],
    'contestant_desc': GENERIC_FIELDS['generic_desc'],
    'youtube_url': {
        'conf': [
            'https://www.youtube.com/watch?v=K5pZlBgXBu0'
        ],
        'dev': [
            '',
            'https://www.youtube.co/watch?v=K5pZlBgXBu0',  #invalid video, extension of a valid one
            'https://www.youtube.com/watch?v=K5pZlBgXBu0lkjsdfjal', #completely invalid video
            'http://www.slideshare.net/Experian_US/how-to-juggle-debt-retirement',
            'https://www.google.com'
        ]
    },
    'slideshow_url': {
        'conf': [
            'http://www.slideshare.net/Experian_US/how-to-juggle-debt-retirement',
            'https://www.slideshare.net/Experian_US/how-to-juggle-debt-retirement'
        ],
        'dev': [
            '',
            'https://www.youtube.com/watch?v=K5pZlBgXBu0',
            'http://www.slideshare.net/Experian_US/how-to-juggle-debt-retirement_bad_link'
        ]
    },
    'website': {
        'conf': [
            'www.google.com',
            'https://www.google.com',
            #RN this could be generated internally
            # and would be better off.  We don't
            # want to allow infinite URLs.  Anything
            # like http://bivio.com/?x=ingored..."
            # works fine so you could just generate
            # ignored with a known length (MAX)
            # Use long url maker to go to google.com
            # MA: Fixed
            'http://bivio.com/?x=ignored' + ('z' * (MAX['url_length'] - 27))
        ],
        'dev': [
            'lsjdfl.alksdjflkdsj.clkj',
            'www.g00gle.com',
            'http://bivio.com/?x=ignored' + ('z' * (MAX['url_length'] - 26))
        ]
    },
    'founder_desc': GENERIC_FIELDS['generic_desc'],
    'tax_id': {
        'conf': ['22-7777777'],
        'dev': ['']
    },
    'business_phone': {
        'conf': [
            '303-123-4567',
            '303 123 4567',
            '1-303-123-4567',
            '1 303 123 4567',
            '303-123-4567-3576',
            '303 123 4567-3576',
            '303 123 4567 3576',
            '1-303-123-4567-3576',
            '1 303 123 4567-3576',
            '1 303 123 4567 3576'
        ],
        'dev': ['']
    },
    'business_address': {
        'conf': [
            '123 Pearl St\nBoulder CO 80303',
            'Unicode monster: «ταБЬℓσ»: 1<2 & 4+1>3, now 20% off!',
            'Escaped \' quotes \"'
        ],
        'dev': [
            '',
            '123 Pearl St'
        ]
    },
    'founder2_name': {
        'conf': GENERIC_FIELDS['generic_name']['conf'],
        'dev': ['x' * (MAX['display_name'] + 1)]
    },
    'founder2_desc': {
        'conf': GENERIC_FIELDS['generic_desc']['conf'],
        'dev': ['x' * (MAX['display_name'] + 1)]
    },
    'agree_to_terms': {
        'conf': [True],
        'dev': [False]
    }
}

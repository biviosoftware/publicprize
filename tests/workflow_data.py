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
            'x ' * int((MAX['display_name'] - 4) / 2),
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
        ]
    }
}

SUBMIT_ENTRY_FIELDS = {
    #RN
    'display_name': GENERIC_FIELDS['generic_name'],
    'contestant_desc': GENERIC_FIELDS['generic_desc'],
    'youtube_url': {
        'conf': [
            'https://www.youtube.com/watch?v=K5pZlBgXBu0'
        ],
        'dev': [
            '',
#            'https://www.youtube.co/watch?v=K5pZlBgXBu0',  #invalid video, extension of a valid one
            'https://www.youtube.com/watch?v=lkjsdfjal', #completely invalid video
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
            '303 123 4567',
            '1-303-123-4567',
            '303 123 4567-3576',
            '1-303-123-4567-3576',
            '1 303 123 4567-3576',
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
            # '123 Pearl St'
        ]
    },
    'founder2_name': {
        'conf': GENERIC_FIELDS['generic_name']['conf'],
        'dev': ['x' * (MAX['display_name'] + 1)]
    },
    'agree_to_terms': {
        'conf': [True],
        'dev': ['']
    }
}

# This is a hardcopy of the values listed in publicprize/contest/model.py
POINTS_PER_QUESTION = [
    10,
    10,
    10,
    5,
    10,
    15
]

JUDGING_POINTS = {
    # MA: I'm not sure whether or not python enables list/set comprehensions
    # nested in data like this. I'm just doing it via hardcoding for now
    'question1': POINTS_PER_QUESTION[0],
    'question2': POINTS_PER_QUESTION[1],
    'question3': POINTS_PER_QUESTION[2],
    'question4': POINTS_PER_QUESTION[3],
    'question5': POINTS_PER_QUESTION[4],
    'question6': POINTS_PER_QUESTION[5],
}

# MA: I'm not sure what would constitute a deviating entry here
JUDGING_FIELDS = {
    'question1': {
        'conf': {1, 2, 3, 4},
        'dev': None
    },
    'question2': {
        'conf': {1, 2, 3, 4},
        'dev': None
    },
    'question3': {
        'conf': {1, 2, 3, 4},
        'dev': None
    },
    'question4': {
        'conf': {1, 2, 3, 4},
        'dev': None
    },
    'question5': {
        'conf': {1, 2, 3, 4},
        'dev': None
    },
    'question6': {
        'conf': {1, 2, 3, 4},
        'dev': None
    },
    'question1_comment': {
        'conf': GENERIC_FIELDS['generic_desc']['conf'],
        'dev': None
    },
    'question2_comment': {
        'conf': GENERIC_FIELDS['generic_desc']['conf'],
        'dev': None
    },
    'question3_comment': {
        'conf': GENERIC_FIELDS['generic_desc']['conf'],
        'dev': None
    },
    'question4_comment': {
        'conf': GENERIC_FIELDS['generic_desc']['conf'],
        'dev': None
    },
    'question5_comment': {
        'conf': GENERIC_FIELDS['generic_desc']['conf'],
        'dev': None
    },
    'question6_comment': {
        'conf': GENERIC_FIELDS['generic_desc']['conf'],
        'dev': None
    },
    'general_comment': {
        'conf': GENERIC_FIELDS['generic_desc']['conf'],
        'dev': None
    }
}

WEBSITE_SUBMISSION_FIELDS = {
    'websites': {
        'conf': [
            'www.bivio.biz-Bivio software',
            'bivio.biz/bp/Clients-Bivio software 2',
            'http://www.bivio.biz-Bivio software',
            'https://www.google.com-Google',
        ],
        'dev': [
            'asldkfjasdklfjalskdjf-x',
            'www.alaskdjfalksdj.com-x',
            'http://www.asdlkfjasdlkfjasdlkfj.com-x',
        ],
    },
}

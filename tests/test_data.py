class SubmitEntryData(object):
    """
        Stores good and bad values for possible entries into the Submit Entry
        page

        Data:
            'display_name'          self.[good|bad]_display_names
            'contestant_desc'       self.[good|bad]_contestant_descriptions
            'youtube_url'           self.[good|bad]_youtube_urls
            'slideshow_url'         self.[good|bad]_slideshow_urls
            'website'               self.[good|bad]_website_urls
            'founder_desc'          self.[good|bad]_founder_descriptions
            'tax_id'                self.[good|bad]_tax_ids
            'business_phone'        self.[good|bad]_phone_nums
            'business_address'      self.[good|bad]_addresses
            'founder2_name'         self.[good|bad]_founder2_names
            'founder2_desc'         self.[good|bad]_founder2_descriptions
            'agree_to_terms'        self.[good|bad]_agree_to_terms
    """

    def __init__(self):

        self.bad_display_names = ['',
                                  'Absurdly long string of text that no one '
                                  'would reasonably enter for a name']
        self.good_display_names = ['Generic Name',
                                   'Name with 123 Numbers',
                                   # special characters currently break the
                                   # text parser
                                   'Name with @#$%^&*() special characters',
                                   'SingleWord',
                                  ]

        self.bad_descs = ['']
        self.good_descs = ['Generic description',
                           '!@#$%^&*()_+=-',  # test special characters
                           # test a long description
                           '150 blaas: blaa blaa blaa blaa blaa blaa blaa ',
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa ',
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa ',
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa ',
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa ',
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa ',
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa ',
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa ',
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa ',
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa ',
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa ',
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa ',
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa ',
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa ',
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa ',
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa ',
                           'blaa blaa blaa blaa blaa blaa blaa blaa'
                           # test a very long description
                           '1000 blaas: blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa blaa blaa blaa blaa blaa blaa blaa '
                           'blaa blaa blaa'
                           ]

        self.good_contestant_descriptions = self.good_descs
        self.bad_contestant_descriptions = self.bad_descs

        self.good_youtube_urls = ['https://www.youtube.com/watch?v=K5pZlBgXBu0']
        self.bad_youtube_urls = ['',
                                 'https://www.youtube.co/watch?v=K5pZlBgXBu0',
                                 'https://www.youtube.com/watch?v=K5pZlBgXBu0lkjsdfjal',
                                 'http://www.slideshare.net/Experian_US/how-to-juggle-debt-retirement',
                                 'https://www.google.com']

        self.good_slideshow_urls = ['http://www.slideshare.net/Experian_US/how-to-juggle-debt-retirement',
                                    'https://www.slideshare.net/Experian_US/how-to-juggle-debt-retirement']
        self.bad_slideshow_urls = ['',
                                   'https://www.youtube.com/watch?v=K5pZlBgXBu0',
                                   'http://www.slideshare.net/Experian_US/how-to-juggle-debt-retirement_bad_link']

        self.good_website_urls = ['www.google.com',
                                  'https://www.google.com',
                                  ]
        self.bad_website_urls = ['',
                                 'lsjdfl.alksdjflkdsj.clkj',
                                 'www.g00gle.com',
                                  # too long
                                  'http://www.longurlmaker.com/go?id=UAOJNVKBMQUGPYZKCQZRZKJEXRCRXMRSMFBZBMBODWUSVTDXJCPJMYOKQQBODSGPYHPZURNXNIQIBUGLWVUJUIUKZVYCOFSNMIMHZAEMIVVKPCVMYPVTYPEYLDBAITNUCACBBHOKCKUSMPEKFADEPHCBLEBTXPOZPQBQXPBAZVSMLXXRXAVMIYNTCPNAEBAURBKORMORHHDTEAKBBGOKEBEGRRHVSHPKIAYZNNQUVUOZUYAVEOGJQKQIBXEUEUEMUDMHRDCMXQLRPMNUBUDSETAGQEAUZFHTITBZXEMUVYMLKAFMUJFYCFFTKGOJLWDUPFUMKGHGETRPTXCNGHMJNRCYXRIINLCDRWQCDXIHRZXKWZYDHKMUCPSZHAIUMLYEIOGMMPUDPROMRNPYXCTARLAYMJTYURDDGKPSZKWOBLBTYQRWSKWKWWJIFCHAULEAVUTUEQJFBKZZBQWUBSEYPNGUQOVKZZKVTEPXUZDVKCVLTRFUKKTZXZTOOPYOOJJINYGHYJDJMYUFQAAAKTZITTXHIVVXEEGSDMZCVDLICGNSGNTRHSAAMXIVSDTXIZPMLPOHTZPVFCNMQHEXZEYMCGHVKBSSAIEMYTTRTJMZMALCHQAHUZUWFBRPCKIDTNPSGIJASWZEWLHEBHMVGGSMIKBLVKOPXDHEMREENEIKPQPQXBMEHFRQQTBLDPBBTIFGZKLNOUYDKNUIPGNXMENCXOOBEPCYYHEYRQLFKJJUXDCMKQJWUWZSLNTQCVOBCTZUJKATUJOSNRFXHOUBLTTXGNNJIBKLVKGEVGYQQMIEENCLCWMNQGKXTXHCZSNVCTZXAYNRLVVPJXALUNZLUKIOIPQHHDDKXDHXBUPMQKCZIDLCQKNLVWZDLPLTTOERRLPSGEFWOIWXLIZCTNNOJNRVDCPXRTOIEEBKIHHXPDUBLUDEHRTQFKMINBFEUUNZYOKHVRELVZMHTQMBIFRNQEWDFCIAWVZVJKCFBHRXGEEAUQBDWTRMXNQCQYDMUDHENKKORBMXFQXAHYEESVQPJHSZGVMAYUFLEPAWRMTWDRXKQCPIXGXHNPHULTVJOAVTQWPHJJEMACXREMABSXJGNQAZKVJZWESMAHTJQYWRATJEGJGYHPEVGFUQADQWHIJIQDSGBOYBIHFORLNYBSTHXNYYQOVYWEHMHZTIOSKXAPMRBZPCSJKPWIONXJLTOTGWSAFHTPFTFRLGQAJIKTYGCMTZWFTLYAHRAMZUCEOHVZOMAYVKRUQUHKTDPMPONWFOJFIMJWTFVIRWGNGYHXTPHMSXZILNFRBOWJAGGULCDDYKQEJYBCNJPGGPOSCTKDIHNJNTEYVHCTSSYBRAEEJTLQJZJLTTOCBCLOVQNRXPLQIJSZKWETQPKZPTKJNZLOCXDXNQPLFABOKTNVQSOGHZGXSRGGQSVSPYQCOGNUHPISJWNZOCGWBMTUDZBURWNHUDJIKXDRNMJWIWWWZCTAOMVSMWMDSZLMDVVNTYFGKODTLZQKBJLQVGIHCVLVUWHYSDMLBRRMGUGSUWDVGOMCVUKYPVTKSAIKDVWFMNSTIYLCVOYBCKEYFOWVKPGCQPNTKJZXXRQFQBIMQHOTRSRXGNTQCZTSOHMZQLWODMUUOCGEJUXBMOZSCSJERDWGKJFBUCPYPJSDMYIWSGYFVXYXQHBIKYOUHUVCXLAMVSPIQYEJEDOZBMWRUYZEWOZEJVGGGGSCZIKQGPZLSOKTAHKUFKZCYYHIUNOBUHDUPNKWDKHVYSPZAAUGKTIJSQRMDGNYNRSDFDAINIELAULBUFHFZQPRGHEKNRIBJBFOEFWRNADOUPPPUWVTNKLTRPDFHLHQNMERSBJGCNUXCKMXHHRUSCNJRRPZDWQQJUIBWSHYFCVINIFVQWPIZDSRUHQXEGONBWPYOXWUASCNAIIRFYZFBSWWANTEUISVEITTFQNFIQTJZCAEAZKCSGYSTSWNAPJFXDYCTLICCCLBEMGFLQHEWGWQZSEAINFFQDHKPQMRSYTWKZCWQJANQWDPPHPXVUCMYKWOBJG'
                                 ]

        self.good_founder_descriptions = self.good_descs
        self.bad_founder_descriptions = self.bad_descs

        self.good_tax_ids = ['22-7777777']
        self.bad_tax_ids = ['',
                            '99999999999999999',
                            '22-777777a',
                            '22-77a7777',
                            '22-77!777a',
                            '22-777*77a',
                            '22M777777a',
                            '22-7}7777a',
                            'ab-cdefghi']

        self.good_phone_nums = ['303-123-4567',
                                '303 123 4567',
                                '1-303-123-4567',
                                '1 303 123 4567',
                                '303-123-4567-3576',
                                '303 123 4567-3576',
                                '303 123 4567 3576',
                                '1-303-123-4567-3576',
                                '1 303 123 4567-3576',
                                '1 303 123 4567 3576']

        self.bad_phone_nums = ['',
                               '1256',
                               '303 abc defg',
                               '303-abc-defg']

        self.good_addresses = ['123 Pearl St\nBoulder CO 80303']
        self.bad_addresses = ['']

        self.good_founder2_names = self.good_display_names
        self.bad_founder2_names = self.good_display_names

        self.good_founder2_descriptions = self.good_descs
        self.bad_founder2_descriptions = self.bad_descs

        self.good_agree_to_terms = [True]
        self.bad_agree_to_terms = [False]

    def get_good_data(self):
        self.items_to_combine = [self.good_display_names,
                                 self.good_contestant_descriptions,
                                 self.good_youtube_urls,
                                 self.good_slideshow_urls,
                                 self.good_website_urls,
                                 self.good_founder_descriptions,
                                 self.good_tax_ids,
                                 self.good_phone_nums,
                                 self.good_addresses,
                                 self.good_founder2_names,
                                 self.good_founder2_descriptions,
                                 self.good_agree_to_terms]
        return self.items_to_combine

    def get_bad_data(self):
        self.items_to_combine = [self.bad_display_names,
                                 self.bad_contestant_descriptions,
                                 self.bad_youtube_urls,
                                 self.bad_slideshow_urls,
                                 self.bad_website_urls,
                                 self.bad_founder_descriptions,
                                 self.bad_tax_ids,
                                 self.bad_phone_nums,
                                 self.bad_addresses,
                                 self.bad_founder2_names,
                                 self.bad_founder2_descriptions,
                                 self.bad_agree_to_terms]
        return self.items_to_combine



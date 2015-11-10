// Copyright (c) 2015 bivio Software, Inc.  All rights reserved.
'use strict';
var app = angular.module('EVC2015App', ['ngRoute', 'ngAnimate']);

app.config(function($routeProvider) {
    $routeProvider
        .when('/contestants', {
            controller: 'NomineeListController as nomineeList',
            templateUrl: '/static/html/nominees.html?' + PUBLIC_PRIZE_APP_VERSION,
        })
        .when('/:nominee_biv_id/contestant', {
            controller: 'NomineeController as nominee',
            templateUrl: '/static/html/nominee.html?' + PUBLIC_PRIZE_APP_VERSION,
        })
        .when('/submit-nominee', {
            controller: 'HomeController as home',
            templateUrl: '/static/html/home.html?' + PUBLIC_PRIZE_APP_VERSION,
        })
        .when('/about', {
            templateUrl: '/static/html/about.html?' + PUBLIC_PRIZE_APP_VERSION,
        })
        .when('/:nominee_biv_id/nominate-thank-you', {
            controller: 'NomineeController as nominee',
            templateUrl: '/static/html/nominate-thank-you.html?' + PUBLIC_PRIZE_APP_VERSION,
        })
        .when('/admin-review-nominees', {
            controller: 'AdminReviewController as adminReview',
            templateUrl: '/static/html/admin-review-nominees.html?' + PUBLIC_PRIZE_APP_VERSION,
        })
        .when('/admin-review-judges', {
            controller: 'AdminJudgesController as adminJudges',
            templateUrl: '/static/html/admin-review-judges.html?' + PUBLIC_PRIZE_APP_VERSION,
        })
        .when('/admin-review-scores', {
            controller: 'AdminScoresController as adminScores',
            templateUrl: '/static/html/admin-review-scores.html?' + PUBLIC_PRIZE_APP_VERSION,
        })
        .when('/admin-review-votes', {
            controller: 'AdminVotesController as adminVotes',
            templateUrl: '/static/html/admin-review-votes.html?' + PUBLIC_PRIZE_APP_VERSION,
        })
        .when('/judging', {
            controller: 'JudgingController as judging',
            templateUrl: '/static/html/judging.html?' + PUBLIC_PRIZE_APP_VERSION,
        })
        .when('/finalists', {
            controller: 'NomineeListController as nomineeList',
            templateUrl: '/static/html/finalists.html?' + PUBLIC_PRIZE_APP_VERSION,
        })
        .otherwise({
            redirectTo: '/finalists',
        });
});

app.factory('serverRequest', function($http, $location) {
    var self = this;

    self.formatFullPath = function(path) {
        var biv = $location.absUrl().match(/\/\/.*?\/(.*?)(#|$)/)[1];
        return '/' + biv + path;
    };

    self.sendRequest = function(url, callback, postData) {
        return $http.post(self.formatFullPath(url), postData).success(function(data) {
            callback(data);
        }).error(function(data, status) {
            console.log(url, ' failed: ', status);
        });
    };
    return self;
});

app.factory('contestState', function(serverRequest) {
    var self = this;
    self.contestInfo = {
        allowNominations: false,
        contestantCount: 0,
        finalistCount: 0,
    };
    serverRequest.sendRequest('/contest-info', function(data) {
        self.contestInfo = data;
    });
    self.allowNominations = function() {
        return self.contestInfo.allowNominations;
    };
    self.contestantCount = function() {
        return self.contestInfo.contestantCount;
    };
    self.finalistCount = function() {
        return self.contestInfo.finalistCount;
    };
    return self;
});

app.factory('userState', function(serverRequest, $rootScope, $location) {
    var self = this;
    self.state = {
        initializing: true,
        randomValue: Math.random(),
    };

    function updateUserState(data) {
        self.state = {
            initializing: false,
            isLoggedIn: data.user_state.is_logged_in,
            isAdmin: data.user_state.is_admin,
            isJudge: data.user_state.is_judge,
            displayName: data.user_state.display_name,
            vote: data.user_state.user_vote,
            randomValue: self.state.randomValue,
            canVote: data.user_state.can_vote,
        };
    }

    self.canVote = function() {
        return self.state.canVote ? true : false;
    };
    self.displayName = function() {
        return self.isLoggedIn() ? self.state.displayName : '';
    };
    self.getVote = function() {
        return self.state.vote;
    };
    self.hasVoted = function() {
        return self.isLoggedIn() && self.state.vote;
    };
    self.isInitializing = function() {
        return self.state.initializing;
    };
    self.isLoggedIn = function() {
        return self.state.isLoggedIn ? true : false;
    };
    self.isAdmin = function() {
        return self.state.isAdmin ? true : false;
    };
    self.isJudge = function() {
        return self.state.isJudge ? true : false;
    };
    self.logout = function() {
        serverRequest.sendRequest('/logout', function(data) {
            updateUserState(data);
            $location.path('/');
            $rootScope.$broadcast('pp.alert', 'You have successfully logged out.');
        });
    };
    self.updateState = function() {
        serverRequest.sendRequest('/user-state', updateUserState);
    }
    self.updateState()
    return self;
});

app.controller('NomineeController', function(serverRequest, userState, $route, $sce, $rootScope, $window) {
    var self = this;
    var nominee_biv_id = $route.current.params.nominee_biv_id;
    var autoplay = $route.current.params.autoplay ? true : false;
    var voting = $route.current.params.vote ? true: false;
    self.info = {};
    self.twitterHandle = '';
    loadNominee();

    function loadNominee() {
        serverRequest.sendRequest(
            '/nominee-info',
            function(data) {
                self.info = data.nominee;
                if (voting && userState.isLoggedIn() && ! userState.hasVoted())
                    $('#voteModal').modal('show');
            },
            {
                nominee_biv_id: nominee_biv_id,
            });
    }

    function nomineeUrl() {
        return '/' + self.info.biv_id  + '/contestant';
    }

    self.fullNomineeUrl = function() {
        return serverRequest.formatFullPath('#' + nomineeUrl());
    };

    self.castVote = function() {
        if (! userState.isLoggedIn()) {
            self.voteUrl = self.fullNomineeUrl() + '?vote=1';
            $('#loginAndVoteModal').modal('show');
            return;
        }
        $('#voteModal').modal('show');
    };

    self.formatURL = function() {
        var url = self.info.url;
        if (! url.match(/\:\/\//))
            url = 'http://' + url;
        return url;
    };

    self.hasVoted = function() {
        return userState.hasVoted();
    };

    self.isJudge = function() {
        return userState.isJudge();
    };

    self.saveVote = function() {
        serverRequest.sendRequest(
            '/nominee-vote',
            function() {
                userState.updateState();
                $('#voteModal').modal('hide');
                $('#tweetModal').modal('show');
                $('#pp-tweet-link').click(function() {
                    open(this.href, '_blank', 'toolbar=0,status=0,width=480,height=360');
                    return false;
                });
            },
            {
                nominee_biv_id: nominee_biv_id,
            })
            .error(function() {
                $('#voteModal').modal('hide');
                $rootScope.$broadcast(
                    'pp.alert',
                    'There was a problem recording your vote. Please contact support@publicprize.com',
                    'danger');
            });
    };

    self.tweetText = function() {
        return 'I just voted for ' + self.info.display_name + ' in the #EspritVentureChallenge sponsored by @BoulderChamber';
    };

    self.tweetVote = function() {
        serverRequest.sendRequest(
            '/nominee-tweet',
            function() {
                userState.updateState();
                $('#tweetModal').modal('hide');
            },
            {
                twitter_handle: self.twitterHandle,
                nominee_biv_id: nominee_biv_id,
            })

    };

    self.userSelection = function() {
        return nominee_biv_id == userState.getVote();
    };

    self.videoURL = function() {
        if (! self.info.url)
            return;
        var url = '//www.youtube.com/embed/' + self.info.youtube_code
            + (autoplay ? '?autoplay=1' : '');
        return $sce.trustAsResourceUrl(url);
    };
});

app.controller('NomineeListController', function(serverRequest, userState, $location) {
    var self = this;
    self.finalists = [];
    self.nominees = [];
    serverRequest.sendRequest(
        '/public-nominee-list',
        function(data) {
            self.nominees = data.nominees;

            for (var i = 0; i < self.nominees.length; i++) {
                if (self.nominees[i].is_finalist)
                    self.finalists.push(self.nominees[i]);
            }
        },
        {
            random_value: userState.state.randomValue,
        });

    function nomineeUrl(nominee) {
        return '/' + nominee.biv_id  + '/contestant';
    }

    self.canVote = function() {
        return userState.canVote() && ! userState.hasVoted();
    };

    self.castVote = function(nominee) {
        if (! userState.isLoggedIn()) {
            self.voteUrl = serverRequest.formatFullPath('#' + nomineeUrl(nominee))
                + '?vote=1';
            $('#loginAndVoteModal').modal('show');
            return;
        }
        $location.path(nomineeUrl(nominee));
        $location.search('vote', 1);
    };

    self.selectNominee = function(nominee, autoplay) {
        $location.path(nomineeUrl(nominee));
        if (autoplay)
            $location.search('autoplay', 1);
    };

    self.userSelection = function(nominee) {
        return nominee.biv_id == userState.getVote();
    };

});

app.controller('HomeController', function(serverRequest, userState, contestState, $location) {
    var MAX_FOUNDERS = 3;
    var self = this;
    self.userState = userState;
    self.formData = {};
    self.formFields = [];
    self.formErrors = {};
    self.founderCount = 1;
    loadFormMetadata();

    function loadFormMetadata() {
        var hidden = {
            founder2_name: true,
            founder2_desc: true,
            founder3_name: true,
            founder3_desc: true,
        };
        serverRequest.sendRequest('/nominee-form-metadata', function(data) {
            self.formFields = data.form_metadata;
            for (var i = 0; i < self.formFields.length; i++)
                self.formFields[i].visible = hidden[self.formFields[i].name] ? false : true;
            //TODO(pjm): timeout is a hack
            setTimeout(
                function() {
                    $('.pp-tooltip').tooltip({
                        'container': 'body'
                    })
                }, 100);
        });
    }

    self.addFounder = function() {
        self.founderCount++;
        for (var i = 0; i < self.formFields.length; i++) {
            var search = 'founder' + self.founderCount;
            if (self.formFields[i].name.indexOf(search) >= 0) {
                self.formFields[i].visible = true;
            }
        }
        if (self.founderCount >= MAX_FOUNDERS)
            $('#addFounderButton').fadeOut();
    };

    self.allowNominations = function() {
        return contestState.allowNominations();
    };

    self.getError = function(name) {
        return self.formErrors[name];
    }

    self.hasError = function(name) {
        return self.getError(name) ? true : false;
    }

    self.saveForm = function() {
        var ladda = Ladda.create(document.querySelector('button.ladda-button'));
        ladda.start();

        serverRequest.sendRequest(
            '/nominee-form-submit',
            function(data) {
                ladda.stop();
                if (data.errors) {
                    self.formErrors = data.errors;
                    return;
                }
                $location.path('/' + data.nominee_biv_id  + '/nominate-thank-you');
            },
            self.formData)
            .error(function(data, status) {
                ladda.stop();
                if (status == 403)
                    self.formErrors.display_name = 'Log in to nominate a company';
            });
    };
});

app.controller('NavController', function () {
    var self = this;
    self.pageTitle = function() {
        return 'Esprit Venture Challenge - Public Prize';
    };
});

app.controller('JudgingController', function(serverRequest) {
    var self = this;
    var rankSuperscript = {
        1: 'st',
        2: 'nd',
        3: 'rd',
    };
    self.MAX_RANKS = 5;
    self.ranks = [
        {
            value: 0,
            text: 'Remove Rank',
        },
        {
            value: 1,
            text: '1st',
        },
        {
            value: 2,
            text: '2nd',
        },
        {
            value: 3,
            text: '3rd',
        },
        {
            value: 4,
            text: '4th',
        },
        {
            value: 5,
            text: '5th',
        },
    ];
    self.nominees = [];
    serverRequest.sendRequest(
        '/judging',
        function(data) {
            self.nominees = data.judging;
        });

    function bumpDown(nominee) {
        var nextNominee = nomineeForRank(nominee.rank + 1);
        if (nextNominee)
            bumpDown(nextNominee);
        nominee.rank++;
    }

    function bumpUp(nominee) {
        var prevNominee = nomineeForRank(nominee.rank - 1);
        if (prevNominee)
            bumpUp(prevNominee);
        nominee.rank--;
    }

    function isMobile() {
        return 'ontouchstart' in document.documentElement;
    }

    function nextRank() {
        for (var r = 1; r <= self.MAX_RANKS; r++) {
            if (! nomineeForRank(r))
                return r;
        }
        return null;
    }

    function nomineeForRank(rank) {
        for (var i = 0; i < self.nominees.length; i++) {
            if (self.nominees[i].rank && self.nominees[i].rank == rank)
                return self.nominees[i];
        }
        return null;
    }

    function rankingCompleted() {
        var rankedCount = 0;
        for (var i = 0; i < self.nominees.length; i++) {
            if (self.nominees[i].rank)
                rankedCount++;
        }
        return rankedCount >= self.MAX_RANKS;
    }

    function saveValues() {
        serverRequest.sendRequest(
            '/judge-ranking',
            updateAutosaveMessage,
            {
                nominees: self.nominees,
            })
            .error(function() {
                self.autoSaveMessage = 'There was a problem recording your ranking. Please contact support@publicprize.com';
            });
    }

    function updateAutosaveMessage() {
        var d = new Date();
        self.autoSaveMessage = (rankingCompleted()
            ? 'Thank you for participating in this contest! '
            : '')
            + 'Autosaved at ' + d.toLocaleTimeString();
    }

    self.hoverNominee = function(nominee, $event) {
        if (isMobile())
            return;
        if (! nominee.rank)
            nominee.hoverRank = nextRank();
    };

    self.endHoverNominee = function(nominee, $event) {
        if (isMobile())
            return;
        nominee.hoverRank = null;
    };

    self.hasComment = function(nominee) {
        return nominee.comment ? true : false;
    }

    self.isDisabled = function(nominee) {
        if (nominee.rank)
            return false;
        return rankingCompleted();
    };

    self.nomineeURL = function(nominee) {
        return '#/' + nominee.biv_id  + '/contestant';
    };

    self.selectNominee = function(nominee, $event) {
        if (nominee.rank)
            return;
        nominee.hoverRank = null;
        nominee.rank = nextRank();
        // hide the dropdown menu
        $($event.currentTarget).dropdown('toggle');
        saveValues();
    };

    self.saveComment = function() {
        self.commentNominee.comment = self.comment;
        $('#commentEditor').modal('hide');
        saveValues();
    };

    self.selectRank = function(nominee, rank) {
        if (! rank.value) {
            nominee.rank = null;
            saveValues();
            return;
        }
        if (nominee.rank == rank.value)
            return;
        var n = nomineeForRank(rank.value);
        if (n) {
            var old_rank = nominee.rank;
            nominee.rank = null;
            if (old_rank > rank.value)
                bumpDown(n);
            else
                bumpUp(n);
        }
        nominee.rank = rank.value;
        saveValues();
    };

    self.showComment = function(nominee) {
        self.commentNominee = nominee;
        self.comment = nominee.comment;
        $('#commentEditor').modal({
            backdrop: 'static',
            show: true,
        });
    };

    self.superscript = function(rank) {
        if (! rank)
            return ''
        return rankSuperscript[rank] || 'th';
    };

});

app.controller('AdminReviewController', function(serverRequest, $sce) {
    var self = this;
    self.nominees = [];
    self.selectedNominee = {};
    serverRequest.sendRequest('/admin-review-nominees', function(data) {
        self.nominees = data.nominees;
    });

    function stopPlaying() {
        $('#videoPlayer').off('hidden.bs.modal', stopPlaying);
        $('#videoPlayer iframe')[0].contentWindow.postMessage('{"event":"command","func":"stopVideo","args":""}', '*');
    }

    self.selectNominee = function(nominee) {
        self.selectedNominee = nominee;
        $('#videoPlayer').modal('show');
        $('#videoPlayer').on('hidden.bs.modal', stopPlaying);
    };

    self.setPublic = function(nominee, isPublic) {
        serverRequest.sendRequest(
            '/admin-set-nominee-visibility',
            function() {
                nominee.is_public = isPublic;
            },
            {
                biv_id: nominee.biv_id,
                is_public: isPublic,
            });
    };

    self.videoURL = function() {
        if (! self.selectedNominee.url)
            return;
        var url = '//www.youtube.com/embed/' + self.selectedNominee.youtube_code + '?autoplay=1&enablejsapi=1';
        return $sce.trustAsResourceUrl(url);
    };
});

app.controller('AdminJudgesController', function(serverRequest) {
    var self = this;
    self.judges = []
    serverRequest.sendRequest('/admin-review-judges', function(data) {
        self.judges = data.judges;
    });
});

app.controller('AdminScoresController', function(serverRequest) {
    var self = this;
    self.scores = [];
    self.totalVotes = 0;
    self.totalJudgeRanks = 0;
    serverRequest.sendRequest('/admin-review-scores', function(data) {
        self.scores = data.scores;
        self.totalVotes = 0;
        self.totalJudgeRanks = 0;

        for (var i = 0; i < self.scores.length; i++) {
            self.totalVotes += self.scores[i].votes;
            self.totalJudgeRanks += self.scores[i].judge_score;
        }
        self.scores.sort(function(a, b) {
            return b.score - a.score;
        });
    });
});

app.controller('AdminVotesController', function(serverRequest) {
    var self = this;
    self.votes = [];
    serverRequest.sendRequest('/admin-review-votes', function(data) {
        self.votes = data.votes;
    });

    self.updateVoteStatus = function(vote, voteStatus) {
        serverRequest.sendRequest(
            '/admin-set-vote-status',
            function() {
                vote.vote_status = voteStatus;
            },
            {
                biv_id: vote.biv_id,
                vote_status: voteStatus,
            });
    };
});

app.directive('loginModal', function() {
    return {
        scope: {
            loginModal: '@',
            loginText: '@',
            nextUrl: '=',
        },
        template: [
            '<div class="modal fade" id="{{ loginModal }}" tabindex="-1" role="dialog">',
              '<div class="modal-dialog">',
                '<div class="modal-content">',
                  '<div class="modal-header pp-modal-header bg-success">',
                    '<button type="button" class="close" data-dismiss="modal"><span>&times;</span></button>',
                    '<h4 class="modal-title">{{ loginText }}</h4>',
                  '</div>',
                  '<div class="pp-login-body modal-body pp-social-icon">',
                    '<a rel="nofollow" href="/pub/linkedin-login{{ nextUrl ? (\'?next=\' + nextUrl) : \'\' }}" class="btn btn-lg pp-login-link"><img src="/static/img/linkedin39.png" alt="LinkedIn"> using LinkedIn</a>',
                  '<br />',
                '</div>',
              '</div>',
            '</div>',
        ].join(''),
    };
});

app.directive('navLinks', function(userState) {
    return {
        scope: {},
        template: [
            '<ul class="nav navbar-nav navbar-right" data-ng-hide="userState.isInitializing()" data-ng-cloak="">',
            '<li data-ng-hide="userState.isLoggedIn()"><a rel="nofollow" class="pp-nav-item" data-toggle="modal" data-target="#signupModal" href>Sign up</a></li>',
            '<li data-ng-hide="userState.isLoggedIn()"><a rel="nofollow" class="pp-nav-item" data-toggle="modal" data-target="#loginModal" href>Log in</a></li>',
            '<li data-ng-show="userState.isAdmin()" class="dropdown"><a class="pp-nav-item pp-nav-important dropdown-toggle" href data-toggle="dropdown">Admin <span class="caret"></span></a>',
              '<ul class="dropdown-menu" role="menu">',
                '<li><a href="#/admin-review-nominees">Review Nominees</a></li>',
                '<li><a href="#/admin-review-judges">Review Judges</a></li>',
                '<li><a href="#/admin-review-scores">Review Scores</a></li>',
                '<li><a href="#/admin-review-votes">Review Votes</a></li>',
              '</ul>',
            '</li>',
            '<li data-ng-show="userState.isJudge()" class="dropdown"><a class="pp-nav-item pp-nav-important dropdown-toggle" href="#/judging" data-toggle="dropdown">Judging</a></li>',
            '<li data-ng-show="userState.isLoggedIn()"><a rel="nofollow" class="pp-nav-item" data-ng-click="userState.logout()" href>Log out</a></li>',
            '</ul>',
        ].join(''),
        controller: function($scope) {
            $scope.userState = userState;
        },
    };
});

app.directive('alertBox', function($rootScope) {
    return {
        scope: {},
        controller: function($scope) {
            $rootScope.$on('pp.alert', function(alert, message, level) {
                $scope.message = message;
                $scope.level = level || 'success';
            });
        },
        template: [
            '<div class="container">',
              '<div class="row">',
                '<div class="alert alert-{{ level }} alert-dismissible" data-ng-show="message" data-ng-class="{slideDown: message}">',
                  '<button type="button" class="close" data-dismiss="alert"><span>&times;</span></button>',
	          '<strong>{{ message }}</strong>',
	        '</div>',
              '</div>',
            '</div>',
        ].join(''),
    };
});

function formFieldTemplate(includeHelp) {
    return [
        '<div data-ng-switch="f.type">',
          '<span data-ng-show="home.hasError(f.name)" class="pp-form-error text-danger">{{ home.getError(f.name) }}</span>',
          '<div data-ng-show="home.hasError(f.name)" class="clearfix"></div>',
            (includeHelp ? '<div class="input-group">' : ''),
              '<div data-ng-switch-when="CSRFTokenField"></div>',
              '<textarea data-ng-switch-when="TextAreaField" class="form-control" data-ng-class="{slideDown: f.visible}" rows="5" placeholder="{{ f.label }}" data-ng-model="home.formData[f.name]"></textarea>',
              '<input data-ng-switch-default class="form-control" type="text" value="" data-ng-class="{slideDown: f.visible}" placeholder="{{ f.label }}" data-ng-model="home.formData[f.name]">',
              (includeHelp ? '<span class="input-group-addon"><span class= "pp-tooltip" data-toggle="tooltip" title="{{ f.helpText }}"><span class="glyphicon glyphicon-info-sign text-primary"></span></span></span>' : ''),
            (includeHelp ? '</div>' : ''),
          '</div>',
        '</div>',
    ].join('');
}

app.directive('formField', function() {
    return {
        scope: {
            f: '=formField',
            home: '=controller',
        },
        template: formFieldTemplate(false),
    };
});

app.directive('formFieldWithHelp', function() {
    return {
        scope: {
            f: '=formFieldWithHelp',
            home: '=controller',
        },
        template: formFieldTemplate(true),
    };
});

app.directive('sponsorList', function() {
    return {
        scope: {
            includeCarousel: '=',
        },
        template: [
//TODO(pjm): get leader list and link to contestant page
            // '<div class="col-sm-4" data-ng-show="showCarousel()">',
            //   '<h3>Contest Leaders</h3>',
            //   '<div id="pp-carousel" class="carousel slide">',
            //     '<div class="carousel-inner" role="listbox">',
            //       '<div data-ng-repeat="leader in leaders" class="item" data-ng-class="{\'active\': $index == 0}">',
            //         '<img data-ng-src="https://img.youtube.com/vi/{{ leader.youtube_code }}/mqdefault.jpg" alt="{{ leader.display_name }}">',
            //         '<div class="carousel-caption">{{ leader.display_name }}</div>',
            //       '</div>',
            //     '</div>',
            //   '</div>',
            // '</div>',
            '<div class="col-sm-3 col-sm-offset-1 col-xs-12 pp-sidebar">',
            '<h1>Sponsors</h1>',
            '<div class="row">',
              '<div data-ng-repeat="sponsor in sponsors">',
                '<div class="col-sm-12 col-xs-6">',
                  '<div class="pp-sidebar-module pp-sidebar-module-inset pp-sponsor-sidebar pp-sponsor-images">',
                    '<a href="{{ sponsor.website }}" target="_blank">',
                    '<img style="padding: 30px 0; width: 100%; max-width: 150px" data-ng-src="{{ \'/\' + sponsor.biv_id + \'/sponsor_logo\' }}"lt="{{ sponsor.display_name }}" /></a>',
                  '</div>',
                '</div>',
                '<div data-ng-class="{clearfix: $index %2}"></div>',
              '</div>',
            '</div>',
            '</div>',
        ].join(''),
        controller: function($scope, serverRequest) {
            $scope.sponsors = [];
            // $scope.leaders = [
            //     {
            //         display_name: 'Test item 1',
            //         youtube_code: '8nHBGFKLHZQ',
            //     },
            //     {
            //         display_name: 'Another Item',
            //         youtube_code: 'NbuUW9i-mHs',
            //     },
            //     {
            //         display_name: 'Last Item',
            //         youtube_code: 'MVbeoSPqRs4',
            //     },
            // ];
            // $scope.showCarousel = function() {
            //     return $scope.leaders.length && $scope.includeCarousel;
            // }
            serverRequest.sendRequest('/sponsors', function(data) {
                $scope.sponsors = data.sponsors;
            });
        },
        link: function(scope, element) {
            $(element).find('#pp-carousel').carousel({});
        }
    };
});

app.directive('sectionNav', function($location) {
    return {
        scope: {},
        template: [
            '<br />',
            '<ul class="nav nav-justified">',
              '<li data-ng-class="{\'pp-active-menu\': isSelected(\'finalists\') }"><a class="btn btn-default" href="#/finalists">Finalists <span class="badge">{{ finalistCount() }}</span></a></li>',
              '<li data-ng-class="{\'pp-active-menu\': isSelected(\'contestants\') }"><a class="btn btn-default" href="#/contestants">Contestants <span class="badge">{{ contestantCount() }}</span></a></li>',
              '<li data-ng-class="{\'pp-active-menu\': isSelected(\'about\') }"><a class="btn btn-default" href="#/about">About</a></li>',
            '</ul>',
        ].join(''),
        controller: function($scope, contestState) {
            $scope.contestantCount = function() {
                return contestState.contestantCount();
            };
            $scope.finalistCount = function() {
                return contestState.finalistCount();
            };
            $scope.isSelected = function(path) {
                return $location.path().indexOf(path) >= 0;
            };
        },
    };
});

app.animation('.slideDown', function() {
    return {
        addClass: function(element, className, done) {
            if (className == 'slideDown') {
                $(element).hide();
                $(element).slideDown(done);
            }
        },
    }
});

app.filter('urlEncode', function() {
    return window.encodeURIComponent;
});

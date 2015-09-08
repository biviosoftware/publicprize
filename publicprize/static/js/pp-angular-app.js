// Copyright (c) 2015 bivio Software, Inc.  All rights reserved.
'use strict';
var app = angular.module('EVC2015App', ['ngRoute']);

app.config(function($routeProvider) {
    $routeProvider
        .when('/home', {
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
        .otherwise({
            redirectTo: '/home',
        });
});

app.factory('serverRequest', function($http, $location) {
    var self = this;
    self.sendRequest = function(url, callback, postData) {
        var biv = $location.absUrl().match(/\/\/.*?\/(.*?)(#|$)/)[1];
        return $http.post('/' + biv + url, postData).success(function(data) {
            callback(data);
        }).error(function(data, status) {
            console.log(url, ' failed: ', status);
        });
    };
    return self;
});

app.factory('userState', function(serverRequest) {
    var self = this;
    self.state = {};

    function updateUserState(data) {
        self.state = {
            isLoggedIn: data.user_state.is_logged_in,
            isAdmin: data.user_state.is_admin,
            isJudge: data.user_state.is_judge,
        };
    }

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
        serverRequest.sendRequest('/logout', updateUserState);
    };
    self.updateState = function() {
        serverRequest.sendRequest('/user-state', updateUserState);
    }
    self.updateState()
    return self;
});

app.controller('NomineeController', function(serverRequest, $route) {
    var self = this;
    var nominee_biv_id = $route.current.params.nominee_biv_id;
    self.info = {};
    loadNominee();

    function loadNominee() {
        serverRequest.sendRequest(
            '/nominee-info',
            function(data) {
                self.info = data.nominee;
            },
            {
                nominee_biv_id: nominee_biv_id,
            });
    }
});

app.controller('HomeController', function(serverRequest, userState, $location) {
    var MAX_FOUNDERS = 3;
    var self = this;
    self.userState = userState;
    self.formData = {};
    self.formFields = [];
    self.formErrors = {};
    self.founderCount = 1;
    self.sponsors = [];
    hideFounders();
    loadFormMetadata();
    loadSponsors();

    function hideFounders() {
        //TODO(pjm): timeout is a hack
        setTimeout(
            function() {
                var fields = ['founder2_name', 'founder2_desc', 'founder3_name', 'founder3_desc']
                for (var i = 0; i < fields.length; i++)
                    $('#' + fields[i]).hide();
            }, 100);
    }

    function loadFormMetadata() {
        serverRequest.sendRequest('/nominee-form-metadata', function(data) {
            self.formFields = data.form_metadata;
        });
    }

    function loadSponsors() {
        serverRequest.sendRequest('/sponsors', function(data) {
            self.sponsors = data.sponsors;
        });
    }

    self.addFounder = function() {
        self.founderCount++;
        $('#founder' + self.founderCount + '_name').fadeIn();
        $('#founder' + self.founderCount + '_desc').fadeIn();
        if (self.founderCount >= MAX_FOUNDERS)
            $('#addFounderButton').fadeOut();
    };

    self.getError = function(name) {
        return self.formErrors[name];
    }

    self.hasError = function(name) {
        return self.getError(name) ? true : false;
    }

    self.saveForm = function() {
        serverRequest.sendRequest(
            '/nominee-form-submit',
            function(data) {
                if (data.errors) {
                    self.formErrors = data.errors;
                    return;
                }
                $location.path('/' + data.nominee_biv_id  + '/nominate-thank-you');
            },
            self.formData)
            .error(function(data, status) {
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

app.directive('loginModal', function() {
    return {
        scope: {
            loginModal: '@',
            loginText: '@',
        },
        template: [
            '<div class="modal fade" id="{{ loginModal }}" tabindex="-1" role="dialog">',
              '<div class="modal-dialog">',
                '<div class="modal-content">',
                  '<div class="modal-header">',
                    '<button type="button" class="close" data-dismiss="modal"><span>&times;</span></button>',
                    '<h4 class="modal-title">{{ loginText }}</h4>',
                  '</div>',
                  '<div class="pp-login-body modal-body pp-social-icon">',
                    '<a rel="nofollow" href="/pub/linkedin-login" class="btn btn-lg pp-login-link"><img src="/static/img/linkedin39.png" alt="LinkedIn"> using LinkedIn</a>',
                  '<br />',
                '</div>',
              '</div>',
            '</div>',
        ].join(''),
    };
});

app.directive('navLinks', function(userState) {
    return {
        scope: {
        },
        template: [
            '<li data-ng-hide="userState.isLoggedIn()"><a rel="nofollow" class="pp-nav-item" data-toggle="modal" data-target="#signupModal" href>Sign up</a></li>',
            '<li data-ng-hide="userState.isLoggedIn()"><a rel="nofollow" class="pp-nav-item" data-toggle="modal" data-target="#loginModal" href>Log in</a></li>',
            '<li data-ng-show="userState.isLoggedIn()"><a rel="nofollow" class="pp-nav-item" data-ng-click="userState.logout()" href>Log out</a></li>',
        ].join(''),
        controller: function($scope) {
            $scope.userState = userState;
        },
    };
});

// Copyright (c) 2015 bivio Software, Inc.  All rights reserved.
'use strict';
var app = angular.module('EVC2015App', ['ngRoute', 'ngAnimate']);

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

app.factory('userState', function(serverRequest, $rootScope) {
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
        serverRequest.sendRequest('/logout', function(data) {
            updateUserState(data);
            $rootScope.$broadcast('pp.alert', 'You have successfully logged out.');
        });
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
    loadFormMetadata();
    loadSponsors();

    function hideFounders() {
    }

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

    function loadSponsors() {
        serverRequest.sendRequest('/sponsors', function(data) {
            self.sponsors = data.sponsors;
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
        scope: {},
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

app.directive('alertBox', function($rootScope) {
    return {
        scope: {},
        controller: function($scope) {
            $rootScope.$on('pp.alert', function(alert, message) {
                $scope.message = message;
            });
        },
        template: [
            '<div class="container">',
              '<div class="row">',
                '<div class="alert alert-success alert-dismissible" data-ng-show="message" data-ng-class="{slideDown: message}">',
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

//TODO(pjm): really ugly, combine formField with formFieldWithHelp
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

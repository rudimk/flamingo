// Generated by CoffeeScript 1.3.1
var __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; },
  __hasProp = {}.hasOwnProperty,
  __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor; child.__super__ = parent.prototype; return child; };

define(['chaplin/mediator', 'chaplin/lib/utils', 'chaplin/lib/services/service_provider'], function(mediator, utils, ServiceProvider) {
  'use strict';

  var Custom;
  return Custom = (function(_super) {

    __extends(Custom, _super);

    Custom.name = 'Custom';

    Custom.prototype.name = 'custom';

    Custom.prototype.status = null;

    Custom.prototype.accessToken = null;

    Custom.prototype.sessionId = null;

    function Custom() {
      this.publishAbortionResult = __bind(this.publishAbortionResult, this);

      this.loginHandler = __bind(this.loginHandler, this);

      this.loginStatusHandler = __bind(this.loginStatusHandler, this);

      this.getLoginStatus = __bind(this.getLoginStatus, this);

      this.saveAuthResponse = __bind(this.saveAuthResponse, this);
      Custom.__super__.constructor.apply(this, arguments);
      console.debug('Custom#constructor');
      this.subscribeEvent('logout', this.logout);
    }

    Custom.prototype.dispose = function() {};

    Custom.prototype.loadSDK = function() {
      return this.resolve();
    };

    Custom.prototype.isLoaded = function() {
      return true;
    };

    Custom.prototype.saveAuthResponse = function(response) {
      console.debug('Custom#saveAuthResponse', response);
      this.status = !response.is_anonymous;
      return this.sessionId = response.id;
    };

    Custom.prototype.getLoginStatus = function(callback, force) {
      var response;
      if (callback == null) {
        callback = this.loginStatusHandler;
      }
      if (force == null) {
        force = false;
      }
      console.debug('Custom#getLoginStatus');
      response = $.get('/account/sessions/');
      return response.success(callback);
    };

    Custom.prototype.loginStatusHandler = function(response) {
      var authResponse;
      console.debug('Custom#loginStatusHandler', response);
      this.saveAuthResponse(response);
      authResponse = response.is_anonymous;
      if (!authResponse) {
        return this.publishSession(response);
      } else {
        return mediator.publish('logout');
      }
    };

    Custom.prototype.triggerLogin = function(loginContext) {
      console.debug('Custom#triggerLogin', loginContext, this.sessionId);
      return $.ajax({
        url: "/account/sessions/" + this.sessionId,
        contentType: 'application/json',
        type: 'put',
        data: JSON.stringify(loginContext),
        processData: false,
        complete: _(this.loginHandler).bind(this)
      });
    };

    Custom.prototype.loginHandler = function(loginContext, status) {
      var response;
      console.debug('Custom#loginHandler', loginContext, status);
      response = JSON.parse(loginContext.responseText);
      switch (status) {
        case 'error':
          mediator.publish('loginFail', response);
          break;
        case 'success':
          mediator.publish('loginSuccessful', response);
      }
      return this.getLoginStatus(this.publishAbortionResult, true);
    };

    Custom.prototype.publishSession = function(authResponse) {
      console.debug('Custom#publishSession', authResponse);
      return mediator.publish('serviceProviderSession', {
        provider: this,
        userId: authResponse.userID,
        accessToken: authResponse.accessToken
      });
    };

    Custom.prototype.publishAbortionResult = function(response) {
      var authResponse;
      this.saveAuthResponse(response);
      authResponse = response.authResponse;
      if (authResponse) {
        mediator.publish('loginSuccessful', {
          provider: this,
          loginContext: loginContext
        });
        mediator.publish('loginSuccessfulThoughAborted', {
          provider: this,
          loginContext: loginContext
        });
        return this.publishSession(authResponse);
      } else {
        return mediator.publish('loginFail', {
          provider: this,
          loginContext: loginContext
        });
      }
    };

    Custom.prototype.logout = function() {
      return this.status = this.accessToken = null;
    };

    return Custom;

  })(ServiceProvider);
});

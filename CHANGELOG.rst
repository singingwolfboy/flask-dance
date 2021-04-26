Changelog
=========

`unreleased`_
-------------
nothing yet

`4.0.0`_ (2021-04-10)
---------------------
* Dropped support for Python 2 and Python 3.5
* If you are using the SQLAlchemy token storage, this project now depends on
  SQLAlchemy version 1.3.11 and above. `sqlalchemy-utils` is no longer necessary.
* Added `verify_tls_certificates` option to `make_gitlab_blueprint`
* Added Twitch pre-set configuration

`3.3.1`_ (2021-03-01)
---------------------
* Added `hostname` option to the `make_salesforce_blueprint`
* Added `is_sandbox` option to the `make_salesforce_blueprint`
* Changed base url for `make_salesforce_blueprint`

`3.3.0`_ (2021-02-25)
---------------------
* Added Atlassian pre-set configuration
* Added Salesforce pre-set configuration
* Added `offline` option to `make_dropbox_blueprint`
* Added `prompt` option to `make_discord_blueprint`
* Added `subdomain` option to `make_slack_blueprint`

`3.2.0`_ (2020-11-24)
---------------------
Added Digital Ocean pre-set configuration

`3.1.0`_ (2020-10-29)
---------------------
* Updated Discord to use the new discord.com instead of the old discordapp.com
* Add Strava pre-set configuration

`3.0.0`_ (2019-10-21)
---------------------
* Updated Meetup and Nylas pre-set configurations
  to include the ``client_id`` in the OAuth token request.
* Removed Okta pre-set configuration, since it doesn't add any value over
  using ``OAuth2ConsumerBlueprint`` directly.
* Updated Azure to allow defining ``authorization_url_params``

`2.2.0`_ (2019-06-04)
---------------------
* Added Heroku pre-set configuration

`2.1.0`_ (2019-05-15)
---------------------
* Flask-Dance now provides a ``betamax_record_flask_dance`` testing fixture,
  for recording and replaying HTTP requests using Betamax_. See the testing
  documentation for more information.
* Added LinkedIn pre-set configuration

`2.0.0`_ (2019-03-30)
---------------------

Changed (**backwards incompatible**)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* The backwards-compatible references to "backend" have been removed.
  Use "storage" instead.
* The columns defined in ``OAuthConsumerMixin`` now set ``nullable=False``.
  If you are using the SQLAlchemy storage and are upgrading from a previous
  version of Flask-Dance, you may want to do a database migration.
* Previously, Flask-Dance had an undocumented
  feature where it would automatically redirect based on a ``next``
  parameter in the URL. This undocumented feature has been removed.
* All pre-set configurations now use a consistent
  naming scheme for pulling client IDs and client secrets from the app config.
  The following configurations have changed: Dropbox, Meetup, Twitter,
  and Zoho.
* Replace ``lazy`` dependency with
  `werkzeug.utils.cached_property <http://werkzeug.pocoo.org/docs/0.14/utils/#werkzeug.utils.cached_property>`__

`1.4.0`_ (2019-02-22)
---------------------

Changed
~~~~~~~
* "Backends" are now called "Storages", since the word "backend" means
  something different in the context of web development. This release
  is fully backwards-compatible, but deprecation warnings have been
  added anywhere that you import and use a backend (rather than a
  storage).

Added
~~~~~
* Add ``oauth_before_login`` signal
* Add ``reprompt_select_account`` parameter to google blueprint

`1.3.0`_ (2019-01-14)
---------------------

Added
~~~~~
* Add ``authorization_required`` decorator
* Added Authentiq pre-set configuration

`1.2.0`_ (2018-12-05)
---------------------

Added
~~~~~
* Added ``rerequest_declined_permissions`` argument to facebook blueprint
* Added Reddit pre-set configuration

`1.1.0`_ (2018-09-12)
---------------------

Added
~~~~~
* Added ``tenant`` argument to ``make_azure_blueprint``
* Added ``hosted_domain`` argument to ``make_google_blueprint``
* Added Okta pre-set configuration
* Added Zoho pre-set configuration

Fixed
~~~~~
* Updated Azure AD default scopes. See `issue 149`_.
* Only set ``auto_refresh_url`` in ``make_google_blueprint`` if a token of
  type ``offline`` is requested. See issues `#143`_, `#144`_ and `#161`_ for
  background.

`1.0.0`_ (2018-06-04)
------------------
* Flask-Cache is deprecated. Switch to Flask-Caching.
* When using the OAuth 1 blueprint with the SQLAlchemy backend and the
  ``user_required`` argument set to ``True``, the backend was trying to load
  tokens before any were set, causing an exception in the backend.
  Now, the backend will not attempt to load tokens until the OAuth dance
  is complete.
* Added exception handler around ``parse_authorization_response`` in OAuth1

`0.14.0`_ (2018-03-14)
-------------------
* Accessing the ``access_token`` property on an instance of the
  ``OAuth2Session`` class will now query the token backend, instead of
  checking the client on the instance.
* Pre-set configuration for GitLab provider

`0.13.0`_ (2017-11-12)
-------------------
* sphinxcontrib-napoleon is no longer required to build the Flask-Dance
  documentation.
* Added Spotify pre-set configuration
* Added Discord pre-set configuration
* Added an optional ``user_required`` argument to the SQLAlchemy backend.
  When this is enabled, trying to set an OAuth object without an associated
  user will raise an error.

`0.12.0`_ (2017-10-22)
-------------------
* Updated the Dropbox configuration to use the v2 authentication URLs
* Added the "require_role" authentication parameter for Dropbox
* Documented all authentication parameters for Dropbox

`0.11.1`_ (2017-07-31)
-------------------
* Changed Nylas configuration to refer to "client_id" and "client_secret"
  rather than "api_id" and "api_secret".

`0.11.0`_ (2017-07-24)
-------------------
* Added the Nylas pre-set configuration
* Improve timezone handling for OAuth 2 token refreshing.
* Update tests and docs regarding ``OAuthConsumerMixin`` inheritance.
* Fix Dropbox documentation regarding default ``login_url`` and
  ``authorized_url``

`0.10.1`_ (2016-11-21)
-------------------
* Fixed ``make_google_blueprint`` to include ``auto_refresh_url`` so that
  token renewal is automatically handled by ``requests-oauthlib``

`0.10.0`_ (2016-09-27)
-------------------
* Added the Azure AD pre-set configuration
* Improve OAuth 2 token auto-refresh

`0.9.0`_ (2016-07-1)
-----------------
* Allowed an ``oauth_authorized`` event handler to return a ``flask.Response``
  instance. If so, that response will be sent to the requesting user.

`0.8.3`_ (2016-05-18)
------------------
* Fixed an error that occurred if you were running an unreleased version
  of Flask, due to the version comparison code. See `issue 53`_.
  Thanks, @ThiefMaster!

`0.8.2`_ (2015-12-30)
------------------
* If the OAuth 1 token request is denied on accessing the login view,
  Flask-Dance will now redirect the user and fire the ``oauth_error`` signal.
  This matches the behavior of how Flask-Dance handles OAuth 2 errors.

`0.8.1`_ (2015-12-28)
------------------
* Fixed a typo in the Slack configuration, where it would load the OAuth 2
  client secret from a config variable named "SLLACK_OAUTH_CLIENT_SECRET"
  instead of "SLACK_OAUTH_CLIENT_SECRET"

`0.8.0`_ (2015-12-28)
------------------
* Added the Slack pre-set configuration
* Fixed a subtle bug where setting the ``client_id`` property on an instance
  of ``OAuth2ConsumerBlueprint`` did not update the value that the ``oauthlib``
  library uses to create the redirect URL in the login step. ``client_id`` is
  now a dynamic property on ``OAuth2ConsumerBlueprint``, which sets the
  ``client_id`` property on the wrapped ``oauthlib`` client automatically.
* Added some debug log statements to ``OAuth2ConsumerBlueprint``
* You can now define a ``session_created`` method on subclasses of
  ``OAuth2ConsumerBlueprint``. If you do, it will be called when a Requests
  session is dynamically created, so that the session can be modified before
  it is returned.

`0.7.1`_ (2015-12-12)
------------------
* Removed the Dictective utility class, and replaced it with
  ``werkzeug.datastructures.CallbackDict``. It does the same thing, but
  it's better tested, and already a part of one of Flask-Dance's dependencies.
* If the user hits the ``authorized`` view without having a "state" variable
  set in the browser cookies, Flask-Dance will now redirect the user back
  to the ``login`` view to start the OAuth dance all over again, rather than
  raising a ``KeyError``.

`0.7.0`_ (2015-08-21)
------------------
* Flask-Dance no longer checks for the existence of a ``X-Forwarded-Proto``
  header to determine if generated URLs should use a ``https://`` scheme.
  If you are running your application behind a TLS termination proxy,
  use Werkzeug's ``ProxyFix`` middleware to inform Flask of that.

`0.6.0`_ (2015-05-12)
------------------
* Added the Dropbox pre-set configuration
* Added the Meetup pre-set configuration
* Added the Facebook pre-set configuration
* Flask-Dance now always passes the optional ``redirect_uri`` parameter to
  the OAuth 2 authorization request, since Dropbox requires it.
* Make Flask-Dance provide additional information in errors when providers fail
  to provide auth tokens

`0.5.1`_ (2015-04-28)
------------------
* Make the ``authorized`` property on both ``OAuth1Session`` and ``OAuth2Session``
  dynamically load the token from the backend

`0.5.0`_ (2015-04-20)
------------------
* Redesigned token storage backend system: it now uses objects

.. warning::
   This release is not backwards-compatible, due to the changes to how backends
   work. If you are using the SQLAlchemy backend, read the documentation to see
   how it works now!

* Added documentation about OAuth protocol
* Added quickstarts for Google, and for a multi-user SQLAlchemy system
* Added ``reprompt_consent`` parameter to Google pre-set configuration
* Added ``oauth_error`` signal
* If there is an error with the OAuth 2 authorization process, Flask-Dance
  will now redirect the user anyway rather than letting the error bubble up
  and cause a 500 status code. The ``oauth_error`` signal will be fired
  with information about the error.

`0.4.3`_ (2015-03-09)
------------------
* ``OAuth2ConsumerBlueprint`` now accepts two new arguments to its constructor:
  ``authorization_url_params`` and ``token_url_params``
* When using the Google pre-set configuration, you can now request offline
  access for your OAuth token by passing ``offline=True`` to the
  ``make_google_blueprint`` function

`0.4.2`_ (2015-03-01)
------------------
* Added ``anon_user`` argument to ``set_token_storage_sqlalchemy()`` method
* Fire ``oauth_authorized`` signal before setting token, so that a signal
  handler can set the logged-in user
* You can now indicate that an OAuth token should not be stored by returning
  ``False`` from any receiver function that is connected to the
  ``oauth_authorized`` signal

`0.4.1`_ (2015-02-28)
------------------
* ``OAuth1SessionWithBaseURL`` has been renamed to ``OAuth1Session``. The old
  name still exists as an alias, for backwards compatibility.
* ``OAuth2SessionWithBaseURL`` has been renamed to ``OAuth2Session``. The old
  name still exists as an alias, for backwards compatibility.
* You can now pass a ``user`` or ``user_id`` object to ``blueprint.load_token``.
* ``OAuth1Session`` and ``OAuth2Session`` now store a reference to the blueprint,
  so that you can also call ``session.load_token``, which is proxied to the
  blueprint. This method also takes ``user`` or ``user_id`` arguments.


`0.4.0`_ (2015-02-12)
------------------
* Renamed ``assign_token_to_session`` to ``load_token``
* Added a ``from_config`` dict to OAuthConsumerBlueprint objects. The info
  in that dict is used to dynamically populate information on the blueprint
  at runtime from the configuration of the app that the blueprint is bound to.
  Also set up sensible configuration variable names for the pre-set
  configurations.
* If neither ``redirect_url`` nor ``redirect_to`` are specified, default to
  redirecting the user to the root of the website (``/``). Previously,
  specifying one of these two options was required.

`0.3.2`_ (2015-01-06)
------------------
* Added a the Google pre-set configuration.

`0.3.1`_ (2014-12-16)
------------------
* Added a new ``session_class`` parameter, so that you can specify a custom
  requests.Session subclass with custom behavior.

`0.3.0`_ (2014-12-15)
------------------
* Changed ``OAuthConsumerMixin.created_on`` to ``OAuthConsumerMixin.created_at``,
  to reflect the fact that it is a DateTime, not a Date. If you are upgrading
  from an older version of Flask-Dance and using ``OAuthConsumerMixin``,
  this will require a database migration.

`0.2.3`_ (2014-10-13)
------------------
* Renamed ``OAuthMixin`` to ``OAuthConsumerMixin``

`0.2.2`_ (2014-10-13)
------------------
* Changed event sender from app to blueprint, to match docs

`0.2.1`_ (2014-10-13)
------------------
* Fixed packaging problems

`0.2`_ (2014-10-12)
----------------
* Added SQLAlchemy support
* Added Sphinx-based documentation
* Added support for Flask-Login and Flask-Cache
* Switch from ``login_callback`` decorator to blinker signals

`0.1`_ (2014-09-15)
----------------
* Initial release

.. _Betamax: https://betamax.readthedocs.io/
.. _issue 53: https://github.com/singingwolfboy/flask-dance/issues/53
.. _issue 149: https://github.com/singingwolfboy/flask-dance/issues/149
.. _#143: https://github.com/singingwolfboy/flask-dance/issues/143
.. _#144: https://github.com/singingwolfboy/flask-dance/issues/144
.. _#161: https://github.com/singingwolfboy/flask-dance/issues/161


.. _unreleased: https://github.com/singingwolfboy/flask-dance/compare/v4.0.0...HEAD
.. _4.0.0: https://github.com/singingwolfboy/flask-dance/compare/v3.3.1...v4.0.0
.. _3.3.1: https://github.com/singingwolfboy/flask-dance/compare/v3.3.0...v3.3.1
.. _3.3.0: https://github.com/singingwolfboy/flask-dance/compare/v3.2.0...v3.3.0
.. _3.2.0: https://github.com/singingwolfboy/flask-dance/compare/v3.1.0...v3.2.0
.. _3.1.0: https://github.com/singingwolfboy/flask-dance/compare/v3.0.0...v3.1.0
.. _3.0.0: https://github.com/singingwolfboy/flask-dance/compare/v2.2.0...v3.0.0
.. _2.2.0: https://github.com/singingwolfboy/flask-dance/compare/v2.1.0...v2.2.0
.. _2.1.0: https://github.com/singingwolfboy/flask-dance/compare/v2.0.0...v2.1.0
.. _2.0.0: https://github.com/singingwolfboy/flask-dance/compare/v1.4.0...v2.0.0
.. _1.4.0: https://github.com/singingwolfboy/flask-dance/compare/v1.3.0...v1.4.0
.. _1.3.0: https://github.com/singingwolfboy/flask-dance/compare/v1.2.0...v1.3.0
.. _1.2.0: https://github.com/singingwolfboy/flask-dance/compare/v1.1.0...v1.2.0
.. _1.1.0: https://github.com/singingwolfboy/flask-dance/compare/v1.0.0...v1.1.0
.. _1.0.0: https://github.com/singingwolfboy/flask-dance/compare/v0.14.0...v1.0.0
.. _0.14.0: https://github.com/singingwolfboy/flask-dance/compare/v0.13.0...v0.14.0
.. _0.13.0: https://github.com/singingwolfboy/flask-dance/compare/v0.12.0...v0.13.0
.. _0.12.0: https://github.com/singingwolfboy/flask-dance/compare/v0.11.1...v0.12.0
.. _0.11.1: https://github.com/singingwolfboy/flask-dance/compare/v0.11.0...v0.11.1
.. _0.11.0: https://github.com/singingwolfboy/flask-dance/compare/v0.10.0...v0.11.0
.. _0.10.1: https://github.com/singingwolfboy/flask-dance/compare/v0.10.0...v0.10.1
.. _0.10.0: https://github.com/singingwolfboy/flask-dance/compare/v0.9.0...v0.10.0
.. _0.9.0: https://github.com/singingwolfboy/flask-dance/compare/v0.8.3...v0.9.0
.. _0.8.3: https://github.com/singingwolfboy/flask-dance/compare/v0.8.2...v0.8.3
.. _0.8.2: https://github.com/singingwolfboy/flask-dance/compare/v0.8.1...v0.8.2
.. _0.8.1: https://github.com/singingwolfboy/flask-dance/compare/v0.8.0...v0.8.1
.. _0.8.0: https://github.com/singingwolfboy/flask-dance/compare/v0.7.1...v0.8.0
.. _0.7.1: https://github.com/singingwolfboy/flask-dance/compare/v0.7.0...v0.7.1
.. _0.7.0: https://github.com/singingwolfboy/flask-dance/compare/v0.6.0...v0.7.0
.. _0.6.0: https://github.com/singingwolfboy/flask-dance/compare/v0.5.1...v0.6.0
.. _0.5.1: https://github.com/singingwolfboy/flask-dance/compare/v0.5.0...v0.5.1
.. _0.5.0: https://github.com/singingwolfboy/flask-dance/compare/v0.4.3...v0.5.0
.. _0.4.3: https://github.com/singingwolfboy/flask-dance/compare/v0.4.2...v0.4.3
.. _0.4.2: https://github.com/singingwolfboy/flask-dance/compare/v0.4.1...v0.4.2
.. _0.4.1: https://github.com/singingwolfboy/flask-dance/compare/v0.4.0...v0.4.1
.. _0.4.0: https://github.com/singingwolfboy/flask-dance/compare/v0.3.2...v0.4.0
.. _0.3.2: https://github.com/singingwolfboy/flask-dance/compare/v0.3.1...v0.3.2
.. _0.3.1: https://github.com/singingwolfboy/flask-dance/compare/v0.3.0...v0.3.1
.. _0.3.0: https://github.com/singingwolfboy/flask-dance/compare/v0.2.3...v0.3.0
.. _0.2.3: https://github.com/singingwolfboy/flask-dance/compare/v0.2.2...v0.2.3
.. _0.2.2: https://github.com/singingwolfboy/flask-dance/compare/v0.2.1...v0.2.2
.. _0.2.1: https://github.com/singingwolfboy/flask-dance/compare/v0.2...v0.2.1
.. _0.2: https://github.com/singingwolfboy/flask-dance/compare/v0.1...v0.2
.. _0.1: https://github.com/singingwolfboy/flask-dance/compare/9b458e401a0...v0.1

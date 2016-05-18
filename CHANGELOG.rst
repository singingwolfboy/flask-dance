Change Log
==========

unreleased
----------
Nothing yet

0.8.3 (2016-05-18)
------------------
* Fixed an error that occurred if you were running an unreleased version
  of Flask, due to the version comparison code. See `issue 53`_.
  Thanks, @ThiefMaster!

0.8.2 (2015-12-30)
------------------
* If the OAuth 1 token request is denied on accessing the login view,
  Flask-Dance will now redirect the user and fire the ``oauth_error`` signal.
  This matches the behavior of how Flask-Dance handles OAuth 2 errors.

0.8.1 (2015-12-28)
------------------
* Fixed a typo in the Slack configuration, where it would load the OAuth 2
  client secret from a config variable named "SLLACK_OAUTH_CLIENT_SECRET"
  instead of "SLACK_OAUTH_CLIENT_SECRET"

0.8.0 (2015-12-28)
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

0.7.1 (2015-12-12)
------------------
* Removed the Dictective utility class, and replaced it with
  ``werkzeug.datastructures.CallbackDict``. It does the same thing, but
  it's better tested, and already a part of one of Flask-Dance's dependencies.
* If the user hits the ``authorized`` view without having a "state" variable
  set in the browser cookies, Flask-Dance will now redirect the user back
  to the ``login`` view to start the OAuth dance all over again, rather than
  raising a ``KeyError``.

0.7.0 (2015-08-21)
------------------
* Flask-Dance no longer checks for the existence of a ``X-Forwarded-Proto``
  header to determine if generated URLs should use a ``https://`` scheme.
  If you are running your application behind a TLS termination proxy,
  use Werkzeug's ``ProxyFix`` middleware to inform Flask of that.

0.6.0 (2015-05-12)
------------------
* Added the Dropbox pre-set configuration
* Added the Meetup pre-set configuration
* Added the Facebook pre-set configuration
* Flask-Dance now always passes the optional ``redirect_uri`` parameter to
  the OAuth 2 authorization request, since Dropbox requires it.
* Make Flask-Dance provide additional information in errors when providers fail
  to provide auth tokens

0.5.1 (2015-04-28)
------------------
* Make the ``authorized`` property on both ``OAuth1Session`` and ``OAuth2Session``
  dynamically load the token from the backend

0.5.0 (2015-04-20)
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

0.4.3 (2015-03-09)
------------------
* ``OAuth2ConsumerBlueprint`` now accepts two new arguments to its constructor:
  ``authorization_url_params`` and ``token_url_params``
* When using the Google pre-set configuration, you can now request offline
  access for your OAuth token by passing ``offline=True`` to the
  ``make_google_blueprint`` function

0.4.2 (2015-03-01)
------------------
* Added ``anon_user`` argument to ``set_token_storage_sqlalchemy()`` method
* Fire ``oauth_authorized`` signal before setting token, so that a signal
  handler can set the logged-in user
* You can now indicate that an OAuth token should not be stored by returning
  ``False`` from any receiver function that is connected to the
  ``oauth_authorized`` signal

0.4.1 (2015-02-28)
------------------
* ``OAuth1SessionWithBaseURL`` has been renamed to ``OAuth1Session``. The old
  name still exists as an alias, for backwards compatibility.
* ``OAuth2SessionWithBaseURL`` has been renamed to ``OAuth2Session``. The old
  name still exists as an alias, for backwards compatibility.
* You can now pass a ``user`` or ``user_id`` object to ``blueprint.load_token``.
* ``OAuth1Session`` and ``OAuth2Session`` now store a reference to the blueprint,
  so that you can also call ``session.load_token``, which is proxied to the
  blueprint. This method also takes ``user`` or ``user_id`` arguments.


0.4.0 (2015-02-12)
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

0.3.2 (2015-01-06)
------------------
* Added a the Google pre-set configuration.

0.3.1 (2014-12-16)
------------------
* Added a new ``session_class`` parameter, so that you can specify a custom
  requests.Session subclass with custom behavior.

0.3.0 (2014-12-15)
------------------
* Changed ``OAuthConsumerMixin.created_on`` to ``OAuthConsumerMixin.created_at``,
  to reflect the fact that it is a DateTime, not a Date. If you are upgrading
  from an older version of Flask-Dance and using ``OAuthConsumerMixin``,
  this will require a database migration.

0.2.3 (2014-10-13)
------------------
* Renamed ``OAuthMixin`` to ``OAuthConsumerMixin``

0.2.2 (2014-10-13)
------------------
* Changed event sender from app to blueprint, to match docs

0.2.1 (2014-10-13)
------------------
* Fixed packaging problems

0.2 (2014-10-12)
----------------
* Added SQLAlchemy support
* Added Sphinx-based documentation
* Added support for Flask-Login and Flask-Cache
* Switch from ``login_callback`` decorator to blinker signals

0.1 (2014-09-15)
----------------
* Initial release

.. _issue 53: https://github.com/singingwolfboy/flask-dance/issues/53

Change Log
==========

unreleased
----------
Nothing yet

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

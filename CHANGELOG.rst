Change Log
==========

unreleased
----------
* Renamed ``assign_token_to_session`` to ``load_token``
* Added a ``from_config`` dict to OAuthConsumerBlueprint objects. The info
  in that dict is used to dynamically populate information on the blueprint
  at runtime from the configuration of the app that the blueprint is bound to.
  Also set up sensible configuration variable names for the pre-set
  configurations.

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

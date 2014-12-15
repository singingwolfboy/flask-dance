Change Log
==========

unreleased
----------
nothing yet

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

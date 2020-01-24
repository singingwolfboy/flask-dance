Quickstart
==========

The fastest way to get up and running with Flask-Dance is to start from
an example project. First, decide which :doc:`token storage
<storages>` you want to use:

* :class:`~flask_dance.consumer.storage.session.SessionStorage` is the default
  because it requires zero configuration. It uses the
  :ref:`Flask session <flask:sessions>` to store OAuth tokens.
  It's the easiest for getting started, but it's not a good choice for
  production applications.
* :class:`~flask_dance.consumer.storage.sqla.SQLAlchemyStorage` uses a
  relational database to store OAuth tokens. It's great for production usage,
  but it requires a relational database with `SQLAlchemy`_
  and it's more complicated to set up.

If you're not sure which to pick, start with ``SessionStorage``.
You can switch later, if you want.

Next, check the lists below to find the OAuth provider you're interested in
and jump to an example project that uses Flask-Dance with that provider!

Flask sessions (easiest)
------------------------

* `GitHub <https://github.com/singingwolfboy/flask-dance-github>`__
* `Google <https://github.com/singingwolfboy/flask-dance-google>`__
* `Facebook <https://github.com/singingwolfboy/flask-dance-facebook>`__
* `Slack <https://github.com/singingwolfboy/flask-dance-slack>`__
* `Twitter <https://github.com/singingwolfboy/flask-dance-twitter>`__
* `LinkedIn <https://github.com/singingwolfboy/flask-dance-linkedin>`__
* `Heroku <https://github.com/singingwolfboy/flask-dance-heroku>`__

SQLAlchemy
----------

* `Google <https://github.com/singingwolfboy/flask-dance-google-sqla>`__
* `Google with Flask-Security <https://github.com/singingwolfboy/flask-dance-google-security-sqla>`__
* `Twitter <https://github.com/singingwolfboy/flask-dance-twitter-sqla>`__
* `Facebook <https://github.com/singingwolfboy/flask-dance-facebook-sqla>`__
* `Heroku <https://github.com/singingwolfboy/flask-dance-heroku-sqla>`__
* `Multiple providers simultaneously <https://github.com/singingwolfboy/flask-dance-multi-provider>`__

.. admonition:: Other Providers

    Don't see the OAuth provider you want? Flask-Dance provides
    :doc:`built-in support for even more providers <providers>`,
    and you can configure Flask-Dance to support
    :ref:`any custom provider you want <custom-provider>`.
    Start with any of the example projects listed above, and modify it to use
    the provider you want!

.. _SQLAlchemy: http://www.sqlalchemy.org/

Flask-Dance
===========

Doing the OAuth dance with style using `Flask`_, `requests`_, and `oauthlib`_.
Check out just how easy it can be to hook up your Flask app with OAuth:

.. code-block:: python

    from flask import Flask, redirect, url_for
    from flask_dance.contrib.github import make_github_blueprint, github

    app = Flask(__name__)
    app.secret_key = "supersekrit"  # Replace this with your own secret!
    blueprint = make_github_blueprint(
        client_id="my-key-here",
        client_secret="my-secret-here",
    )
    app.register_blueprint(blueprint, url_prefix="/login")

    @app.route("/")
    def index():
        if not github.authorized:
            return redirect(url_for("github.login"))
        resp = github.get("/user")
        assert resp.ok
        return "You are @{login} on GitHub".format(login=resp.json()["login"])

Ready to get started?

.. _Flask: http://flask.pocoo.org/
.. _requests: http://python-requests.org/
.. _oauthlib: https://oauthlib.readthedocs.io/

User Guide
----------

.. toctree::
   :maxdepth: 1

   install
   quickstart
   concepts
   understanding-the-magic
   multi-user
   logout
   examples

Options & Configuration
-----------------------

.. toctree::
   :maxdepth: 2

   providers
   storages
   signals

Advanced Topics
---------------

.. toctree::
   how-oauth-works
   proxies
   testing
   api
   contributing

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


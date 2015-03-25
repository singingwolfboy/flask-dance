Quickstart
==========
For a few popular services, Flask-Dance provides :doc:`pre-set configurations
<contrib>`. For example, to authenticate with Github, just do the following::

    from flask import Flask, redirect, url_for
    from flask_dance.contrib.github import make_github_blueprint, github

    app = Flask(__name__)
    github_blueprint = make_github_blueprint(
        client_id="my-key-here",
        client_secret="my-secret-here",
        scope="user:email",
    )
    app.register_blueprint(github_blueprint, url_prefix="/login")

    @app.route("/")
    def index():
        if not github.authorized:
            return redirect(url_for("github.login"))
        resp = github.get("/user/emails")
        assert resp.ok
        emails = [result["email"] for result in resp.json()]
        return " ".join(emails)

The ``github`` object is a `context local`_, just like :obj:`flask.request`.
That means that you can import it in any Python file you want, and use it
in the context of an incoming HTTP request. If you've split your Flask app up
into multiple different files, feel free to import this object in any
of your files, and use it just like you would use the `requests`_ module.

.. _context local: http://flask.pocoo.org/docs/latest/quickstart/#context-locals
.. _requests: http://python-requests.org/

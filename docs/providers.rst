Providers
=========
Flask-Dance comes with pre-set OAuth consumer configurations
for a few popular OAuth providers. Flask-Dance also works with providers
that aren't in this list: see the :ref:`Custom <custom-provider>` section
at the bottom of the page.
We also welcome pull requests to add new pre-set provider configurations
to Flask-Dance!

.. contents:: Included Providers
   :local:
   :backlinks: none

Facebook
--------
.. module:: flask_dance.contrib.facebook

.. autofunction:: make_facebook_blueprint

.. data:: facebook

    A :class:`~werkzeug.local.LocalProxy` to a :class:`requests.Session` that
    already has the Facebook authentication token loaded (assuming that the user
    has authenticated with Facebook at some point in the past).

GitHub
------
.. module:: flask_dance.contrib.github

.. autofunction:: make_github_blueprint

.. data:: github

    A :class:`~werkzeug.local.LocalProxy` to a :class:`requests.Session` that
    already has the GitHub authentication token loaded (assuming that the user
    has authenticated with GitHub at some point in the past).

Google
------
.. module:: flask_dance.contrib.google

.. autofunction:: make_google_blueprint

.. data:: google

    A :class:`~werkzeug.local.LocalProxy` to a :class:`requests.Session` that
    already has the Google authentication token loaded (assuming that the user
    has authenticated with Google at some point in the past).

Twitter
-------
.. module:: flask_dance.contrib.twitter

.. autofunction:: make_twitter_blueprint

.. data:: twitter

    A :class:`~werkzeug.local.LocalProxy` to a :class:`requests.Session` that
    already has the Twitter authentication token loaded (assuming that the user
    has authenticated with Twitter at some point in the past).

JIRA
----
.. module:: flask_dance.contrib.jira

.. autofunction:: make_jira_blueprint

.. data:: jira

    A :class:`~werkzeug.local.LocalProxy` to a :class:`requests.Session` that
    already has the JIRA authentication token loaded (assuming that the user
    has authenticated with JIRA at some point in the past).

Dropbox
-------
.. module:: flask_dance.contrib.dropbox

.. autofunction:: make_dropbox_blueprint

.. data:: dropbox

    A :class:`~werkzeug.local.LocalProxy` to a :class:`requests.Session` that
    already has the Dropbox authentication token loaded (assuming that the user
    has authenticated with Dropbox at some point in the past).

Meetup
------
.. module:: flask_dance.contrib.meetup

.. autofunction:: make_meetup_blueprint

.. data:: meetup

    A :class:`~werkzeug.local.LocalProxy` to a :class:`requests.Session` that
    already has the Meetup authentication token loaded (assuming that the user
    has authenticated with Meetup at some point in the past).

Slack
-----
.. module:: flask_dance.contrib.slack

.. autofunction:: make_slack_blueprint

.. data:: slack

    A :class:`~werkzeug.local.LocalProxy` to a :class:`requests.Session` that
    already has the Slack authentication token loaded (assuming that the user
    has authenticated with Slack at some point in the past).

.. _custom-provider:

Custom
------

Flask-Dance allows you to build authentication blueprints for any OAuth
provider, not just the ones listed above. For example, let's create a blueprint
for a fictional OAuth provider called oauth-example.com. We check the
documentation for oauth-example.com, and discover that they're using OAuth 2,
the access token URL is ``https://oauth-example.com/login/access_token``,
and the authorization URL is ``https://oauth-example.com/login/authorize``.
We could then build the blueprint like this:

.. code-block:: python

    from flask import Flask
    from flask_dance.consumer import OAuth2ConsumerBlueprint

    app = Flask(__name__)
    example_blueprint = OAuth2ConsumerBlueprint(
        "oauth-example", __name__,
        client_id="my-key-here",
        client_secret="my-secret-here",
        base_url="https://oauth-example.com",
        token_url="https://oauth-example.com/login/access_token",
        authorization_url="https://oauth-example.com/login/authorize",
    )
    app.register_blueprint(example_blueprint, url_prefix="/login")

Now, in your page template, you can do something like:

.. code-block:: jinja

    <a href="{{ url_for("oauth-example.login") }}">Login with OAuth Example</a>

And in your views, you can make authenticated requests using the
:attr:`~flask_dance.consumer.OAuth2ConsumerBlueprint.session` attribute on the
blueprint:

.. code-block:: python

    resp = example_blueprint.session.get("/user")
    assert resp.ok
    print("Here's the content of my response: " + resp.content)

It all follows the same patterns as the :doc:`quickstarts/index`. You can also read
the code to see how the pre-set configurations are implemented -- it's very
short.

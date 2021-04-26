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

Atlassian
---------
.. module:: flask_dance.contrib.atlassian

.. autofunction:: make_atlassian_blueprint

.. data:: atlassian

    A :class:`~werkzeug.local.LocalProxy` to a :class:`requests.Session` that
    already has the Atlassian authentication token loaded (assuming
    that the user has authenticated with Atlassian at some point in the past).

Authentiq
---------
.. module:: flask_dance.contrib.authentiq

.. autofunction:: make_authentiq_blueprint

.. data:: authentiq

    A :class:`~werkzeug.local.LocalProxy` to a :class:`requests.Session` that
    already has the Authentiq Connect authentication token loaded (assuming
    that the user has authenticated with Authentiq at some point in the past).

Azure
-----
.. module:: flask_dance.contrib.azure

.. autofunction:: make_azure_blueprint

.. data:: azure

    A :class:`~werkzeug.local.LocalProxy` to a :class:`requests.Session` that
    already has the Azure AD authentication token loaded (assuming that the user
    has authenticated with Azure AD at some point in the past).

Digital Ocean
-------------
.. module:: flask_dance.contrib.digitalocean

.. autofunction:: make_digitalocean_blueprint

.. data:: digitalocean

    A :class:`~werkzeug.local.LocalProxy` to a :class:`requests.Session` that
    already has the Digital Ocean authentication token loaded (assuming that 
    the user has authenticated with Digital Ocean at some point in the past).

Discord
-------
.. module:: flask_dance.contrib.discord

.. autofunction:: make_discord_blueprint

.. data:: discord

    A :class:`~werkzeug.local.LocalProxy` to a :class:`requests.Session` that
    already has the Discord authentication token loaded (assuming that the user
    has authenticated with Discord at some point in the past).

Dropbox
-------
.. module:: flask_dance.contrib.dropbox

.. autofunction:: make_dropbox_blueprint

.. data:: dropbox

    A :class:`~werkzeug.local.LocalProxy` to a :class:`requests.Session` that
    already has the Dropbox authentication token loaded (assuming that the user
    has authenticated with Dropbox at some point in the past).

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

GitLab
------
.. module:: flask_dance.contrib.gitlab

.. autofunction:: make_gitlab_blueprint

.. data:: gitlab

    A :class:`~werkzeug.local.LocalProxy` to a :class:`requests.Session` that
    already has the GitLab authentication token loaded (assuming that the user
    has authenticated with GitLab at some point in the past).

Google
------
.. module:: flask_dance.contrib.google

.. autofunction:: make_google_blueprint

.. data:: google

    A :class:`~werkzeug.local.LocalProxy` to a :class:`requests.Session` that
    already has the Google authentication token loaded (assuming that the user
    has authenticated with Google at some point in the past).

Heroku
------
.. module:: flask_dance.contrib.heroku

.. autofunction:: make_heroku_blueprint

.. data:: heroku

    A :class:`~werkzeug.local.LocalProxy` to a :class:`requests.Session` that
    already has the Heroku authentication token loaded (assuming that the user
    has authenticated with Heroku at some point in the past).

JIRA
----
.. module:: flask_dance.contrib.jira

.. autofunction:: make_jira_blueprint

.. data:: jira

    A :class:`~werkzeug.local.LocalProxy` to a :class:`requests.Session` that
    already has the JIRA authentication token loaded (assuming that the user
    has authenticated with JIRA at some point in the past).

LinkedIn
--------
.. module:: flask_dance.contrib.linkedin

.. autofunction:: make_linkedin_blueprint

.. data:: linkedin

    A :class:`~werkzeug.local.LocalProxy` to a :class:`requests.Session` that
    already has the LinkedIn authentication token loaded (assuming that the user
    has authenticated with LinkedIn at some point in the past).

Meetup
------
.. module:: flask_dance.contrib.meetup

.. autofunction:: make_meetup_blueprint

.. data:: meetup

    A :class:`~werkzeug.local.LocalProxy` to a :class:`requests.Session` that
    already has the Meetup authentication token loaded (assuming that the user
    has authenticated with Meetup at some point in the past).

Nylas
-----
.. module:: flask_dance.contrib.nylas

.. autofunction:: make_nylas_blueprint

.. data:: nylas

    A :class:`~werkzeug.local.LocalProxy` to a :class:`requests.Session` that
    already has the Nylas authentication token loaded (assuming that the user
    has authenticated with Nylas at some point in the past).

Reddit
------
.. module:: flask_dance.contrib.reddit

.. autofunction:: make_reddit_blueprint

.. data:: reddit

    A :class:`~werkzeug.local.LocalProxy` to a :class:`requests.Session` that
    already has the Reddit authentication token loaded (assuming that the user
    has authenticated with Reddit at some point in the past).

Salesforce
----------
.. module:: flask_dance.contrib.salesforce

.. autofunction:: make_salesforce_blueprint

.. data:: salesforce

    A :class:`~werkzeug.local.LocalProxy` to a :class:`requests.Session` that
    already has the Salesforce authentication token loaded (assuming
    that the user has authenticated with Salesforce at some point in the past).

Slack
-----
.. module:: flask_dance.contrib.slack

.. autofunction:: make_slack_blueprint

.. data:: slack

    A :class:`~werkzeug.local.LocalProxy` to a :class:`requests.Session` that
    already has the Slack authentication token loaded (assuming that the user
    has authenticated with Slack at some point in the past).

Strava
------
.. module:: flask_dance.contrib.strava

.. autofunction:: make_strava_blueprint

.. data:: strava

    A :class:`~werkzeug.local.LocalProxy` to a :class:`requests.Session` that
    already has the Strava authentication token loaded (assuming that the user
    has authenticated with Strava at some point in the past).

Twitch
-------
.. module:: flask_dance.contrib.twitch

.. autofunction:: make_twitch_blueprint

.. data:: twitch

    A :class:`~werkzeug.local.LocalProxy` to a :class:`requests.Session` that
    already has the Twitch authentication token loaded (assuming that the user
    has authenticated with Twitch at some point in the past).

Twitter
-------
.. module:: flask_dance.contrib.twitter

.. autofunction:: make_twitter_blueprint

.. data:: twitter

    A :class:`~werkzeug.local.LocalProxy` to a :class:`requests.Session` that
    already has the Twitter authentication token loaded (assuming that the user
    has authenticated with Twitter at some point in the past).

Spotify
-------
.. module:: flask_dance.contrib.spotify

.. autofunction:: make_spotify_blueprint

.. data:: spotify

    A :class:`~werkzeug.local.LocalProxy` to a :class:`requests.Session` that
    already has the Spotify authentication token loaded (assuming that the user
    has authenticated with Spotify at some point in the past).

Zoho
----
.. module:: flask_dance.contrib.zoho

.. autofunction:: make_zoho_blueprint

.. data:: zoho

    A :class:`~werkzeug.local.LocalProxy` to a :class:`requests.Session` that
    already has the Zoho authentication token loaded (assuming that the user
    has authenticated with Zoho at some point in the past).

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

It all follows the same patterns as the :doc:`quickstart` example projects.
You can also read the code to see how the pre-set configurations are
implemented -- it's very short.

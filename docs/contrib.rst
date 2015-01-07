Pre-set Configurations
======================
Flask-Dance comes with pre-set OAuth consumer configurations
for a few popular OAuth providers. If you want to use Flask-Dance with an
OAuth provider that isn't listed here, simply create an instance of
:class:`~flask_dance.consumer.OAuth1ConsumerBlueprint` or
:class:`~flask_dance.consumer.OAuth2ConsumerBlueprint`
and provide the information for your provider. We also welcome pull requests
to add new pre-set configurations to Flask-Dance!

.. contents:: Included Configurations
   :local:
   :backlinks: none

Github
------
.. module:: flask_dance.contrib.github

.. autofunction:: make_github_blueprint

.. data:: github

    A :class:`~werkzeug.local.LocalProxy` to a :class:`requests.Session` that
    already has the Github authentication token loaded (assuming that the user
    has authenticated with Github at some point in the past).

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

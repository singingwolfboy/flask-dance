Pre-set Configurations
======================
Flask-Dance comes with pre-set OAuth consumer configurations
for a few popular services. If you want to use Flask-Dance with a service
that isn't listed here, simply create an instance of
:class:`~flask_dance.consumer.OAuth1ConsumerBlueprint` or
:class:`~flask_dance.consumer.OAuth2ConsumerBlueprint`
and provide the information for your service. We also welcome pull requests
to add new pre-set configurations to Flask-Dance!

Github
------
.. autofunction:: flask_dance.contrib.github.make_github_blueprint

.. py:data:: flask_dance.contrib.github.github

    A :class:`~werkzeug.local.LocalProxy` to a :class:`requests.Session` that
    already has the Github authentication token loaded (assuming that the user
    has authenticated with Github at some point in the past).

Twitter
-------
.. autofunction:: flask_dance.contrib.twitter.make_twitter_blueprint

.. py:data:: flask_dance.contrib.twitter.twitter

    A :class:`~werkzeug.local.LocalProxy` to a :class:`requests.Session` that
    already has the Twitter authentication token loaded (assuming that the user
    has authenticated with Twitter at some point in the past).

JIRA
-------
.. autofunction:: flask_dance.contrib.jira.make_jira_blueprint

.. py:data:: flask_dance.contrib.jira.jira

    A :class:`~werkzeug.local.LocalProxy` to a :class:`requests.Session` that
    already has the JIRA authentication token loaded (assuming that the user
    has authenticated with JIRA at some point in the past).

Logging Out
===========

Many websites use OAuth as an authentication system (see :doc:`multi-user`
for more information). Although this can work quite well, it gets more
complicated when you want to allow the user to log out of your website.
For starters, we need to understand what "logging out" even *means*.

Local Accounts vs Provider Accounts
-----------------------------------

When you use OAuth as an authentication system, your users still have
local accounts on your system. OAuth allows your users to log in
with a provider (such as Google or Facebook), and use their provider
login to authenticate to your local account. Essentially, the
exchange looks something like this, if we assume that "CustomSite"
is the name of your website, and it's using the Google provider:

1.  User: Hey CustomSite, I'm user ShinyStar99. Let me in.
2.  CustomSite: Sorry user, anyone could claim that and I don't trust you.
    How do I know you're telling the truth?
3.  User: My friend Google can back me up. You trust Google, right?
4.  CustomSite: Yes, I trust Google. Hey Google, who is this user?
5.  Google: Hold on, I need to ask my user if I have permission to
    give you any information at all. Hey User, CustomSite wants
    to know who you are. Do you want me to tell CustomSite some
    basic information about you?
6.  User: Yes, please.
7.  Google: Alright CustomSite, I can tell you that on *my* website,
    this user has the ID 987654.
8.  CustomSite: Alright, let me check my database.
    Google user ID 987654 matches up with one of my local users,
    with ID 12345. And it looks like that local user is ShinyStar99!
9.  User: You see? I told you so!
10. CustomSite: Come in, ShinyStar99. Who's next?

In this exchange, you can see that there are two *different* user accounts
involved: one user account on Google, and one user account on CustomSite.
They have different user IDs, and could contain different sets of information,
even though they both represent the same user.

So if you want to cause a user to log out, what exactly do you mean?
We'll go step-by-step through the different options.

Log Out Local Account
---------------------

If you want to cause a user to log out of their local user account,
check the documentation for whatever system you're using to manage
local accounts. If you're using `Flask-Login`_ (or `Flask-Security`_,
which is built on top of Flask-Login), you can import and call the
:func:`flask_login.logout_user` function, like this:

.. code-block:: python
    :emphasize-lines: 6

    from flask_login import logout_user
    # other imports as necessary

    @app.route("/logout")
    def logout():
        logout_user()
        return redirect(somewhere)

After you do this, your application will treat the user like any other
anonymous user. However, logging out your user from their local account
doesn't do anything about the provider account. As a result, if the
user tries to log in again after you've logged them out this way,
the conversation will look like this:

1.  User: Hey CustomSite, I'm user ShinyStar99. Let me in.
    Ask Google if you don't believe me.
2.  CustomSite: Hey Google, who is this user?
3.  Google: My user already gave me permission to tell you some
    basic information. On *my* website, this user has the ID 987654.
4.  CustomSite: Oh right, it's ShinyStar99 again. Go ahead.

In most cases, this is what you want. However, sometimes you want to
really reset things back to the start, as though the user had never
granted consent to share information in the first place.

Revoking Access with the Provider
---------------------------------

Undoing the user's permission to share information from the provider
to your custom site is called "revoking access". Unfortunately,
every provider has a different way of doing this, so you'll need
to check the OAuth documentation provided by your OAuth provider.

When you are granted access by a user, the provider will give your
application a "token" that is used for making subsequent API requests.
In order to revoke access for a user, you may need to include this
token as an argument, so the provider knows which token to revoke.
You can get this information by checking the ``token`` property of the
Flask-Dance blueprint.

We'll use Google as an example. First, check
`Google's documentation for how to revoke access via OAuth2
<https://developers.google.com/identity/protocols/OAuth2WebServer#tokenrevoke>`_.
Notice that you do indeed need to provide the token in order to revoke it.

Here's some sample code that works with Google:

.. code-block:: python
    :emphasize-lines: 12-16

    from flask import Flask, redirect
    from flask_dance.contrib.google import make_google_blueprint, google
    from flask_login import logout_user

    app = Flask(__name__)
    blueprint = make_google_blueprint()
    app.register_blueprint(blueprint, url_prefix="/login")

    @app.route("/logout")
    def logout():
        token = blueprint.token["access_token"]
        resp = google.post(
            "https://accounts.google.com/o/oauth2/revoke",
            params={"token": token},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert resp.ok, resp.text
        logout_user()        # Delete Flask-Login's session cookie
        del blueprint.token  # Delete OAuth token from storage
        return redirect(somewhere)

After the user uses this method to log out, Google will not remember that they
granted consent to share information with your website.

.. warning::

    In this sample code, we are using an :keyword:`assert` statement.
    This works fine for debugging, but not for production. Be sure to modify
    this code to appropriately handle cases where there is an API failure
    when trying to revoke the token.

.. note::

    In this code, we already have a reference to the ``blueprint`` object,
    so we could grab the token easily. But what if you don't have access
    to that object? Instead, you can use the :data:`flask.current_app` proxy
    to pull out the blueprint object you need. For example, instead of
    this line:

    .. code-block:: python

        token = blueprint.token["access_token"]

    You could use this line instead:

    .. code-block:: python

        token = current_app.blueprints["google"].token["access_token"]


Log Out Provider Account
------------------------

You can log out the user from their local account, and you can revoke access
with the provider. But what about logging the user out from their provider
account? Can you force the user to type their password into Google again
if they want to log in to your website in the future?

The short answer is: no, you can't. You can't control how a user interacts
with other websites, except for in the ways that those other websites
specifically allow you to. And since this could potentially be used as
part of a security exploit, websites will generally *not* allow you
to force users to log out.

.. _Flask-Login: https://flask-login.readthedocs.io/
.. _Flask-Security: https://pythonhosted.org/Flask-Security/

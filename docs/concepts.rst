Concepts
========

In order to use OAuth and Flask-Dance correctly, there are a few
basic concepts you need to understand. This page will summarize
these concepts, and provide links for further information.

OAuth
-----

OAuth is a system that allows two websites to securely share information.
Usually (but not always), OAuth is used to allow users to grant permission
to share information from one website to another website.

An OAuth **provider** is a website that *provides* information about users
to other websites. An OAuth **consumer** is a website that requests information
from an OAuth provider. Before an OAuth provider will provide information about
a user to an OAuth consumer, the provider must ask the user to grant permission
to share that information with the consumer.

Before an OAuth provider will even speak to a consumer, the consumer must get
a **client ID** and **client secret** from that provider. It's a bit like
how some website require you to create an account before you can do anything
else. OAuth providers do this so that they keep track of which consumers
they are sharing information with. If a consumer starts using information to do
evil things (like hacking or impersonating users), the provider can use
this information to deactivate that consumer's access to the provider's API.

After a user grants permission to share their data with a consumer, the
provider gives that consumer an **OAuth token**. This token records the fact
that the consumer has permission to access the information, and the consumer
must provide this token on *every API request*. If the consumer ever loses
this token, it has to get a new one, which might involve asking the user
for permission again. As a result, OAuth tokens must be stored somewhere
and retrieved as necessary.

.. warning::

    If an attacker manages to steal an OAuth token from a consumer,
    the attacker can use that token to do evil things to the user
    that granted permission for that token. This could cause the
    OAuth provider to deactivate the consumer from their API.
    Be careful with OAuth tokens, and store them securely! If you don't,
    you could lose access to your provider's API!

User Management
---------------

The most well-known use for OAuth is for bypassing user registration:
users can "sign in" with a well-known OAuth provider like Google or Facebook
in order to avoid creating another username and password. However, this is
not the *only* use for OAuth. In fact, it's entirely possible to use
OAuth without even having a user management system on your website at all!

For example, let's say you want to create a Twitter account that is completely
public. Anyone in the world should be able to post a tweet, without any
identifying information attached to it. You build a simple website that has
a text field and a "submit" button, but no user management system at all.
Whenever anyone submits a tweet to your website, it uses the Twitter API
to post that tweet to your Twitter account -- which requires using OAuth.

Flask-Dance does *not* assume that your website has a user management system.
It's easy to use Flask-Dance with a user management system if you want to,
though! Read the documentation on :doc:`multi-user` if you plan to use a
user management system.

Local Accounts vs Provider Accounts
-----------------------------------

It's a common misconception that, because a user can log in to your website
using OAuth instead of creating a new username/password combination,
that means they do not have a user account on your website. This is false.
Logging in with OAuth *does create a local user account*, and that user account
will have some kind of identifier (or ``user_id``). The ``user_id`` on this
local account does *not* have to match that user's ID on Google,
or Facebook, or Twitter, or whatever OAuth provider(s) you choose to use.

The distinction between a local account and a provider account is especially
important when :doc:`implementing logout <logout>`.

Blueprints
----------

A :ref:`Flask blueprint <flask:blueprints>` is component of a
Flask application. Because Flask-Dance is designed to be the OAuth component
of your Flask application, it is built using blueprints. As a result,
Flask-Dance supports all the features that any blueprint supports,
including registering the blueprint at any URL prefix or subdomain
you want, url routing, and custom error handlers. Read the
:ref:`Flask documentation about blueprints <flask:blueprints>`
for more information.

Signals
-------

Flask uses the `blinker`_ library to provide support for
:ref:`signals <flask:signals>`. Signals allow you to subscribe to certain
events that occur in your application, so that you can respond instantly
when those events happen.

Signals are an important part of Flask-Dance, because they allow you to
do whatever custom processing you want in response to certain events.
For example, when a user successfully completes the OAuth dance, you probably
want to flash a welcome message or kick off some kind of data import task.
Signals allow you to do that without modifying the code in Flask-Dance.
Read the :ref:`signals page <signals>` for more information.

.. _blinker: https://pythonhosted.org/blinker/

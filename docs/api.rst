Developer Interface
===================

Consumers
---------

.. currentmodule:: flask_dance.consumer

An OAuth consumer is a website that allows users to log in with other websites
(known as OAuth providers). Once a user has gone through the OAuth dance, the
consumer website is allowed to interact with the provider website on behalf
of the user.

.. autoclass:: OAuth1ConsumerBlueprint(...)

   .. automethod:: __init__

   .. attribute:: session

      An :class:`~requests_oauthlib.OAuth1Session` instance that
      automatically loads tokens for the OAuth provider from the token storage.
      This instance is automatically created the first time it is referenced
      for each request to your Flask application.

   .. autoattribute:: storage

   .. autoattribute:: token

   .. attribute:: config

      A special dictionary that holds information about the current state of
      the application, which the token storage can use to look up the correct OAuth
      token from storage. For example, in a multi-user system, where each user
      has their own OAuth token, information about which user is currently logged
      in for this request is stored in this dictionary. This dictionary is special
      because it automatically alerts the storage when any attribute in the
      dictionary is changed, so that the storage's caches are appropriately
      invalidated.

   .. attribute:: from_config

      A dictionary used to dynamically load variables from the
      :ref:`Flask application config <flask:config>` into the blueprint
      at the start of each request. To tell this blueprint to pull configuration
      from the app, set key-value pairs on this dict. Keys are the name of
      the local variable to set on the blueprint object, and values are the
      variable name in the Flask application config.
      Variable names can be a dotpath. For example::

         blueprint.from_config["session.client_id"] = "GITHUB_OAUTH_CLIENT_ID"

      Which will cause this line to execute at the start of every request::

         blueprint.session.client_id = app.config["GITHUB_OAUTH_CLIENT_ID"]

.. autoclass:: OAuth2ConsumerBlueprint(...)

   .. automethod:: __init__

   .. attribute:: session

      An :class:`~requests_oauthlib.OAuth2Session` instance that
      automatically loads tokens for the OAuth provider from the storage.
      This instance is automatically created the first time it is referenced
      for each request to your Flask application.

   .. autoattribute:: storage

   .. autoattribute:: token

   .. attribute:: config

      A special dictionary that holds information about the current state of
      the application, which the token storage can use to look up the correct OAuth
      token from storage. For example, in a multi-user system, where each user
      has their own OAuth token, information about which user is currently logged
      in for this request is stored in this dictionary. This dictionary is special
      because it automatically alerts the storage when any attribute in the
      dictionary is changed, so that the storage's caches are appropriately
      invalidated.

   .. attribute:: from_config

      A dictionary used to dynamically load variables from the
      :ref:`Flask application config <flask:config>` into the blueprint
      at the start of each request. To tell this blueprint to pull configuration
      from the app, set key-value pairs on this dict. Keys are the name of
      the local variable to set on the blueprint object, and values are the
      variable name in the Flask application config.
      Variable names can be a dotpath. For example::

         blueprint.from_config["session.client_id"] = "GITHUB_OAUTH_CLIENT_ID"

      Which will cause this line to execute at the start of every request::

         blueprint.session.client_id = app.config["GITHUB_OAUTH_CLIENT_ID"]

Storages
--------

.. autoclass:: flask_dance.consumer.storage.session.SessionStorage(...)
   :members:
   :special-members:


.. autoclass:: flask_dance.consumer.storage.sqla.SQLAlchemyStorage(...)
   :members:
   :special-members:

Sessions
--------

.. autoclass:: flask_dance.consumer.requests.OAuth1Session
   :members: token, authorized, authorization_required

.. autoclass:: flask_dance.consumer.requests.OAuth2Session
   :members: token, access_token, authorized, authorization_required

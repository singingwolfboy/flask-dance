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
      automatically loads tokens for the OAuth provider from the backend.
      This instance is automatically created the first time it is referenced
      for each request to your Flask application.

   .. attribute:: backend

      The :doc:`token storage backend <backends>` that this blueprint
      uses.

   .. attribute:: token

      The OAuth token currently loaded in the :attr:`session` attribute.

   .. attribute:: config

      A special dictionary that holds information about the current state of
      the application, which the backend can use to look up the correct OAuth
      token from storage. For example, in a multi-user system, where each user
      has their own OAuth token, information about which user is currently logged
      in for this request is stored in this dictionary. This dictionary is special
      because it automatically alerts the backend when any attribute in the
      dictionary is changed, so that the backend's caches are appropriately
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
      automatically loads tokens for the OAuth provider from the backend.
      This instance is automatically created the first time it is referenced
      for each request to your Flask application.

   .. attribute:: backend

      The :doc:`token storage backend <backends>` that this blueprint
      uses.

   .. attribute:: token

      The OAuth token currently loaded in the :attr:`session` attribute.

   .. attribute:: config

      A special dictionary that holds information about the current state of
      the application, which the backend can use to look up the correct OAuth
      token from storage. For example, in a multi-user system, where each user
      has their own OAuth token, information about which user is currently logged
      in for this request is stored in this dictionary. This dictionary is special
      because it automatically alerts the backend when any attribute in the
      dictionary is changed, so that the backend's caches are appropriately
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

Backends
--------

.. autoclass:: flask_dance.consumer.backend.session.SessionBackend(...)
   :members:
   :special-members:


.. autoclass:: flask_dance.consumer.backend.sqla.SQLAlchemyBackend(...)
   :members:
   :special-members:


API
===

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
      automatically loads credentials for the OAuth provider (if the user has
      already gone through the OAuth dance).

   .. attribute:: token_storage

      The :doc:`token storage backend <token-storage>` that this blueprint
      uses.

   .. attribute:: token

      A dynamic reference to the stored OAuth token.

.. autoclass:: OAuth2ConsumerBlueprint(...)

   .. automethod:: __init__

   .. attribute:: session

      An :class:`~requests_oauthlib.OAuth2Session` instance that
      automatically loads credentials for the OAuth provider (if the user has
      already gone through the OAuth dance).

   .. attribute:: token_storage

      The :doc:`token storage backend <token-storage>` that this blueprint
      uses.

   .. attribute:: token

      A dynamic reference to the stored OAuth token.

Storage Backends
----------------

.. autoclass:: flask_dance.consumer.storage.session.SessionStorage(...)
   :members:
   :special-members:


.. autoclass:: flask_dance.consumer.storage.sqla.SQLAlchemyStorage(...)
   :members:
   :special-members:


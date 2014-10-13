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

   .. automethod:: token_getter
   .. automethod:: token_setter
   .. automethod:: token_deleter
   .. autoattribute:: token

   .. automethod:: set_token_storage_session
   .. automethod:: set_token_storage_sqlalchemy

.. autoclass:: OAuth2ConsumerBlueprint(...)

   .. automethod:: __init__

   .. attribute:: session

      An :class:`~requests_oauthlib.OAuth2Session` instance that
      automatically loads credentials for the OAuth provider (if the user has
      already gone through the OAuth dance).

   .. automethod:: token_getter
   .. automethod:: token_setter
   .. automethod:: token_deleter
   .. autoattribute:: token

   .. automethod:: set_token_storage_session
   .. automethod:: set_token_storage_sqlalchemy

Models
------

.. currentmodule:: flask_dance.models

.. autoclass:: OAuthConsumerMixin

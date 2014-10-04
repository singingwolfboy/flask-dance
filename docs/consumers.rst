Consumers
=========
An OAuth consumer is a website that allows users to log in with other websites
(known as OAuth providers). Once a user has gone through the OAuth dance, the
consumer website is allowed to interact with the provider website on behalf
of the user.

.. autoclass:: flask_dance.consumer.OAuth1ConsumerBlueprint(...)

   .. automethod:: flask_dance.consumer.OAuth1ConsumerBlueprint.__init__

   .. attribute:: session

      An :class:`~requests_oauthlib.OAuth1Session` instance that
      automatically loads credentials for the OAuth provider (if the user has
      already gone through the OAuth dance).

   .. automethod:: flask_dance.consumer.OAuth1ConsumerBlueprint.token_getter
   .. automethod:: flask_dance.consumer.OAuth1ConsumerBlueprint.token_setter
   .. automethod:: flask_dance.consumer.OAuth1ConsumerBlueprint.token_deleter
   .. autoattribute:: flask_dance.consumer.OAuth1ConsumerBlueprint.token

   .. automethod:: flask_dance.consumer.OAuth1ConsumerBlueprint.logged_in

.. autoclass:: flask_dance.consumer.OAuth2ConsumerBlueprint(...)

   .. automethod:: flask_dance.consumer.OAuth2ConsumerBlueprint.__init__

   .. attribute:: session

      An :class:`~requests_oauthlib.OAuth2Session` instance that
      automatically loads credentials for the OAuth provider (if the user has
      already gone through the OAuth dance).

   .. automethod:: flask_dance.consumer.OAuth2ConsumerBlueprint.token_getter
   .. automethod:: flask_dance.consumer.OAuth2ConsumerBlueprint.token_setter
   .. automethod:: flask_dance.consumer.OAuth2ConsumerBlueprint.token_deleter
   .. autoattribute:: flask_dance.consumer.OAuth2ConsumerBlueprint.token

   .. automethod:: flask_dance.consumer.OAuth2ConsumerBlueprint.logged_in

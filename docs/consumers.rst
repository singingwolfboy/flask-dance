Consumers
=========
An OAuth consumer is a website that allows users to log in with other websites
(known as OAuth providers). Once a user has gone through the OAuth dance, the
consumer website is allowed to interact with the provider website on behalf
of the user.

.. autoclass:: flask_dance.consumer.OAuth1ConsumerBlueprint
.. autoclass:: flask_dance.consumer.OAuth2ConsumerBlueprint
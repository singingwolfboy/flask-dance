How OAuth Works
===============

OAuth uses a series of specially-crafted HTTP views and redirects to allow
websites to share information with each other securely, and with the user's
consent [#oauth-user]_. There are four roles in an OAuth interaction:

provider
    A website that has information about a user. Well-known OAuth providers
    include Google, Facebook, Twitter, etc.
consumer
    A website that wants to obtain some information about a user from the
    provider.
user
    An actual person who controls information stored with the provider.
client
    A program (usually a web browser) that interacts with the provider and
    consumer on behalf of the user.

In order to securely interact with each other, the provider and consumer must
exchange secrets ahead of time, before any OAuth communication actually happens.
Generally, this happens when someone who runs the consumer website goes to the
provider website and registers an application with the provider, putting
in information about the name and URL of the consumer website. The provider
then gives the consumer a "client secret", which is a random string of letters
and numbers. By presenting this client secret in future OAuth communication,
the provider website can verify that the consumer is who they say they are,
and not some other website trying to intercept the communication.

.. note::
   Even though it is called a "client secret", the secret represents the
   consumer website, not the client (the user's web browser).

After the consumer has registered an application with the provider and gotten
a client secret, the consumer can do the "OAuth dance" to get consent from a
user to share information with the consumer. The dance has five steps:

.. aafig::
   :proportional:

   +---------+             +-----------+               +----------+
   |  Client |             |  Consumer |               | Provider |
   +----+----+             +-----+-----+               +----+-----+
        | start dance            |                          |
        |----------------------->| send secret & state      |
        |                        |------------------------->|
        | redirect, with         | send authorization grant |
        | authorization grant    |<-------------------------|
        |<-----------------------|                          |
        | "follow redirect"      |                          |
        |-------------------------------------------------->| user
        |         redirect, with authorization code & state | grants
        |<--------------------------------------------------| consent
        | "follow redirect"      |                          |
        |----------------------->| send secret & auth code  |
        |                        |------------------------->|
        |                        | "send access token"      |
        |                        |<-------------------------|

1. The consumer tells the provider that they're about to do the OAuth dance.
   The consumer gives the provider the client secret, to verify that everything's
   cool. The consumer also makes up a new secret, called the "state",
   and passes that to the provider. The provider checks the OAuth secret, and
   if it looks good, the provider makes up a new secret called an
   "authorization grant", and gives it to the consumer.

2. The consumer crafts a special URL that points to the provider, but has the
   authorization grant embedded in the URL. The consumer asks the client
   to go visit that URL.

3. When the client visits the provider at that URL, the provider notices the
   authorization grant, and looks up the consumer that it belongs to.
   The provider tells the user that this consumer wants to access some or all
   of the user's information. The user gets to decide if this is OK or not.
   If the user decides that this is not OK, the dance is over.

4. If the user grants consent, the provider makes up another new secret, called
   the "authorization code". The provider crafts a special URL that points to
   the consumer, which has two secrets embedded in it: the authorization code
   (that the provider made up) and the state (that the consumer made up).
   The provider asks the client to go visit that URL.

5. When the client visits the consumer at that URL, the consumer notices the
   two secrets in the URL. As a security measure, the consumer checks the
   state secret, to be sure it matches what the consumer said it should be.
   The consumer then sends the authorization code and the client secret back
   to the provider. If everything looks good to the provider, the provider
   makes up one final secret, called the "access token", and sends it back
   to the consumer. This completes the dance.

Phew, that was complicated! But the end result is, the consumer has an access
token, which proves that the user has given consent for the provider to give
the consumer information about that user. Now, whenever the consumer needs
information from the provider about the user, the consumer simply makes an
API request to the provider and passes the access token along with the request.
The provider sees the access token, looks up the user that granted consent,
and determines whether the requested information falls within what the user
authorized. If so, the provider returns that information to the consumer.
In effect, the consumer is now the user's client!

.. warning::
    Keep your access tokens secure! Treat a user's access token like you would
    treat their password.

.. note::
    The OAuth dance normally only needs to be performed once per user.
    Once the consumer has an access token, that access token can be used
    to make many API requests on behalf of the user. Some OAuth
    implementations put a lifespan on the access token, after which it must
    be refreshed, but refreshing an access token does not require any
    interaction from the user.

.. [#oauth-user] Not all OAuth interactions share information about specific
    users. When no user-specific information is involved, then the consumer
    is able to get information from the provider without getting a user's
    consent, since there is no one to get consent from. In practice, however,
    most OAuth interactions are about sharing information about users, so this
    documentation assumes that use-case.

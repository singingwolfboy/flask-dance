How OAuth Works
===============

Definitions
-----------

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
user to share information with the consumer. There are two different versions
of the dance: OAuth 1, which is the original version; and OAuth 2, the successor
to OAuth 1 which is more flexible and more widely used today.

OAuth 2
-------

.. seqdiag::

    seqdiag {
        Client -> Consumer [label = "start dance"];
        Client <- Consumer [label = "redirect to provider,\nwith secret, scopes, & state"];
        Client -> Provider [label = "follow redirect", rightnote="user\ngrants\n consent"];
        Client <- Provider [label = "redirect to consumer, with authorization code and state"];
        Client -> Consumer [label = "follow redirect"];
        Consumer --> Provider [label = "send secret and\nauthorization code"];
        Consumer <-- Provider [label = "return access token"];
        Client <-- Consumer [label = "render page or redirect"];
    }

1.  The client visits the consumer at a special URL, indicating that they
    want to connect to the provider with OAuth. Typically, there is a button
    on the consumer's website labelled "Log In with Google" or similar, which
    takes the user to this special URL.

2.  The consumer decides how much of the user's data they want to access,
    using specfic keywords called "scopes". The consumer also makes up a random
    string of letters and numbers, called a "state" token. The consumer crafts
    a special URL that points to the provider, but has the client secret,
    the scopes, the state token embedded in it. The consumer asks the client
    to visit the provider using this special URL.

3.  When the client visits the provider at that URL, the provider notices the
    client secret, and looks up the consumer that it belongs to.
    The provider also notices the scopes that the consumer is requesting.
    The provider displays a page informing the user what information the
    consumer wants access to -- it may be all of the user's information, or
    just some of the user's information. The user gets to decide if this is
    OK or not. If the user decides that this is not OK, the dance is over.

4.  If the user grants consent, the provider makes up a new secret, called
    the "authorization code". The provider crafts a special URL that points to
    the consumer, but has the authorization code and the state token
    embedded in it. The provider asks the client to visit the consumer
    using this special URL.

5.  When the client visits the consumer at that URL, the consumer first checks
    the state token to be sure that it hasn't changed, just to verify that
    no one has tampered with the request. Then, the consumer makes a separate
    request to the provider, passing along the client secret and the
    authorization code. If everything looks good to the provider, the provider
    makes up one final secret, called the "access token", and sends it back
    to the consumer. This completes the dance.

OAuth 1
-------

.. seqdiag::

    seqdiag {
        Client -> Consumer [label = "start dance"];
        Consumer --> Provider [label = "send client secret"];
        Consumer <-- Provider [label = "return request token"];
        Client <- Consumer [label = "redirect, with request token"];
        Client -> Provider [label = "follow redirect", rightnote="user\ngrants\nconsent"];
        Client <- Provider [label = "redirect, with authorization code"];
        Client -> Consumer [label = "follow redirect"];
        Consumer --> Provider [label = "send client secret\n& authorization code"];
        Consumer <-- Provider [label = "return access token"];
        Client <-- Consumer [label = "render page or redirect"];
    }

1.  The client visits the consumer at a special URL, indicating that they
    want to connect to the provider with OAuth. Typically, there is a button
    on the consumer's website labelled "Log In with Twitter" or similar, which
    takes the user to this special URL.

1.  The consumer tells the provider that they're about to do the OAuth dance.
    The consumer gives the provider the client secret, to verify that
    everything's cool. The provider checks the OAuth secret, and if it
    looks good, the provider makes up a new secret called a
    "request token", and gives it to the consumer.

2.  The consumer crafts a special URL that points to the provider, but has the
    client secret and request token embedded in it. The consumer asks the client
    to visit the provider using this special URL.

3.  When the client visits the provider at that URL, the provider notices the
    request token, and looks up the consumer that it belongs to.
    The provider tells the user that this consumer wants to access some or all
    of the user's information. The user gets to decide if this is OK or not.
    If the user decides that this is not OK, the dance is over.

4.  If the user grants consent, the provider makes up another new secret, called
    the "authorization code". The provider crafts a special URL that points to
    the consumer, but has the authorization code embedded in it.
    The provider asks the client to go visit the consumer at that special URL.

5.  When the client visits the consumer at that URL, the consumer notices the
    authorization code. The consumer makes another request to the provider,
    passing along the client secret and the authorization code.
    If everything looks good to the provider, the provider makes up one
    final secret, called the "access token", and sends it back to the consumer.
    This completes the dance.

Dance Complete
--------------

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

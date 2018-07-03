Testing
=======

When building Flask apps that have integrated Flask-Dance you'll eventually run
into the need to test your app. But if routes are guarded by the requirement of
having a valid OAuth2 session, i.e getting past the ``.authorized()`` call on
a provider, how do you test this?

One possible way of solving this is by injecting the necessary information into
the Flask session. The following examples assume you're using `py.test`_ and the
Google provider, but the same trick applies to any of the supported providers.

Creating a session
------------------

In your ``conftest.py`` create two fixtures, like this:

.. code-block:: python

    import time

    import pytest

    from your_app import create_app
    from your_app.settings import Testing

    fake_time = time.time()


    @pytest.fixture
    def app():
        """Returns an app fixture with the testing configuration."""
        app = create_app(config_object=Testing)
        yield app


    @pytest.fixture
    def loggedin_app(app):
        """Creates a logged-in test client instance."""
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['google_oauth_token'] = {
                    'access_token': 'this is totally fake',
                    'id_token': 'this is not a real token',
                    'token_type': 'Bearer',
                    'expires_in': '3600',
                    'expires_at': fake_time + 3600,
                }
            yield client
    
This will inject the necessary information in order to ensure that Flask-Dance,
requests-oauthlib and oauthlib believe there is a valid session, and one that
won't need to be refreshed for another hour (3600 seconds). If your tests run
longer than that, you'll need to adjust that value.

The ``fake_time`` is created so that you can always refer to the same point in
time throughout tests, and in any other fixture you might create. Alternatively
you can use something like `pytest-freezegun`_ and then call any of the ``time``
and ``datetime`` functions as you normally would:

.. code-block:: python

    @pytest.fixture
    @pytest.mark.freeze_time('2018-05-04')
    def loggedin_app(app):
        """Creates a logged-in test client instance."""
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['domain'] = 'example.com'
                sess['google_oauth_token'] = {
                    'access_token': 'this is totally fake',
                    'id_token': 'this is not a real token',
                    'token_type': 'Bearer',
                    'expires_in': '3600',
                    'expires_at': time.time() + 3600,
                }
            yield client

Now that we have a logged-in client you can call any of the routes using the
test client and check their responses.

.. code-block:: python

    def test_not_logged_in(app):
        """Test that we redirect to Google to login."""
        res = app.test_client().get('/')
        assert ('redirected automatically to target URL: <a href="/login/'
                'google">/login/google</a>').lower() in res.get_data(as_text=True).lower()
        assert res.status_code == 302


    def test_logged_in_index(loggedin_app):
        """Tests getting the index route.

        This will render the normal template as we have a valid oauth2 session.
        """
        res = loggedin_app.get('/')
        assert res.content_type == 'text/html; charset=utf-8'
        assert res.status_code == 200
        assert 'something only shown when logged in' in res.get_data(as_text=True).lower()


Calling authenticated APIs
--------------------------

Though we've managed to create a working session a problem now arises if you
try to actually call an API, by using ``google.get('some url')`` for example.
Your token will fail to validate and the request will be denied.

This can be handled by a Python library called `responses`_, which lets us control
the full HTTP request cycle.

.. warning::
    Note that this means we're essentially mocking the API we're calling, so
    your tests will continue passing even if the real API has changed behaviour.

Let's assume the index route calls out to the `Google Plus API`_ and displays some
profile information. Here's how you could handle that.

.. code-block:: python

    import pytest
    import responses


    @responses.activate
    def test_getting_profile(loggedin_app):
        """Test displaying profile information."""
        responses.add(
            responses.GET,
            'https://www.googleapis.com/plus/v1/people/me',
            status=200,
            json={
              'kind': 'plus#person',
              'id': '118051310819094153327',
              'displayName': 'Chirag Shah',
              'url': 'https://plus.google.com/118051310819094153327',
              'image': {
                'url': 'https://lh5.googleusercontent.com/-XnZDEoiF09Y/AAAAAAAAAAI/AAAAAAAAYCI/7fow4a2UTMU/photo.jpg'
              }
            })
        res = loggedin_app.get('/')
        assert len(responses.calls) == 1
        assert res.status_code == 200
        assert res.content_type == 'text/html; charset=utf-8'
        assert 'some profile information we fetched' in res.get_data(as_text=True).lower()


Responses can do a lot more for you, but you'll have to refer to its
documentation instead.

.. _`py.test`: https://docs.pytest.org/
.. _`pytest-freezegun`: https://github.com/ktosiek/pytest-freezegun
.. _`responses`: https://github.com/getsentry/responses
.. _`Google Plus API`: https://developers.google.com/+/web/api/rest/

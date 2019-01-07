Twitter Frontend Quickstart
===========================

Prerequisite
------------
Please see the `twitter <twitter.rst>` document before
reading this implementation. You are familiar with
frontend libraries like React, Angular, or VueJS and have worked
with components, webpack, and other JS libaries like axios.

Set up the application
----------------------
In this demo, I have used 127.0.0.1 instead of localhost after
I experienced the issue in this `tech note <https://twittercommunity.com/t/why-cant-i-use-localhost-as-my-oauth-callback/708>`_.


Github Demo
-----------
You can find the complete source for this demo in this `flask-dance-twitter-frontend <https://github.com/headwinds/flask-dance-twitter-frontend>`_ github.
Please note that this demo does not yet include the
`sql backend <slqa-multiuser.rst>` that hangs onto the token
after the flask session has expired.

Code
----
Once your project has compiled, please view visit ``http://127.0.0.1:5000`` in your browser.
Then, you can click on the Signin with Twitter hyperlink.

In your signin view, make sure you use a hyperlink or button that
will redirect the user to a confirmation webpage that Twitter provides.

.. code-block:: HTML

    <a href="/api/twitter/aut">Sign in with Twitter</a>

You can only use RESTFUL libraries like axios to get the
authentication status.

For instance, when the component mounts, you could call a function to check
the authentication status against Twitter's API.

If the authentication fails, then you can display a hyperlink for
the user to begin the dance, or if it succeeds, then simply
display the authenticated username.

The following example uses axios and vuejs but this could be ported to
react, angular, or vanila javascript. You could create 3 state variables:
welcome (String ""), authenticated (Boolean false),
authenticateCheckComplete (Boolean false), and then use these to
either show the hyperlink or the authenticated username.

.. code-block:: javascript

    function checkAuthentication(){
        const self = this;

        const url = (document.domain === "127.0.0.1")
            ? 'http://127.0.0.1:5000/twitter/auth' : 'https://your-production-domain/twitter/auth'

        axios.get(url).then(
            response => {
                if (response.data.screen_name) {
                    self.welcome = "welcome " + response.data.screen_name;
                    self.authenticated = true;
                }
            }
        ).catch(error => {
            this.errored = error
        }).finally(() => self.authenticateCheckComplete = true);

    }
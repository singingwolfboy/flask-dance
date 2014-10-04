Login Callbacks
===============
You probably have some custom processing code that you want to run when a user
logs in. You might need to update their user profile, fire an event, or
simply :ref:`flash a message <flask:message-flashing-pattern>`
to let them know they've logged in. It's easy, just use the
:meth:`~OAuth2ConsumerBlueprint.logged_in` decorator
on the blueprint to ensure the function is called at the right time::

    @github_blueprint.logged_in
    def github_logged_in(token):
        if "error" in token:
            flash("You denied the request to sign in. Please try again.")
            del github_blueprint.token
        else:
            flash("Signed in successfully!")

The function is passed a dict containing whatever OAuth token information is
returned from the OAuth provider. Remember that errors can happen, so it's worth
checking for them! If you're using OAuth 2, the user may also grant you
different scopes than the ones you requested, so you should verify that, as well.
By the time this function is called, the token will already be saved (either
into the Flask session by default, or using your custom ``token_setter`` function)
so if you want to delete the saved token, you can just delete the ``token``
property from the blueprint. That will call your ``token_deleter`` function,
or remove it from the Flask session if you haven't defined a ``token_deleter``
function.

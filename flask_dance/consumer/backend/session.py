from flask_dance.consumer.backend import BaseBackend
import flask


class SessionBackend(BaseBackend):
    """
    The default storage backend. Stores and retrieves OAuth tokens using
    the :ref:`Flask session <flask:sessions>`.
    """
    def __init__(self, key="{bp.name}_oauth_token"):
        """
        Args:
            key (str): The name to use as a key for storing the OAuth token in the
                Flask session. This string will have ``.format(bp=self.blueprint)``
                called on it before it is used. so you can refer to information
                on the blueprint as part of the key. For example, ``{bp.name}``
                will be replaced with the name of the blueprint.
        """
        self.key = key

    def get(self, blueprint):
        key = self.key.format(bp=blueprint)
        return flask.session.get(key)

    def set(self, blueprint, token):
        key = self.key.format(bp=blueprint)
        flask.session[key] = token

    def delete(self, blueprint):
        key = self.key.format(bp=blueprint)
        del flask.session[key]

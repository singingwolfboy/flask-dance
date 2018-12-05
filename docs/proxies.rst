Proxies and HTTPS
=================

Running a secure HTTPS website is important, but encrypting and decrypting
HTTPS traffic is computationally expensive. Many people running large-scale
websites (including `Heroku`_) use a `TLS termination proxy`_ to reduce load
on the HTTP server. This works great, but means that the webserver running
your Flask application is actually speaking HTTP, not HTTPS.

As a result, Flask-Dance can get confused, and generate callback URLs
that have an ``http://`` scheme, instead of an ``https://`` scheme.
This is bad, because OAuth requires that all connections use HTTPS for
security purposes, and OAuth providers will reject requests that suggest
a callback URL with a ``http://`` scheme.

When you proxy the request from a `TLS termination proxy`_, probably your
load balancer, you need to ensure a few headers are set/proxied correctly
for Flask to do the right thing out of the box:

* ``Host``: preserve the Host header of the original request
* ``X-Real-IP``: preserve the source IP of the original request
* ``X-Forwarded-For``: a list of IP addresses of the source IP and any
  HTTP proxies we've been through
* ``X-Forwarded-Proto``: the protocol, http or https, that the request
  came in with

In 99.9% of the cases the `TLS termination proxy`_ will be configured to
do the right thing by default and any well-behaved Flask application will
work out of the box. However, if you're accessing the WSGI environment
directly, you will run into trouble. Don't do this and instead use the
functions provided by Werkzeug's :mod:`~werkzeug.wsgi` module or Flask's
:attr:`~flask.request` to access things like a ``Host`` header.

If your Flask app is behind a TLS termination proxy, and you need to make
sure that Flask is aware of that, check Flask's documentation for
:ref:`how to deploy a proxy setup <flask:deploying-proxy-setups>`.

Please read it and follow its instructions. This is not unique to
Flask-Dance and there's nothing to configure on Flask-Dance's side
to solve this. It's also worth noting you might wish to set Flask's
:data:`PREFERRED_URL_SCHEME`.

.. _TLS termination proxy: https://en.wikipedia.org/wiki/TLS_termination_proxy
.. _Heroku: https://www.heroku.com/

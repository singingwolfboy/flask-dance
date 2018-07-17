Installation
============

Use `pip`_ to install Flask-Dance. To use basic functionality, run this:

.. code-block:: bash

    $ pip install Flask-Dance

To also use the :ref:`SQLAlchemy backend <sqlalchemy-backend>`, specify the
``sqla`` extra, like this:

.. code-block:: bash

    $ pip install Flask-Dance[sqla]

.. _pip: https://pip.pypa.io

Library development
============

Use `tox`_ to execute unit tests on multiple python versions.
To build the documentation, it requires the `flask-dance` theme (using git `submodule`).


.. code-block:: bash

   $ git submodule update
   $ tox


.. _tox: https://tox.readthedocs.io/

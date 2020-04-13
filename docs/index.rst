.. NGINXRAY documentation master file, created by
   sphinx-quickstart on Mon Apr  6 12:56:02 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to NGINXRAY's documentation!
====================================

.. toctree::
   :maxdepth: 2

Service Doubles Configuration
-----------------------------

You can define a suite of fake services that will accept traffic and act like
they do in the real world, minus the actual internal operations. They accept
requests and behave as expected. Here is an example of a configuration:

.. literalinclude:: ../pub_config.yml
   :language: yaml


This configuration defines a list of services, containing `publisher` and one
of its routes. You can provide a list of services and a list of routes, even
though there is only one here currently.

NGINXRAY reads in this configuration and dynamically configures services to be
run locally which will behave as configured above.

.. toctree::
   
   internal_components

NGINXRAY can be invoked as follows
----------------------------------
.. NOTE::
  There is currently not a great build/distribution system so you will have to
  clone the repo, make a virtual env, and install requirements. 


::

  $ python nginxray.py config.yml


You can pass in any config you like. You can specify nginx.conf files from
where ever you like.::

   $ python nginxray.py config.yml --nginx-conf ~/my/nginx/conf

The `--nginx-conf` option takes a directory and configures the nginx routing
using whatever is inside.

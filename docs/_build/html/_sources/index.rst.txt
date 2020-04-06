.. NGINXRAY documentation master file, created by
   sphinx-quickstart on Mon Apr  6 12:56:02 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to NGINXRAY's documentation!
====================================

.. toctree::
   :maxdepth: 2

Service Fake Configuration
--------------------------

You can define a suite of fake services that will accept traffic and act like they do in
the real world, minus the actual internal operations. They accept requests and behave as
expected. Here is an example of a configuration:

.. code-block:: yaml

   services:
     publisher:
       routes:
         - name: prophet_xml_import
           route: "/api/v1/playlists/prophet_xml_import/<stream>/"
           method: "GET"
           params:
             - xml_contents
         - name: david_xml_import
           route: "/api/v1/playlists/david_xml_import/<stream>/"
           method: "POST"
           params:
             - password
     whatson:
       routes:
         - name: whats_on_prophet
           route: "/whats-on/v1/update"
           method: "GET"
           params:
             - xml_contents
             - stream
         - route: "/whats-on/v1/update"
           method: "POST"
           params:
             - stream

This configuration defines two services, `publisher` and `whatson`, that each have two
routes.

NGINXRAY reads in this configuration and dynamically configures services to be run locally
and that will behave as configured above.

.. toctree::
   
   service_configuration


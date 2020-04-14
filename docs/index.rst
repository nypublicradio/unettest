.. NGINXRAY documentation master file, created by
   sphinx-quickstart on Mon Apr  6 12:56:02 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to NGINXRAY's documentation!
====================================

.. toctree::
   :maxdepth: 2

   config_document

   internal_components


NGINXRAY [NXR] is a test harness for your NGINX server configurations. 
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Have you spent hours twiddling with an NGINX.conf only to have it act totally
nuts?? Are you irritated by the slow process of making a tweak, deploying,
realizing there's a typo, deploying again etc etc etc ? I am!! There are only so
many times you can go get a "Deploying!" coffee in one day. And I wasn't
satisfied with running NGINX on my computer! What a pain that is. So I decided
to box NGINX up in a Docker container. And I figured that now that NGINX is in
Docker, why not ALL my services! I could poke at them and see how they act. Like
a software circus on my own laptop. And I wouldn't have to flip between 800
terminal tabs!

And so is born NGINXRAY. You can tell NXR how the world works and then hand her a
nginx.conf and see how everything works just like you would expect! Or exactly how you
wouldn't!



NGINXRAY can be invoked as follows
----------------------------------
.. NOTE::
  There is currently not a great build/distribution system so you will have to
  clone the `repo <https://github.com/nypublicradio/nginxray>`_, make a virtual env, and install requirements. You need Docker
  and docker-compose. **@ me on slack if you have questions or want a
  walkthrough!!**


::

  $ python nginxray.py config.yml

.. NOTE::
  Use ``python nginxray.py --help``\ .


You can pass in any config you like. You can specify nginx.conf files from
anywhere you like. ::

   $ python nginxray.py config.yml --nginx-conf ~/my/nginx/conf

The `--nginx-conf` option takes a directory and configures the NGINX routing
using whatever is inside.

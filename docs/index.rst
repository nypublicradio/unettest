.. NGINXRAY documentation master file, created by
   sphinx-quickstart on Mon Apr  6 12:56:02 2020.

Welcome to NGINXRAY's documentation!
====================================

.. toctree::
   :maxdepth: 2

   config_document

   internal_components

   tutorial


NGINXRAY [NXR], a network repl
++++++++++++++++++++++++++++++

Now that we have all these little microservices, isn't it a little annoying that we have
to pay attention to all the weird ways they talk to each other, crisscrossing back and
forth? And isn't it aggravating that they are not checked by unit tests?

Have you spent hours twiddling with an NGINX.conf only to have it act totally nuts?? Are
you irritated by the slow process of making a tweak, deploying, realizing there's a typo,
deploying again etc etc etc ? I am!! There are only so many times you can go get a
"Deploying!" coffee in one day and I am tired of abusing our nonproduction environments. 

I tried running NGINX on my computer but that was fragile and agitating. It wasn't good
enough--too painful!  So I decided to box up NGINX in a Docker container. And I figured
that now that NGINX is in Docker, why not ALL of my services! I could poke at them and see
how they act. Like a software circus on my own laptop. And I wouldn't have to flip between
800 terminal tabs!

And so is born NGINXRAY. You can tell NXR how the world works and then hand her a
nginx.conf and see how everything works just like you would expect! Or exactly how you
wouldn't!

NGINXRAY lets you design a repl on your laptop for things running on the internet and the
APIs that connect them.



NGINXRAY can be invoked as follows
----------------------------------
**@ me on slack if you have questions or want a walkthrough!!**

Requirements:


* Docker
* docker-compose
* `NGINXRAY for MacOS <https://nginxray.s3.us-east-2.amazonaws.com/nginxray.mac>`_
  (`SHA-256 checksum <https://nginxray.s3.us-east-2.amazonaws.com/mac-sha256>`_)



::

  $ nginxray config.yml

.. NOTE::
  Use ``python nginxray.py --help``\ .


You can pass in an :doc:`config_document`. You can specify nginx.conf files from
anywhere you like. ::

   $ python nginxray.py config.yml --nginx-conf ~/my/nginx/conf

The `--nginx-conf` option takes a directory and configures the NGINX routing
using whatever is inside.

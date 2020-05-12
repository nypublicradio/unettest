.. UNETTEST documentation master file, created by
   sphinx-quickstart on Mon Apr  6 12:56:02 2020.

This is ``unettest``\ 
=====================

``if u got a network, u net test``
++++++++++++++++++++++++++++++++++

.. toctree::
   :maxdepth: 2

   config_document

   nginx_files

   internal_components

   tutorial


``unettest``, a network mocker, repl, and test harness
++++++++++++++++++++++++++++++++++++++++++++++++++++++

Your code is unit tested. Is your network? Why not? Get some tests.

Now that we live in a microservice world, isn't it a little annoying keeping
track of all the weird ways they talk to each other, crisscrossing back and
forth? And isn't it aggravating that those connections are not checked by unit
tests?

Have you spent hours twiddling with an NGINX.conf only to have it act totally
nuts?? Are you irritated by the slow process of making a tweak, deploying,
realizing there's a typo, deploying again etc etc etc ? I am!! There are only
so many times you can go get a "Deploying!" coffee in one day and I am tired of
abusing our nonproduction environments. 

I tried running NGINX on my computer but that was fragile and agitating. It
wasn't good enough--too painful!  So I boxed up NGINX in a Docker container.
And I figured that now that NGINX is in Docker, why not ALL of my services! I
could poke at them and see how they act like a software circus on my laptop.
And I wouldn't have to flip between 800 terminal tabs!

And so is born ``unettest``. You can tell ``unettest`` how the world works and
then hand her an nginx.conf and see how things work like you expect! Or how you
don't!

``unettest`` lets you design a repl on your laptop for things on the internet and
the APIs that connect them. ``unettest`` lets you unit test your network.



``unettest`` can be invoked as follows
--------------------------------------
**@ me on slack if you have questions or want a walkthrough!!**

Requirements:


* Docker
* docker-compose
* `\ ``unettest`` for MacOS <https://unettest.s3.us-east-2.amazonaws.com/unettest.mac>`_
  (`SHA-256 checksum <https://unettest.s3.us-east-2.amazonaws.com/mac-sha256>`_)



::

  $ unettest config.yml

.. NOTE::
  Use ``unettest --help``\ .


You can pass in an :doc:`config_document`. You can specify nginx.conf files from
anywhere you like. ::

   $ unettest config.yml --nginx-conf ~/my/nginx/conf

The `--nginx-conf` option takes a directory and configures the NGINX routing
using whatever is inside.

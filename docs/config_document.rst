===========================
 ``unettest`` Configuration
===========================

You can configure ``unettest`` to mimic any network. You can configure it with a
simple and straight-forward declarative configuration language in YAML, similar
to writing docker-compose. 

You first define the services in the network, then you write a series of tests
that are sent like requests into your network where their behavior is monitored
and tested for success.

Service Definitions
-------------------

``unettest`` operates with a group of fake ``service``\ s that represent a real
network.  If you have real-world servers or serverless microservices and an
NGINX server handling inbound traffic rules and routing instructions, you can
define tests for that NGINX server. ``unettest`` will create a test double for
each of your web services--they are defined in ``unettest`` as a ``service``\ .
Your NGINX.conf can talk to each of them as if they were the real thing, but for
ease of use, ``unettest`` fakes them on your own computer--you don't even need
to be connected to the internet to test your network rules!

When you load an NGINX.conf into ``unettest``, it'll use the routing rules as
you have defined them for your production systems. Since there is a replica (as
defined by your ``unettest`` Service Definitions) of the real network on your
local machine, you can manipulate and test routing rules without leaving your
own local development environment.

Test Doubles
^^^^^^^^^^^^

Your first objective as a ``unettest`` user setting up a test or REPL is to
configure some test doubles.

Say you have a web service, ``bookstore``. It has an assortment of routes. One
of them might be ::

  GET /books/non-fiction?author=davis

You also have an NGINX server.  This server is maybe doing things like 
`proxy_pass`\ ing requests from ::

  nonfictionbooks.com/authors/davis 

to your bookstore endpoint.

In the real world, your bookstore service receives ::

  GET /books/non-fiction?author=davis
  
and might return back a list of books 

* Women, Race & Class, Angela Davis
* Essays One, Lydia Davis
* The Autobiography of, Miles Davis

``unettest`` doesn't care about that. ``unettest`` is simply interested in
testing the network.  You can assume that your bookstore service is working and
that if you did actually call it, it would return something. You don't care. You
can define a ``service`` that looks like ``bookstore`` from the perspective of
NGINX.

.. code-block:: yaml

  services:
    - bookstore:
        routes:
          - name: non_fiction
            route: '/books/non-fiction'
            method: 'GET'
            status: 200
            params:
              - author

This tells ``unettest`` that you have a service, ``bookstore`` that can accept
routes to ``/books/non-fiction`` and will normally return a 200. It accepts
params for author. Pretty straightforward! Careful that you are precise with 
your indentation levels in the YAML.

And so we know we have some fancy logic in our NGINX.conf that will pass a
request from elsewhere to our venerable ``bookstore`` service. Let's see what
that might look like:

.. code-block:: nginx

  http {
          # docker-compose dns resolver
          resolver     127.0.0.11 valid=10s;

          server {
                  set_by_lua_block $bookstore {
                          -- here you can define logic for
                          -- test, non-prod, and prod urls
                          return "http://bookstore:5000"
                  }

                  server_name  _;

                  listen 80 default_server;

                  location ~* /authors/(.*) { 

                          proxy_set_header Host "localhost:5000";
                          proxy_pass $bookstore/books/non-fiction?author=$1; 

                  }
          }
  }

  events {
  }


You can put this in a file called ``nginx/nginx.conf`` where ``nginx`` is a
subdirectory of your pwd.

Test Definitions
----------------

Now you can write test cases for the NGINX rules.

.. code-block:: yaml

  tests:
    - test_non_fiction:
        send: 'GET'
        target: '/authors/davis'
        expect:
          - bookstore.non_fiction:
              called_times: 1
              method: 'GET'
              return_status: 200
              called_with:
                params:
                  author: davis

This is defining a request sent to NGINX.conf and then checking against its
intenal records that what you expect to happen is actually happening. 

``target`` is the uri sent to NGINX.

``expect`` is a declarative way of checking what happened. This one is saying
that the route ``non_fiction`` declared in ``bookstore`` is called one time,
that it was called with a GET, that it returned a 200, and also that it
included the query param ``?author=davis``. Our NGINX.conf is doing this work
and here we are testing that it parsed 'davis' out of the uri and is properly
configured to pass it to ``bookstore`` as a query param.

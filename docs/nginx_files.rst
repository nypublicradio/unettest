============
 NGINX Files
============

How to Configure ``unettest``\ 's NGINX
---------------------------------------

Your ``unettest`` routes traffic to your fake services using NGINX. So, how do you tell
``unettest`` which NGINX conf files to use?

.. NOTE::
  At the moment, ``unettest`` only supports directories of NGINX files, not single files. You
  can have a directory with only one file in it, but be aware that you must be pointing
  ``unettest`` to a directory.

There are a handful of ways to load NGINX confs, depending on what is most convenient.
During execution, you will find a log line that tells you which config ``unettest`` has chosen
to use.

Default
^^^^^^^

If given no other configuration, ``unettest`` will look in the default folder, ``./nginx/``.
So if you are running ``unettest`` from a folder that has a folder called ``nginx`` containing
nginx configurations, those will be used.

Command Line Arg
^^^^^^^^^^^^^^^^

You can point ``unettest`` at any arbitrary collection of NGINX files with the command line
arg ``--nginx-conf``.

Using the flag
  e.g. ``unettest --nginx-conf ~/work/nginx``

ENV VAR
^^^^^^^

You can also set an env var that ``unettest`` will reference when running your service and
test suites. This is especially useful when you are using the same config over and over.

NGINX_CONFIG
  is the var to set.

  e.g. ``export NGINX_CONFIG=~/work/nginx``

  note -- you can set this in your shell dotfiles but be careful that you don't forget
  about it and months later wonder why nginx isn't using the config you think it is.

Title: Managing Django settings the right way
Subtitle: We've been doing this wrong for a very long time...
Author: Karol Majta
Date: 2013-05-06 02:37
Tags: Django, Python

It all starts with SQLite and a single settings file. Managing this kind of configuration is
a no brainer. Just drop your apps into your django project folder, update
the settings file, grab a coke and enjoy your life. After a few weeks reality
starts to kick in.

The first thing you realize is that SQLite is so ridiculously forgiving
that your tests pass on development machine but fail on staging and production
boxes. This is a first lession learned, you start to use PostgreSQL whenever
possible, even on development machines.

Then comes the second problem. Django's idea of drop-in apps does not seem like
the best idea anymore, and you start to use distribute to manage your
applications, because it just seems cleaner to use the same tools for yours
and third party tools.

Then comes the menace of managing configuration.

Who changed that setting?
=========================

I strongly believe that the number of ideas on how to manage django settings
files is even higher than the number of django devs. After a while of working
with the framework I can honestly say that I've seen really ugly things and
I've done things I'm not really proud of when it comes to managing
configuration. To make things worse, django docs on this material are really
sparse. When there's no opinionated way of doing things raw creativity can
take over common sense. So let's clarify things a bit:

  1. I am a huge opponent of django's default way of managing apps
     by keeping them in a project module. Use distribute, it was made
     for this and it gets the job done right.
  
  2. Your settings files need to be under version control.

  3. There should be only one settings file per project. `local_settings.py`
     hackery allways ends up with `special_case_settings1.py` files lying
     around in your project directory.

These three points seem reasonably simple and straightforward, but they
can be tricky to implement, as they need different approaches for development
and staging/production environments.

I like to keep a separate *project repo* that contains just the settings,
project-wide templates and all requirements listed in `requirements.txt`.
This way installing an app is a breeze, but sometimes the extra work
necessary for editting the `settings.py` after checkout seems a bit over
the top.

Environment variables to the rescue
===================================

In *Two Scoops of Django* Danny Greenfeld argues that settings that may
vary between different machines should be configured with environment
variables. In your `settings.py` can basically do:

    python::
    APNS_CERTFILE = os.environ.get('MYAPP_APNS_CERTFILE', None)
    if APNS_CERTFILE is None:
        raise ImproperlyConfigured("You need to send push messages man!")

This way you can make it hard to launch a project which lacks proper config
and provide fellow developers on how to configure it properly. But there's
a little caveat: how do you manage environment variables between projects
and on one machine? Let's say you develop two projects at the same time
and they both use `SOMEVAR` environment variable. How do you set it properly
when working with each of them? And what happens when you remove them from
disk, do you end up with an unnecessary `export` statement in your `.bashrc`?
How do you set your variables on staging and production servers if they share
the same machine?

Develop your virtualenvwrapper skills!
--------------------------------------

I was pretty hesitant towards the idea of **virtualenvwrapper** since I saw
it as a bunch of unnecessary bells and whistles around plain ol' virtualenv.
I still don't think that `workon` or `mkvirtualenv` is a big productivity
gain, but the virtualenvwrapper has one utility that makes managing per-project
environments a breeze. In each of your virtualenv `bin` directories you can
place a `postactivate` script that will get sourced each time you activate it.
Seems pretty obvious now:

    bash::
    # postactivate
    export MYAPP_APNS_CERTFILE="/home/hacker/apns.pem"

This gets even better. You can also create a `postdeactivate` script run
each time you deactivate an env:

    bash::
    # postdeactivate
    unset MYAPP_APNS_CERTFILE

This way you always revert changes to your `$PATH` when virtualenv gets
deactivated.

Yup! It's that simple. Absolutely no pain and you get a very clean separation
of settings code, that can be checked with git and change only from time to
time from environment-dependent settings that developers can change freely as
they wish.

In production
-------------

If you've ever done any deployments with `mod_python` or `mod_wsgi` you
probably know that virtualenvs `activate` and `activate_this` scripts don't
play nicely on production servers. Solution is simple. Use **Gunicorn**
managed by **Supervisord**. This also is a no-brainer. When specifying
command for your *program block* just remember about two simple things:

  1. Always provide full path to executable in virtualenv

  2. Don't forget to setup the child process' environment variables

If you stick with these rules a fragment of your configuration for Supervisord
may look like this:

    [program:myproject]
    ...
    directory = /path/to/my/django/project/
    command = /path/to/my/virtualenv/bin/gunicorn project.wsgi.application
    environment = MYVAR="myvar",MYOTHERVAR="myothervar"
    ...

Can this get better?
====================

While I think envvars combined with virtualenvwrapper in development and
supervisord in production provide fair amount of help in separating your
code from configuration, there might still be room for improvement. If
you have any thoughts on this feel free to share them in comments.


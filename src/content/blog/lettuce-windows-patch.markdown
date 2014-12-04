Title: Virtualenv + Lettuce + Splinter + Windows Monkeypatch
Subtitle: The dirty hack for integration testing on Windows
Author: Karol Majta
Date: 2012-05-01 15:08 
Tags: Python, Django, Virtualenv, Splinter

Recently I've been hacking around with BBD testing and Django using Virtualenv,
Lettuce and Splinter. My machine runs Windows and I ran into an annoying 
error related to unicode string encoding in Windows PATH. If you find
yourself in same kind of trouble, I present a quick (and dirty) three-line
fix that can solve the issue.

## What went wrong?

After setting up a vanilla virtualenv for my project I installed Django,
Lettuce and Splinter. Everything worked fine in Python interactive shell
and after activating the endvironment I was able to start the browser and
control it using Splinter:
 
    :::pycon
    In [1]: from splinter.browser import Browser

    In [2]: b = Browser()

    In [3]: b.quit()

That worked like a charm.

Unfortunately when I ran my first integration test with lettuce an ugly error
appeared.
 
    :::pytb
    Traceback (most recent call last):
      File "c:\Users\Karol\Python\Django\i-lend-you\lib\site-packages\lettuce\registry.py", line 85, in call_hook
        callback(*args, **kw)
      File "C:\Users\Karol\Python\Django\i-lend-you\ilendyou_project\terrain.py", line 15, in set_browser
        world.browser = Browser('firefox')
      File "c:\Users\Karol\Python\Django\i-lend-you\lib\site-packages\splinter\browser.py", line 37, in Browser
        return driver(*args, **kwargs)
      File "c:\Users\Karol\Python\Django\i-lend-you\lib\site-packages\splinter\driver\webdriver\firefox.py", line 27, in __init__
        self.driver = Firefox(firefox_profile)
      File "c:\Users\Karol\Python\Django\i-lend-you\lib\site-packages\selenium\webdriver\firefox\webdriver.py", line 45, in __init__
        self.binary, timeout),
      File "c:\Users\Karol\Python\Django\i-lend-you\lib\site-packages\selenium\webdriver\firefox\extension_connection.py", line 46, in __init__
        self.binary.launch_browser(self.profile)
      File "c:\Users\Karol\Python\Django\i-lend-you\lib\site-packages\selenium\webdriver\firefox\firefox_binary.py", line 43, in launch_browser
        self._start_from_profile_path(self.profile.path)
      File "c:\Users\Karol\Python\Django\i-lend-you\lib\site-packages\selenium\webdriver\firefox\firefox_binary.py", line 65, in _start_from_profile_path
        env=self._firefox_env).wait()
      File "d:\Python2\Lib\subprocess.py", line 672, in __init__
        errread, errwrite)
      File "d:\Python2\Lib\subprocess.py", line 882, in _execute_child
        startupinfo)
    TypeError: environment can only contain strings

A quick research on that error showed it is related with attemts of adding
unicode strings with encoding other than UTF-16 to Windows PATH.

## The monkeypatch

I should start with a big disclaimer. **This is not a fix! This is a sloppy
and ugly monkeypatch, but it makes things run.**

When you look at the traceback you can see the error originates in Selenium's
Firefox webdriver. Analyzing the code shows that in **__init__** the driver
builds a dict by copying the environment of the parent process.

    :::python
    def __init__(self, firefox_path=None):
        self._start_cmd = firefox_path
        if self._start_cmd is None:
            self._start_cmd = self._get_firefox_start_cmd()
        # Rather than modifying the environment of the calling Python process
        # copy it and modify as needed.
        self._firefox_env = os.environ.copy()

We can slightly modify the constructor to escape each entry in the dict.

    :::python
    def __init__(self, firefox_path=None):
        self._start_cmd = firefox_path
        if self._start_cmd is None:
            self._start_cmd = self._get_firefox_start_cmd()
        # Rather than modifying the environment of the calling Python process
        # copy it and modify as needed.
        escaped_environ = {}
        for key, value in os.environ.items():
            escaped_environ[key] = str(value)
        self._firefox_env = escaped_environ

That's it. My tests started working after this patch.

## The right way to go

I suspect that Lettuce does some *magic* to **os.environ** when launching
tests in a subprocess, but I had no time investigate. I don't think that
Selenium or Splinter can be to blame, because they do work in standard
Python scripts and in interactive shell. So the right way to go would be
to find the issue in Lettuce and fix it, which I will probably do soon.

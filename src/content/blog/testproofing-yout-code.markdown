Title: Testproofing your code
Subtitle:
Author: Karol Majta
Date: 2013-06-02 20:17
Tags: Python, Django, BDD, TDD, patterns

Recently I've been playing quite a lot with [Behave](http://pythonhosted.org/behave/),
a lovely and fresh BDD framework for Python. If you're
looking for a really hype tool to mess around with
end-to-end tests and user specs you should give it
a try.

Writing stories and acceptance tests would be super
fun if there was no database, external APIs, and no
"enviroment" that should be properly mocked out.
Database trip times can be kept low by using in-memory
SQLite, it's the http layer that becomes a real pain.

Fortunately I've found a great [HTTPretty](https://github.com/gabrielfalcao/HTTPretty)
library that monkey-patches Python's socket module keeping all
requests made with popular HTTP libraries in strict
isolation from the outside world.

So far so good... You can monkey patch stuff, mess
around with your configuration and keep your tests
quite reliable, but why the hell is it so hard?

## Tested code vs Testable code

*It's broken until it's tested*, isn't it? True,
true, so let's look at some simple example:

    ::python
    import uuid
    
    class Entity(object):
        """
        Super dull class that only has an id. And by
        accident it can be compared...
        """
        
        def __init__(self)
            self.entity_id = int(uuid.uuid4())
        
        def __cmp__(self, other):
            if self.entity_id < other.entity_id:
                return -1
            elif self.entity_id == other.entity_id:
                return 0
            else:
                return 1
        
        def __hash__(self):
            return self.entity_id

The `__hash__` method is a simple getter so it doesn't
need a test, let's have a look at the test for `__cmp__`:

    ::python
    def test_cmp():
        e1 = Entity()
        e2 = Entity()
        
        expected = e1.entity_id < e2.entity_id
        actual = e1 < e2
        
        assert expected == actual

Whoa! Tested code, it works :) Yup, it does, but you
probably already see the smell in it. We had to
duplicate the logic of `__cmp__` method inside the
test to do some introspection about the objects. That's
bad. Firstly, it's against the DRY principle, secondly
unittests are about assumptions that look trivial in
test code. This one is not. So, how to refactor our
code?

    ::python    
    class Entity(object):
        """
        Super dull class that only has an id. And by
        accident it can be compared...
        """
        def __init__(self, entity_id):
            self.entity_id = entity_id
        
        def __cmp__(self, other):
            if self.entity_id < other.entity_id:
                return -1
            elif self.entity_id == other.entity_id:
                return 0
            else:
                return 1
        
        def __hash__(self):
            return self.entity_id

Test code is really simple now:

    ::python
    def test_cmp():
        e1 = Entity(1)
        e2 = Entity(2)
        
        assert e1 < e2

That's good, and it's a really good idea to **never
instantiate or by other means "obtain" anything** in
your constructors. Everything that's neccessary to
create an instance should be provided as arguments.

That seems great when you're reading smart books filled with
bright insights, but we all know in real world code
this can get painfully cumbersome to always provide
every small piece of information.

## Give me the defaults!

We need them so bad! The power of great python
libraries such as *Requests* comes from the fact
that they're dead simple to use without a single line
of configuration.

Providing defaults is really simple in Python and
because the language is so robust there is more than
one way to do it.

Factory methods and default arguments:

    ::python
    import uuid

    class Entity(object):
        """
        Super dull class that only has an id. And by
        accident it can be compared...
        """
        
        @classmethod
        def create(self, cls, uid_factory=uuid.uuid4)
            return Entity(uid_factory())
        
        # here comes the rest of implementation

Class properties:

    ::python
    import uuid

    class Entity(object):
        """
        Super dull class that only has an id. And by
        accident it can be compared...
        """
        
        uid_factory = uuid.uuid4
        
        def __init__(self):
            self.entity_id = self.__class__.uid_factory()
        
        # here comes the rest of implementation

Both ways seem equaly good for me and it's mostly
a matter of taste which one you prefer.

Default arguments may lead to really long constructor
lists, if other classes use `Entity` their methods
may carry this burden further into your code.

Class properties are powerful, but if you look at
the `__init__` there is no obvious way to pass
the `entity_id` explicitly, so in your tests you
would need to configure the class with custom factory.

## Welcome to the Real World

Previous examples were somewhat made up to prove some
points, but they're not very detached from real
solutions. Let's look at a django view that fetches
`google.com` and returns the result:

    ::python
    from django.views.generic.base import View
    from django.http import HttpResponse
    
    import requests

    class GoogleView(View):
    
        def get(self, request):
            text = requests.get("http://google.com").text
            return HttpResponse(text)
            
Now imagine an end-to-end test run using *Selenium* or
other framework, or better, a whole suite. How can you
prevent it from hitting the network hundreds of times?
How can you prevent it from failing unexpectedly on
network errors, or google errors (this probably won't
happen, but who knows?). You can monkeypatch.

What if you provide this code to your client and he
runs his acceptance suite? He can monkeypatch. But he
will monkeypatch code that he does not know, he will
dig into the internals he would never think to care
about. He shouldn't have to. He can also mock the
whole network layer with *HTTPretty*. Whatever he
does, the person responsible for end-to-end tests will
probably hate you.

One simple refactoring in this code can change this:

    ::python
    class GoogleView(View):
    
        http_provider = requests
    
        def get(self, request):
            text = self.http_provider.get("http://google.com").text
            return HttpResponse(text)

Now in any BDD framework, such as *Behave* one can
modify the behavior of this class for the whole suite:

    ::python
    import GoogleView

    class StubResponse(object)
        def __init__(self, text):
            self.text = text

    class StubRequests(object):
        def get(url):
            return StubResponse("Hello from google!")

    def before_all(context):
        GoogleView.http_provider = StubRequests()

## Testable for the win!

Let me state it again: *tested code is the code that
works*, but **testable code is the quality code**. If
your library/framework/product is not painfully
difficult to mock/silent/replace/configure in
end to end tests, you're doing it right.

If there are any bright ideas in that big, steamy, obese
pile of junk - Java, it's **the interface**.
Interfaces cannot be instantiated, and it's great
for tests, because if you depend on interfaces in your
tests you can **always** inject a stub instead of
a real thing.

Dynamic languages make it easy to, monkeypatch,
change behaviors at runtime etc. but they also make
lazy programmers and libraries that are well unit
tested, fun to work with, but fail utterly when you
try to make them transparent in end to end tests.
Get things right. Leave a back door for others to
configure your classes. Provide reasonable
defaults. Others will love your code.

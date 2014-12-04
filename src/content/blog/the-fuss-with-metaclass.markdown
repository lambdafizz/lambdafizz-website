Title: The fuss with metaclass
Subtitle: If you're a wizard, don't use black magic
Author: Karol Majta
Date: 2013-08-18 23:00
Tags: Python, metaprogramming, decorators

Most of young Python ninjas just after entering the dojo learn that metaclasses
are magic. And by magic I mean the good stuff: they spare you work, they spare
you tedious configuration, they "just work", when someone gives them to you.
With this in mind we happily use them to our benefits, and after some time
questions start to arise, and one of them arises quite often: how the hell
does all this stuff work?

Lots of resources on the web state two things:

  - metaclasses are complicated
  - if you are wondering if metaclasses solve your problem, you probably
    should not use them

Well, in my personal opinion, both of the above just prove how some crap
repeated a lot can become a "common knowledge".

Metaclasses are one of the simplest mechanisms of Python, and definately
are much simpler than inheritance (which you probably consider quite
intuitive, don't you?). Yet they should be sometimes avoided, but not
due to their complexity, but because of subtle design flaws they can introduce. Want to find out more? Bare with me.

## What the hell is metaprogramming

Againsit common opinion metaprogramming is posible in every language, dynamic
ones just make it much simpler, and provide intuitive and commonly undersood
semantics. Metaprogramming is just modifying the program in the "before runtime"
stage. It would be easy to assume that what "before runtime" means varies from
language to language, i.e. in C before runtime would be the compile and link
stage, in Python it would be the interpreters first pass through the code (the
so-called import time). Unfortunately this is all wrong. The *meta  part of the
program are all things that happen before the program  starts to execute the
primary task it was designed for, and have the ability to change the way this
task is accomplished*.

To avoid misconceptions lets use two simple examples. Loading configuration
from files and dependency injection. I do not consider loading configuration
*meta*, because while it usually happens before program's main task execution
it does not affect the runtime phase - the configuration can be considered part
of program input, that just like other data gets somehow transformed into the
output by the main task of the program - always in the same way.

On the other hand dependency injection, also performed in the *"before runtime"*
phase has the ability of to change the way a program is executed, as not only
data, but also algorithms are passed further into the *main* part of the
program.

If this still seems a bit cryptic, there's an even easier way of thinking about
what metaprogramming is. It's a civilized macro! Or to put it backwards, macros
were the simplest approach to metaprogramming. Everything that can be done using
macros can be done using *meta* mechanisms of other languages.

So, let's get back to reading configuration files and dependency injection.
Reading configuration files cannot be accomplished using macros, as settings
tend to thange between program runs. Dependency injection can be easily
accomplished with macros, with simple `#ifdef` directives, it is performed
only once, and any change in it's structure needs a new program build.

## The Python way

Okay, with a faint idea of the whole *meta* fuss, let's see how Python tackles
these problems. For our convenience we will use familiar python2.7 syntax.
Declaring a metaclass of a class in python3 has diffetent syntax, but works the
same way, so it should pose no trouble to port code samples from this article.
If you're looking for cross-version portability, use the `six` module from
cheeseshop.

To declare a metaclass on a class you just write:

    :::python
    def MyMeta(name, bases, attrs):
        return type(name + "WithMeta", bases, attrs)

    class SomeClass(object):

        __metaclass__ = MyMeta

Abra-cadabra, done! SomeClass' metaclass is now `MyMeta`. But wait, what?! MyMeta is a function, not a class, so how can it even be a metaclass? That's simple.
A *metaclass* is anything that can produce a class. Our `MyMeta` callable does
exactly that, it just returns a new type using python's builtin `type` function.

Fiddling with the code yields something like:

    >>> a = SomeClass()
    >>> print a
    <class '__main__.SomeClassWithMeta'>

Actually, it's all there is. Sometimes we use subclasses of `type` as
metaclasses, but it's just to get sane default behaviors -- this is well
discussed on StackOverflow.

## Where the weird things are...

The sample above seems dead simple, right? You can modify just about
every aspect of a class before it actually get's created. You can perform
actions that require a class before, during and after it's creation. This is
like having superpowers at no costs! The problem is, superpowers never come
as free-of-charge giveaways... Consider:

    :::python
    class Unicorn(type):

        def __init__(klass, name, bases, attrs):
            klass.__name__ += "IsUnicorn"

    class SeaMonster(type):

        def __init__(klass, name, bases, attrs):
            klass.__name__ += "IsSeaMonster"

    class Pony(object):

        __metaclass__ = Unicorn

    class Fish(object):

        __metaclass__ = SeaMonster

Let's see how the code works:

    >>> print Pony
    <class '__main__.PonyIsUnicorn'>
    >>> print Fish
    <class '__main__.FishIsSeaMonster'>

So far so good. So now let's imagine this code got shipped to *Joe The
Programmer Inc.* and they want to get what's best of it. Both Pony and Fish
just inherit from object, so it might be quite safe to mix them into `Seahorse` and save ourselves some work:

    :::python
    class Seahorse(Pony, Fish):
        pass

And we get a nasty error:

    TypeError: Error when calling the metaclass bases
        metaclass conflict: the metaclass of a derived class must be a (non-strict) subclass of the metaclasses of all its bases

It looks like we gave up the power of multiple inheritance. And yes, we did...
a little bit. You can probably figure yourself what's the deal.
`class Seahorse(Fish, Pony)` is an instance of `Pony`, but the `__metaclass__`
from mixed in class `Fish` takes precedence, and now Seahorse's metaclass is `SeaMonster`. As you see that makes no sense to python interpreter. Seahorse's metaclass should be a subclass of both `SeaMonster` and `Unicorn`. We have to
manually resolve the conflict, and the *magic* is no longer contained *behind
the door*.

## Un-weird it

It seems that a metaclass approach was just ill suited for the job. Are there
better ways. Yup, there are: class decorators! Check this little snippet out:

    :::python
    def is_a(creature_name):
        def decorator(klass):
            klass.__name__ += "Is" + creature_name
            return klass
        return decorator

    @is_a("Unicorn")
    class Pony(object):
        pass

    @is_a("SeaMonster")
    class Fish(object):
        pass

    @is_a("SeaMonster")
    @is_a("Unicorn")
    class Seahorse(Fish, Pony):
        pass

Let's see how it works:

    >>> print Seahorse
    <class '__main__.SeahorseIsUnicornIsSeaMonster'>

This approach has a few benefits. Firstly, it works. Secondly, the class
hierarchy is loosely coupled with the *monster* and *unicorn* behaviors, which
allows for greater flexibility. It comes with a price, we had do explicitly
specify *monster* and *unicorn* behaviors for `Seahorse`, but this is good
in some ways:

  - author of `Seahorse` class must be explicit about these behaviors, so
    he acknowledges he knows how to use them.
  - author of `Seahorse` is in control of the order in which decorators
    are applied.

In my opinion, the two points above follow python's **explicit is better than
implicit** rule, and I am in favor of this style of programming.

## So what's the fuss?

Metaclasses are dead simple. Metaclasses are pretty powerfull. So what's the
fuss? Why are they black magic? Well, I consider the *metaclass relation* one
of the strongest contract a class can declare. It's even stronger than
inheritance, and as you know, abusing inheritance can yield a code that's
extremely hard to maintain, extend and modify.

Programming based on metaclasses is super-cool as it has something in common
with wizardry, and allows you to feel the thrill of being really smart, but it
can easily lead you to a dead end if you need to quickly extend the feature
set of your classes using third party libraries.

Each class can only have one metaclass, does it ring a bell? Yup, my friend,
when depending on metaclasses you are actually coding Java, a big steamy pile
of junk, as graceful as a 20 year old school bus. Seems scary? Better fasten
your seatbelts, because the thing you're driving has no emergency brakes of
static type system.

Conclusions? Metaclasses are *black magic*, and while black magic is not very
difficult to learn, the price you pay for using it can be unexpectedly high.

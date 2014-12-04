Title: Python Decorators
Subtitle: They're good for you, your family and your dog!
Author: Karol Majta
Date: 2012-01-27 21:12 
Tags: Python, decorator

Did you ever find yourself trying to add some functionality to code you wrote
six months earlier not imaging you would ever have to extend it? I can bet it
wasn't the most enjoyable time. Fortunately Python decorators come to the rescue!

Let's look at the code I wrote six months ago.

    :::python
    # functions.py

    def factorial(n):
        """
        Calculates factorial of n
        """
        if n <= 1:
            return 1
        else:
            return factorial(n-1)*n

This function calculates factorial of n. Pretty boring - no wonder I let it
lay around for half a year. Today I wanted to add some messages that would
visualize the recursion tree of these functions for my *Fibonacci and Factorials
Explained Fictional Project* which looks like this:

    :::python
    # project.py
    
    from functions import factorial
    
    print "factorial of 5 is {}".format(factorial(5))

If only I had added some logging to these functions...

### Basic *log* decorator

Hardcoding log messages is an option, but you have to hardcode them in *all*
functions. What if there were not one, but ten?

This is where you decide decorators suit great for this situation. So, what
would a decorator generating logging messages look like?

    :::python
    # decorators.py
    
    def log(callable):
        def _callable(*args):
            print "calling {} with arguments {}".format(callable, args)
            result = callable(*args)
            print "{} returned {}".format(callable, result)
            return result
        return _callable

Unless the function has side effects, which is not very common in Python,
we only need to care about the arguments the function receives and
the value it returns. On function call our decorator needs to grab arguments
print them out *(line 5)*, call the function, capture it's result *(line 6)*,
print it letting us know the function has exited *(line 7)*, and finally
return the calculated value *(line 8)*.

Function **log** returns **_callable**, which does exactly what we need.
Now we can use Python's sweet decorator syntax to replace **factorial**
with **_callable**.

The new function definition looks like this:

    :::python
    # functions.py
    
    from decorators import log
    
    @log
    def factorial(n):
        """
        Calculates factorial of n
        """
        if n <= 1:
            return 1
        else:
            return factorial(n-1)*n

And the result is:

    :::sh
    $ python project.py
    calling <function factorial at 0x014B7B30> with arguments (5,)
    calling <function factorial at 0x014B7B30> with arguments (4,)
    calling <function factorial at 0x014B7B30> with arguments (3,)
    calling <function factorial at 0x014B7B30> with arguments (2,)
    calling <function factorial at 0x014B7B30> with arguments (1,)
    <function factorial at 0x014B7B30> returned 1
    <function factorial at 0x014B7B30> returned 2
    <function factorial at 0x014B7B30> returned 6
    <function factorial at 0x014B7B30> returned 24
    <function factorial at 0x014B7B30> returned 120
    factorial of 5 is 120

Yay! It works, and we can apply it to *any* number of functions to track when
they are called and when they return.

### Parametrized decorators

One thing that bothers me is the fact that we dont get a *pretty* function name.
Instead we get **&lt;function factorial at 0x014B7B30&gt;**. We could use a regular
expression to extract function name from it, but I'm not really good at regex.
Instead we can parametrize our decorator with the name for wrapped function.

We will take advantage of the fact that, as we previously stated, python decorators
are *evaluated* once, at definition time. This means, that when we use
**@function(arg1,...)**, firstly **function(arg1,...)** is evaluated,
and secondly the returned value is used as the decorator.

Our parametrized decorator now looks like this:

    :::python
    # decorators.py
    
    def log(name="unknown function"):
      def _log(callable):
          def _callable(*args):
              print "calling {}{}".format(name, args)
              result = callable(*args)
              print "{}{} returned {}".format(name, args, result)
              return result
          return _callable
      return _log

The above snippet may look complicated, but it actually is pretty simple if you
understand *lexical closures*. Function *log* is used just to provide lexical
scope with **name** in it for definition of the actual decorator *_log* which
works exactly the same way as in previous example.

We decorate function providing a name we want to call the wrapped function:

    :::python
    @log("factorial")
    def factorial(n):
        """
        Calculates factorial of n
        """
        if n <= 1:
            return 1
        else:
            return factorial(n-1)*n

Let's see the result:

    :::sh
    $ python project.py
    calling factorial(5,)
    calling factorial(4,)
    calling factorial(3,)
    calling factorial(2,)
    calling factorial(1,)
    factorial(1,) returned 1
    factorial(2,) returned 2
    factorial(3,) returned 6
    factorial(4,) returned 24
    factorial(5,) returned 120
    factorial of 5 is 120

### Stateful decorators

Above output is already pretty good, but it would be nice to have some kind
of graphical indication of the depth of recursion. To accomplish this the
decorated function has to "remember" at what level it was called last time.

Basically if we had some place to store the current recursion depth,
the decorator would have to:

1. increment the recursion depth
2. call wrapped function
3. decrement the recursion depth

The algorithm itself is very simple, finding a proper place to store the variable
is a bit harder task. You probably know that in Python *functions are first-class
objects*. Well, in fact we can work it the other way round. In python you can make
any object a function (or strictly speaking, a *callable*). And objects have
exactly what we need - they have *state*. The solution is to decorate our function
with a callable, stateful object instead of another function.

This is how it's done:

    :::python
    # decorators.py
    
    class Log(object):
        def __init__(self, name="unknown function"):
            self._name = name
            self._depth = 0
        def __call__(self, callable):
            def _callable(*args):
                separator = "".join(["." for i in xrange(0, self._depth)])
                print "{}calling {}{}".format(separator, self._name, args)
                self._depth += 1
                result = callable(*args)
                self._depth -= 1
                print "{}{}{} returned {}".format(separator, self._name, args, result)
                return result
            return _callable

In the initializer we create an instance variable **_name** used for storing
the name of the function, and **_depth** for storing current depth in the call
stack. Then we define a **__call__** instance method, which will be used to
call instances of **Log**. **__call__** returns a decorated function which
keeps track of the depth and handles printing to screen.

Let's apply this decorator to **factorial**:

    :::python
    @Log("factorial")
    def factorial(n):
        """
        Calculates factorial of n
        """
        if n <= 1:
            return 1
        else:
            return factorial(n-1)*n

What happens here is:

1. **Log("factorial")** is evaluated returning a callable object (our decorator).
2. **@** is applied to the callable object. It gets called with **factorial**
   passed as argument.
3. **factorial** is wrapped inside **_callable**, returned and reassigned, but
   still has access to **_depth** of the instance because of *lexical closure*.

And the result is:

    :::sh
    $ python project.py
    calling factorial(5,)
    .calling factorial(4,)
    ..calling factorial(3,)
    ...calling factorial(2,)
    ....calling factorial(1,)
    ....factorial(1,) returned 1
    ...factorial(2,) returned 2
    ..factorial(3,) returned 6
    .factorial(4,) returned 24
    factorial(5,) returned 120
    factorial of 5 is 120

Wow, that looks cool! And, believe me, decorators really are cool.

There are some caveats, however. A careless programmer like me
could write a snippet:

    :::python
    # snippets.py
    
    from decorators import Log
    
    @Log("fun1")
    def fun1():
        pass

    @Log("fun2")
    def fun2():
        fun1()

    @Log("fun3")    
    def fun3():
        fun2()
        
    fun3()

The syntax looks pretty intuitive - it seems we decorate three functions with **Log**!

Let's look at the output:

    :::sh
    $ python snippet.py
    calling fun3()
    calling fun2()
    calling fun1()
    fun1() returned None
    fun2() returned None
    fun3() returned None

The order of calls is correct, however the call stack depth is obviously wrong.
**fun1** gets called deeper than **fun2**, and **fun2** should be one level
deeper than **fun1**. The reason of this behavior is, we actually decorated
our functions with three different loggers that do not share state. We need to
get one Log instance and decorate all functions with it:

    :::python
    # snippets.py
    
    from decorators import Log
    
    commonlog = Log()
    
    @commonlog
    def fun1():
        pass

    @commonlog
    def fun2():
        fun1()

    @commonlog    
    def fun3():
        fun2()
        
    fun3()
    
This results in:

    :::sh
    $ python snippet.py
    calling unknown function()
    .calling unknown function()
    ..calling unknown function()
    ..unknown function() returned None
    .unknown function() returned None
    unknown function() returned None
    
This snippet works as expected, but we lack the functionality of getting functions'
names. We can only parametrize out decorator once, while creating it with **Log("name")**.
We could fall back to using default function names, or values obtained from them with
regular expressions.

## What next?

Now that you've learned that Python decorators are pretty powerful and can
save you lots, and lots of tedious, boring work it's time to learn about
the few decorators that come with Python's Standard Library. Some of them
are part of the language itself, others come bundled with standard modules.

1. [property](http://docs.python.org/library/functions.html#property)
2. [staticmethod](http://docs.python.org/library/functions.html#staticmethod)
3. [classmethod](http://docs.python.org/library/functions.html#classmethod)
4. [abc.abstractmethod](http://docs.python.org/library/abc.html)

[Django](http://www.djangoproject.com) uses decorators pretty often, and they do save you the most boring kind of work!

Stay tuned for more decorator goodies.

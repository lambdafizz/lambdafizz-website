Title: Memoization with decorators
Subtitle: Short guide to poor man's Memcached.
Author: Karol Majta
Date: 2012-04-01 18:10 
Tags: Python, decorator, memoization

Ok, so you already have some decorator knowledge, don't you? If not take a quick 
look at [Python decorators](http://karolmajta.com/blog/python-decorators) 
introductory article I wrote a while ago. Armed with this knowledge you can do
some pretty useful stuff. Today we will look at a technique called *memoization*.

### Memoization 101

So what basically is memoization? It's just storing previously calculated values 
for further use durging program execution. Let's again refer to *Fibonacci and 
Factorials Explained Fictional Project*. This time we will investigate a function 
calculating values of the Fibonacci sequence:

    :::python
    # functions.py
    def fibonacci(n):
        """
        Calculates n-th element of Fibonacci sequence
        """
        if n == 0:
            return 0
        if n == 1:
            return 1
        else:
            return fibonacci(n-2)+fibonacci(n-1)

We can call it from other file like this:

    :::python
    # project.py
    import sys
    
    from functions import fibonacci

    print "fibonacci({0}): {1}".format(sys.argv[1], fibonacci(int(sys.argv[1])))

We get what we expect. But let's look what happens if we decorate the function with
the previously written _log_ decorator and call it:

    :::python
    # functions.py
    
    from decorators import Log
    
    @Log(name="fibonacci")
    def fibonacci(n):
        """
        Calculates n-th element of Fibonacci sequence
        """
        if n == 0:
            return 0
        if n == 1:
            return 1
        else:
            return fibonacci(n-2)+fibonacci(n-1)

The console output:

    :::sh
    $ python snippet.py 4
    calling fibonacci(4,)
    .calling fibonacci(3,)
    ..calling fibonacci(2,)
    ...calling fibonacci(1,)
    ...fibonacci(1,) returned 1
    ...calling fibonacci(0,)
    ...fibonacci(0,) returned 0
    ..fibonacci(2,) returned 1
    ..calling fibonacci(1,)
    ..fibonacci(1,) returned 1
    .fibonacci(3,) returned 2
    .calling fibonacci(2,)
    ..calling fibonacci(1,)
    ..fibonacci(1,) returned 1
    ..calling fibonacci(0,)
    ..fibonacci(0,) returned 0
    .fibonacci(2,) returned 1
    fibonacci(4,) returned 3
    fibonacci(4): 3

Investigating the console output we can figure out some pretty redundant operations 
take place:
    
1. _fibonacci(n)_ gets called with arguments 4, 3, 2, 1 and 0 - that's 
perfectly fine, as we only go "deeper" in the recursion tree.
2. _fibonacci(1)_ and _fibonacci_(0) return (into _fibonacci(2)_)
3. _fibonacci(2)_ returns (into _fibonacci(3)_) and then _fibonacci(1)_ gets called
again, because as you're probably aware _fibonacci(3)=fibonacci(2)+fibonacci(1)_.

Of course we have calcualed the value of _fibonacci(1)_ before and there is no 
need to do it again. The problem can be found in a few other places in the console 
log and tends to become even more severe when argument given to the script is bigger. 
For the sake of brevity I won't include console dumps for that case, but you can try 
it yourself.

One noticable thing is the fact that this problem is not obvious, as humans 
calculate Fibonacci numbers starting from 0 - there is no repetition. The 
recursive algorithm solves it the other way round.

You probably already figured out that the solution is to store previously 
calculated values. This is done in an *extremely* easy and elegant way with 
a class based decorator.

### The *Cache()* decorator

The code is pretty short:

    :::python
    # decorators.py
    
    class Cache(object):
        def __init__(self):
            self._storage = {}
        
        def __call__(self, callable):
            def _callable(*args):
                if self._storage.has_key(args):
                    return self._storage[args]
                else:
                    result = callable(*args)
                    self._storage[args] = result
                    return result
        return _callable
    
        def clear_cache(self):
            self._storage = {}

In the constructor we create the cache. The **__call__** method is actually 
responsible for decorating the function, and **_callable** will replace it.
**_callable** works in a pretty straightforward way. If the arguments' tuple
is in the cache dict return it. Else, add it to the cache dict and then return 
it. There is also an utility method for clearing the cache between function 
calls.

Decorated _fibonacci_ function:

    :::python
    # functions.py
    
    from decorators import Log, Cache

    fib_cache = Cache()
    
    @fib_cache
    @Log(name="fibonacci")
    def fibonacci(n):
        """
        Calculates n-th element of Fibonacci sequence
        """
        if n == 0:
            return 0
        if n == 1:
            return 1
        else:
            return fibonacci(n-2)+fibonacci(n-1)

Let's look at the new console output:

    :::sh
    $ python snippet.py 4
    calling fibonacci(4,)
    .calling fibonacci(3,)
    ..calling fibonacci(2,)
    ...calling fibonacci(1,)
    ...fibonacci(1,) returned 1
    ...calling fibonacci(0,)
    ...fibonacci(0,) returned 0
    ..fibonacci(2,) returned 1
    .fibonacci(3,) returned 2
    fibonacci(4,) returned 3
    fibonacci(4): 3

As you can see, with memoization we never do any unnecessary traversal of the
recursion tree. It's a simple journey - "down" and then "up".

### Profit!

Is it any good? Let's write a short benchmark:

    :::python
    # project.py
    import sys
    
    from functions import fibonacci, fib_cache

    start = time.time()

    for _ in range(0, 1000):
        fibonacci(int(sys.argv[1]))
        fib_cache.clear_cache()

    stop = time.time()

    print stop-start

Test it with different values, and decorated and undecorated version of 
_fibonacci_ function. My results are:

- for *n=5* the undecorated function calls take about _0.01s_ and decorated _0.03s_. 
The decorated vesion is acually *slower* if n is small.
- for *n=10* the undecorated function calls take about _0.1s_ and decorated _0.06s_.
Benefits of memoization start to become visible.
- for *n=20* the undecorated function calls take about _15.0s_ and decorated _0.1s_.
That's circa 100 times faster!

### Areas of application

I've titled this article *poor man's Memcached*. Well... If you feel you need 
Memcached, you probably need Memcached. Use Memcached for "persistent" cache.

Apart from scientific computations and recursive algorithms memoization as 
described in this article can be helpful during optimisation. Our _Cache()_ 
decorator allows us to "turn off" a costly function, or in other words to 
limit it's execution time almost to zero. Switching different functions on 
and off in some sort of testcase can show which parts of code are CPU hungry 
and should be optimized.

Happy (memoized) coding!

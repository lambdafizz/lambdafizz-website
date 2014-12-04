Title: Angular in Angular, or the great JS swindle.
Subtitle: Yo dawg! We put Angular in Angular, so you can $apply() while you $digest()!
Author: Karol Majta
Date: 2014-05-02 20:00 
Tags: Angular, Chrome, Plugin, Extension, JavaScript


Our teammates at [Tokenizer](http://tokenizer.com) did some nice work recently,
and I was able to do some really interesting stuff while building a Chrome
plugin that utilizes our platform.

Developing Chrome plugins really is a refreshing experience, thanks to
the great quality of APIs that are handled to you (kudos to Googlers,
great piece of work there!). It enforces good separation of concerns and
promotes passing lightweight messages between components over explicit
and tight coupling.

Let me shed some light on how Chrome plugins are structured, before I
explain in detail how we squeezed Angular into Angular. There is a
script called `background script` that in essence is a stateful JavaScript
application that runs independently of any webpages, can utilize
specialized APIs available only to extensions and should do everything
that is invisible to the user. There is a notion of `popup` or `popup script`
that's basically a webpage running inside a popup window instead of a
tab. And there is `content script` which, in simplest terms, is just a
bulk of JS code that gets concatenated with whatever is displayed in
browser tabs. All these components communicate passing simple JSON
objects as messages, and this communication is handled by native
Chrome code.

What we needed, was a safe way to use Angular inside content script.


## The world of pain

The problem with content script is that it gets injected (actually
just glued) to whatever is in the browser tab. This means your code
has to work properly even in presence of some other code, that you
know nothing about. Best solution? Keep it damn small and damn simple!

So we decided to use Angular for it...

I know this might sound crazy, but we have invested lots of work
porting some 3rd party libraries (mostly AES and RSA stuff from
CryptoJS and PidCrypt) into Angular modules and not reusing our
known, working and tested APIs seemed like too much of a waste.
We didn't need all the Angular goodies, just making the DI
work would be a win.


## Square pegs in round holes

Good news is, injecting Angular as contentscript *just works* as long
as the webpage in tab does not use Angular itself.

According to the docs it should be possible to run many instances of
Angular bootstrapped on different DOM elements with explicit call to
`angular.bootstrap`. Of course, great majority of sites never use this
method, preferring `ng-app` directive instead.

`ng-app` is a handy shortcut, but it's internal workings are actually
quite ugly, because it uses *import time side effects*. When you include
`angular.js` in your page's head it will implicitly bind to `document.ready`
event, and after it fires, will parse the whole DOM in search for `ng-app`.
When it finds one, it will pass the tagged element to `angular.bootstrap`.
Unfortunately, it will bind to the event as many times, as many times
`angular.js` script tag appears in your code. You can try this yourself.
Just duplicate the script tag, reload the page, and wait for the traceback
in console. Injecting Angular as content script is in essence exactly
same thing.

So, what we needed was a way of preventing angular from searching for `ng-app`
twice.


## If you can't beat 'em, join 'em

Fortunately you can use import time side-effecting code to your own good.
The content scripts get injected into the document in the exact order they
appear in `manifest.json`, so our declaration looked like this:

    :::javascript
    //
    // ...
    //

    "content_scripts" : [{
        "matches": [
            "http://*/*",
            "https://*/*"
        ],
        "js": [
              // declarations of angular independent libs like jquery etc.

              "before-angular.js", // see listing below

              "libs/angular/angular.js",

              // declaration of angular dependent libs like angular-local-storage

              "after-angular.js", // see listing below

              "contentscipt.js" // these are angular modules that deal with our business logic
                                // see listing below
        ],
        "css": [
            "assets/contentscript.css"
        ],
        "run_at": "document_end",
        "all_frames": false
    }]

    //
    // ...
    //

And the two files are:

    :::javascript
    // before-angular.js
    var oldReady = window.jQuery.fn.ready;
    window.jQuery.fn.ready = function () {};

And it's counterpart:

    :::javascript
    // after-angular.js
    window.jQuery.fn.ready = oldReady;

Yup, you're right. We use an ugly, stateful, side-effecting hack to prevent
angular from binding to `document.ready` for the second time. But `ng-app` is
an ugly, stateful, side-effecting hack itself, and it gets stuff done, just
like our code.

We regret nothing...


## When in doubt... guess

All righty, we were able to prevent Angular from automatically calling `bootstrap`
for the second time but we still need to call it ourselves. `bootstrap` takes a
DOM element as first argument, but most pages put `ng-app` in their `html` or
`body` tag so the number of elements that are outside of scope of the "previous"
Angular is close to zero.

This is when I decided to feed it with `null` and see what happens. So the
`contentscript.js` looks somewhat like this.

    :::javascript
    angular.module('you.name.it',
        ['dependency.one', 'dependencyTwo'])

    .constant('PI', Math.PI)
    .service('SomeService', ['$log', 'PI', function ($log, PI) {
        this.sayPi = function () { $log.info('PI is ' + PI); }
    }])
    .run([function () {
        // we put lots and lots of ugly and imperative code here
        // don't do it, and when you do, don't cry
    }]);

    // this is what bootstraps "our" Angular
    angular.element(document).ready(function() {
        angular.bootstrap(null, ['you.name.it']);
    });


## 90 percent of the time works all the time

As you can see, our "solution" (or hack, whatever, I don't mind) is dead simple
and quite ugly, but it's amazing what can be squeezed out of it. Bear in mind that
all it consists of is one stubbed function and `null` passed as root element to
`angular.bootstrap`.

Things that work are:

- **Dependency injection of services.** You can both declare new services
  and consume other.
- **Digest cycle.** Calls to `$rootScope.$apply` take desired effect.
  Promises work as expected.
- **Some directives.** We managed to append some html to body and it gets
  compiled and directives do work (*sic! with null root element*). We just
  had to manually compile the template string and link it with `$rootScope`.
- **Works when angular app is already present on the page (yay!)**

Things that break:

- Seems to break on some Google's applications (it seems it can have something
  to do with apps that use *Google Closure Compiler*). I have no clue why,
  but it manifests in URL routing either totally broken, or working in unexpected
  ways.


## Don't try this at home kids

While it works for us, I do realize that it's not the cleanest piece of code
ever. This is why, if you're following this path, expect the worst. You've been
warned. Stay tuned for some more news on browser plugin development with Angular
(Firefox related stuff is on it's way).

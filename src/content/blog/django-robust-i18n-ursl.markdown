Title: Robust internationalized URLs for Django
Subtitle: It's a plane! It's a bug! It's a feature... and all the joys of i18n.
Author: Karol Majta
Date: 2014-02-12 20:00 
Tags: Python, Django, i18n, i18n, internationalization, url

Ah... internationalization! Everytime someone drops the *i18n bomb*
you know you'll enter the world of pain. While Django provides some
reasonable support for translation of content, and third party apps
do some really neat work with per-instance translations (check out
[django-modeltranslation](https://django-modeltranslation.readthedocs.org/en/latest/),
a pretty awesome piece of work!), there is one thing that is really
lacking proper support. I am talking internationalized urls.

## Welcome to the purgatory

Django's support for multilingual URLs is not really a *hell*. It looks
rather like a *purgatory*. All the helpers and features are there, and
they are not broken. Yet, they work in such nonsensical way that you will
probably wonder if they are there to aid you or to confuse you. I'll get
back to this later, now let's just focus on one simple case.

## Meet Pablo

Pablo lives in Spain, and he want's his portfolio to be available in
Spanish, British English and American English. Sounds like a breeze,
right? So let's look at some important snippets from his project. He
tries to follow the documentation strictly, so there's no magic here.

His `urls.py` is quite simple, he has only one template view, and default
Django's `set_language` view.

    :::python
    from django.conf.urls import patterns, url, include, i18n
    from django.utils.translation import ugettext_lazy as _
    from django.views.generic import TemplateView

    urlpatterns = patterns('',
        url(
            _(r'^hello/$'), TemplateView.as_view(template_name='hello.html'),
            name='hello'
        ),
        url('^i18n/setlang/', set_language, name='set_language'),
    )

His template is also very simple, it will just presetn a simple greeting
and submit buttons with available language:

    :::html
    {% load i18n %}
    <html>
        <div id="greeting">
            {% trans 'Hi there folks!'  %}
        </div>
        <div id="language-select">
            {% get_language_info_list for LANGUAGES as languages %}
            {% for language in languages %}
                <form action="{% url 'set_language' %}" method="post">
                    {% csrf_token %}
                    <input name="language" type="hidden" value="{{ language.code }}" />
                    <input type="submit"
                           value="{{ language.code|upper }}"
                           class="btn-link{% if language.code == LANGUAGE_CODE %} current{% endif %}" />
                </form>
            {% endfor %}
        </div>
    <html>

Now, after hiring a translator for a dreadful hourly wage Pablo's site presents
diffetent content to users based on ther `Accept-Language` header and selected
url. At **/hello/** all Americans will see the default greeting, only posh Brits
will get *Good day, sir*. Spanish amigos can visit **/ola/** to get *Ola Amigo!*.

## Meet Brian

Pablo has a friend, Brian, and he decided to share a link with him, so he emailed
him the **/ola/** link...

Well, bad luck Brian (yeah, I know that's well played)! Your browser sends
`Accept-Language` headers that tell Django to resolve this url in context of
English locale, which means you'll get a nasty 404.

That's unfortunate. There is absolutely no reason, why users should be unable
to share internationalized links. While Python Zen says *In the face of
ambiguity, refuse the temptation to guess*, I say *If you can show your user
a webpage isntead of rubbing an error in his face, you should probably
go for it*. This is why I created this middleware (more or less inspired by
the flatpages middleware, that in case of 404 status code just tries to
resolve request path as a flatpage link). `RobustI18nLocaleMiddleware` does
similar thing. When it detects that response has status *not found* it will
go through all the languages hoping it can resolve it in different locale
context. Let's look at the code:

    :::python
    from django.conf import settings
    from django.core.urlresolvers import get_resolver
    from django.utils import translation

    from robust_urls.utils import try_url_for_language

    class RobustI18nLocaleMiddleware(object):
       """
       If `response.status_code == 404` this middleware makes sure to
       check request.path resolution in contex of all languages present
       in `settings.Languages`. If resolution succeeds a proper page will
       be returned instead. If resolution fails nothing happens.
       """
    
       def process_response(self, request, response):
           """
           If request status code is other than 404, just return provided response.
           If request status code is 404:
             - if request.path can be resolved in context of a language from
              `settings.Languages`, call `handle_successful_match` and return it's
              result
             - if request.path cannot be resolved in context of a language from
              `settings.Languages` return provided response.
           """
           if response.status_code == 404:
               all_languages =  [i[0] for i in settings.LANGUAGES]
               resolver = get_resolver(None)
               for language in all_languages:
                   match = try_url_for_language(request.path, language, resolver)
                   if match is not None:
                       return self.handle_successful_match(
                           request,
                           response,
                           match[0],
                           match[1],
                           match[2],
                           language
                       )
               return response
           else:
               return response
    
       def handle_successful_match(self, request, response,  view, args, kwargs, language):
           """
           In order make sure to:
             - store the matched language in users session or cookie
             - render response from matched view (in context of matched language) and
               return it.
           """
           # this is copypasted from django's i18n.py view
           if hasattr(request, 'session'):
               request.session['django_language'] = language
           else:
               response.set_cookie(settings.LANGUAGE_COOKIE_NAME, language)
           # we shall activate translation during response rendering
           # i am not sure if this is a necessity, but it's surely not stupid
           # to do so
           translation.activate(language)
           resp = view(request, *args, **kwargs)
           resp.render()
           translation.deactivate()
           return resp

That seems to solve it! Now anyone accessing **/ola/** url will see a Spanish
version, anyone accessing */hello/* will get Ametican greeting, except for the
British, because theri `Accept-Language` will kick in, and give them their own
translation. Neat.

Unfortunately there is one more subtle bug. After clicking on a submit button
that is supposed to change the language we get back to the side we started,
and the language remains unchanged. It's not our new middleware that broke stuff.
If you [look at the source code](https://github.com/django/django/blob/master/django/views/i18n.py)
it gets clearer. If no **next** parameter is present in `REQUEST` will use
the `Referer` header to issue a redirection, but the language is already changed,
so `RobustI18nLocaleMiddleware` kicks in changing it back. Without the middleware
we would get 404. Either way, it's kind of broken. This is why we need a custom
version of the `set_language` view:

	:::python
	import urlparse

	from django.core.urlresolvers import get_resolver, reverse
	from django.utils.http import is_safe_url
	from django.utils.translation import get_language, check_for_language

	from robust_urls.utils import try_url_for_language, locale_context
	from django import http
	from django.conf import settings

	def set_language(request):
		"""
		Redirect to a given url, reversed while setting the chosen language in the
		session or cookie. The url and the language code need to be
		specified in the request parameters.

		Since this view changes how the user will see the rest of the site, it must
		only be accessed as a POST request.
		"""
		
		if request.method == 'POST':
			# get necessary values from request
			language = request.POST.get('language', None)
			next_path = request.REQUEST.get('next', '')
			# django safety checks... 
			if not is_safe_url(url=next_path, host=request.get_host()):
				referer = request.META.get('HTTP_REFERER', '')
				next_path = urlparse(referer).path
				if not is_safe_url(url=next_path, host=request.get_host):
					next_path = '/'
			
			# check if given url is found using current locale
			resolver = get_resolver(None)
			resolve_result = try_url_for_language(next_path, get_language(), resolver)
			if resolve_result is None:
				# we didn't succeed at resolving the url with current locale, so
				# we may as well redirect to given url, and it will just be a 404
				redirect_to = next_path
			else:
				# we did succeed, this means the route exists and we can get view's
				# name, expected args and kwargs
				url_name = resolve_result.url_name
				view_args = resolve_result[1]
				view_kwargs = resolve_result[2]
				with locale_context(language):
					redirect_to = reverse(url_name, args=view_args, kwargs=view_kwargs)
				
			# this is standard django stuff again...
			response = http.HttpResponseRedirect(redirect_to)
			if language and check_for_language(language):
				if hasattr(request, 'session'):
					request.session['django_language'] = language
				else:
					response.set_cookie(settings.LANGUAGE_COOKIE_NAME, language)
			return response
		else:
			return http.HttpResponseNotAllowed(['POST',])

This middleware does almost the same thing, but instead of blindly redirecting
it tries to build the target url in context of newly selected language.

Armed with both custom middleware and new version of `set_language` we can
finally say that our URLs work the way they should.

## There's no easy way out

Internationalization itself is a difficult topic, but URL internationalization
can be really tough and definately did not get enough attention. If you liked
the described solution feel free to use
[django-robust-i18n-urls](https://github.com/karolmajta/django-robust-i18n-urls)
that was made to provide presented features.

You may also try
[django-solid-i18n-urls](https://github.com/st4lk/django-solid-i18n-urls)
which is a different beast, but it may also scratch your itch if you're dealing
with URL translation problems.

import os
from functools import partial

from flask import Flask, request, render_template
from flask.ext.babel import Babel

from routes import Router
from blog import BlogPostReader, BlogPostSet

application = Flask(__name__)
application.config['BABEL_DEFAULT_LOCALE'] = os.environ.get('BABEL_DEFAULT_LOCALE', 'en')
application.config['FREEZER_DESTINATION'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'build')
blogposts_dir = os.path.join(os.path.dirname(__file__), os.path.join('content', 'blog'))
Babel(application)
router = Router(application, application.config['BABEL_DEFAULT_LOCALE'])

markdown_files = map(partial(os.path.join, blogposts_dir), os.listdir(blogposts_dir))
blogpost_reader = BlogPostReader(markdown_files)
blogposts = BlogPostSet(blogpost_reader)


# Static page related stuff

@router.route('index')
def index():
    return render_template(os.path.join('pages', request.url_rule.endpoint) + '.html')

@router.route('about-us')
def about():
    return render_template(os.path.join('pages', request.url_rule.endpoint) + '.html')


@router.route('contact-us')
def contact():
    return render_template(os.path.join('pages', request.url_rule.endpoint) + '.html')


# Blog related stuff

@router.route('latest-blog-post')
def blog():
    current = blogposts.latest()
    next = blogposts.next(current)
    previous = blogposts.previous(current)
    return render_template('blog/blogpost.html', **locals())


@router.route('blog-post')
def blog(slug):
    current = blogposts.get(slug)
    next = blogposts.next(current)
    previous = blogposts.previous(current)
    return render_template('blog/blogpost.html', **locals())



if __name__ == '__main__':
    application.run(debug=True)
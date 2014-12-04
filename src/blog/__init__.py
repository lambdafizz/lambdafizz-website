import os
from itertools import dropwhile

import markdown
import iso8601


class BlogPostReader(object):

    def __init__(self, filepaths):
        self.filepaths = filepaths
        self.extensions = [
            'markdown.extensions.meta'
        ]

    def __iter__(self):
        for filepath in self.filepaths:
            yield self._read_as_blogpost(filepath)

    def _read_as_blogpost(self, filepath):
        with open(filepath, 'r') as f:
            contents = f.read()
        md = markdown.Markdown(extensions=self.extensions)
        html = md.convert(contents)
        meta = md.Meta
        default_slug = os.path.basename(filepath).split('.')[0]
        return BlogPost(html, meta, default_slug)


class BlogPost(object):

    def __init__(self, html, meta, default_slug):
        self.html = html
        self.slug = meta.get('slug')[0] if 'slug' in meta else default_slug
        self.date = iso8601.parse_date(meta.get('date')[0]).date()
        self.authors = [self._author_tuple(a) for a in meta.get('authors', [])]

    def _author_tuple(self, s):
        chunks = s.split(',')
        full_name = chunks[0].strip()
        slug = full_name.lower().replace(' ', '-') if len(chunks) == 1 else chunks[1].strip().lower.replace(' ', '-')
        return full_name, slug, False  # third item in tuple is 'exists' flag


class BlogPostSet(object):

    def __init__(self, blogpost_iterable):
        self.d = {}
        for blogpost in blogpost_iterable:
            if blogpost.slug in self.d:
                assert False  # TODO
            self.d[blogpost.slug] = blogpost
        self.l = sorted(self.d.values(), key=lambda p: p.date, reverse=True)

    def get(self, slug):
        return self.d.get(slug, None)

    def latest(self):
        try:
            return self.l[0]
        except IndexError:
            return None

    def previous(self, b):
        try:
            return list(dropwhile(lambda x: x.slug != b.slug, self.l))[1]
        except IndexError:
            return None

    def next(self, b):
        try:
            return list(dropwhile(lambda x: x.slug != b.slug, reversed(self.l)))[1]
        except IndexError:
            return None

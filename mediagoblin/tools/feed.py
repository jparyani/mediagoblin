# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011 MediaGoblin contributors.  See AUTHORS.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from lxml import etree
from lxml.builder import ElementMaker
from werkzeug.wrappers import BaseResponse

import datetime

"""
    Feed engine written for GNU MediaGoblin,
    based on werkzeug atom feeds tool (werkzeug.contrib.atom)

    The feed library contains two types of classes:
        - Entities that contains the feed data.
        - Generators that are injected to the above classes and are able to
            generate feeds in a specific format. An atom feed genearator is
            provided, but others could be written as well.

    The Werkzeurg library interface have been mimetized, so the replacement can
    be done with only switching the import call.

    Example::

        def atom_feed(request):
            feed = AtomFeed("My Blog", feed_url=request.url,
                            url=request.host_url,
                            subtitle="My example blog for a feed test.")
            for post in Post.query.limit(10).all():
                feed.add(post.title, post.body, content_type='html',
                         author=post.author, url=post.url, id=post.uid,
                         updated=post.last_update, published=post.pub_date)
            return feed.get_response()
"""


##
# Class FeedGenerator
#
class FeedGenerator(object):
    def __init__(self):
        pass

    def format_iso8601(self, obj):
        """Format a datetime object for iso8601"""
        return obj.strftime('%Y-%m-%dT%H:%M:%SZ')


##
# Class AtomGenerator
#
class AtomGenerator(FeedGenerator):
    """ Generator that generate feeds in Atom format """
    NAMESPACE = "http://www.w3.org/2005/Atom"

    def __init__(self):
        pass

    def generate(self, data):
        """Return an XML tree representation."""
        if isinstance(data, AtomFeed):
            return self.generate_feed(data)
        elif isinstance(data, FeedEntry):
            return self.generate_feedEntry(data)

    def generate_text_block(self, name, content, content_type=None):
        """Helper method for the builder that creates an XML text block."""
        root = etree.Element(name)

        if content_type:
            root.set('type', content_type)

        if content_type == 'xhtml':
            div_ele = etree.Element('div')
            div_ele.set('xmlns', XHTML_NAMESPACE)
            div_ele.text = content
            root.append(div_ele)
        else:
            root.text = content

        return root

    def generate_feed(self, data):
        """Return an XML tree representation of the feed."""
        NSMAP = {None: self.NAMESPACE}
        root = etree.Element("feed", nsmap=NSMAP)

        E = ElementMaker()

        # atom demands either an author element in every entry or a global one
        if not data.author:
            if False in map(lambda e: bool(e.author), data.entries):
                data.author = ({'name': 'Unknown author'},)

        if not data.updated:
            dates = sorted([entry.updated for entry in data.entries])
            data.updated = dates and dates[-1] or datetime.utcnow()

        title_ele = self.generate_text_block(
            'title',
            data.title,
            data.title_type)
        root.append(title_ele)

        root.append(E.id(data.id))
        root.append(E.updated(self.format_iso8601(data.updated)))

        if data.url:
            link_ele = etree.Element("link")
            link_ele.set("href", data.url)
            root.append(link_ele)

        if data.feed_url:
            link_ele = etree.Element("link")
            link_ele.set("href", data.feed_url)
            link_ele.set("rel", "self")
            root.append(link_ele)

        for link in data.links:
            link_ele = etree.Element("link")
            for name, value in link.items():
                link_ele.set(name, value)
            root.append(link_ele)

        for author in data.author:
            author_element = etree.Element("author")
            author_element.append(E.name(author['name']))
            if 'uri' in author:
                author_element.append(E.name(author['uri']))
            if 'email' in author:
                author_element.append(E.name(author['email']))

            root.append(author_element)

        if data.subtitle:
            root.append(self.generate_text_block('subtitle', data.subtitle,
                                                    data.subtitle_type))
        if data.icon:
            root.append(E.icon(data.icon))

        if data.logo:
            root.append(E.logo(data.logo))

        if data.rights:
            root.append(self.generate_text_block('rights', data.rights,
                                                    data.rights_type))

        generator_name, generator_url, generator_version = data.generator
        if generator_name or generator_url or generator_version:
            generator_ele = etree.Element("generator")
            if generator_url:
                generator_ele.set("uri", generator_url, True)
            if generator_version:
                generator_ele.set("version", generator_version)

            generator_ele.text = generator_name

            root.append(generator_ele)

        for entry in data.entries:
            root.append(entry.generate())

        return root

    def generate_feedEntry(self, data):
        """Return an XML tree representation of the feed entry."""
        E = ElementMaker()
        root = etree.Element("entry")

        if data.xml_base:
            root.base = data.xml_base

        title_ele = self.generate_text_block(
            'title',
            data.title,
            data.title_type)
        root.append(title_ele)

        root.append(E.id(data.id))
        root.append(E.updated(self.format_iso8601(data.updated)))

        if data.published:
            root.append(E.published(self.format_iso8601(data.published)))

        if data.url:
            link_ele = etree.Element("link")
            link_ele.set("href", data.url)
            root.append(link_ele)

        for author in data.author:
            author_element = etree.Element("author")
            author_element.append(E.name(author['name']))
            if 'uri' in author:
                author_element.append(E.name(author['uri']))
            if 'email' in author:
                author_element.append(E.name(author['email']))

            root.append(author_element)

        for link in data.links:
            link_ele = etree.Element("link")
            for name, value in link.items():
                link_ele.set(name, value)
            root.append(link_ele)

        print data.thumbnail

        if data.thumbnail:
            namespace = "http://search.yahoo.com/mrss/"
            nsmap = {"media": namespace}
            thumbnail_ele = etree.Element(
                "{http://search.yahoo.com/mrss/}thumbnail", nsmap=nsmap)
            thumbnail_ele.set("url", data.thumbnail)

            root.append(thumbnail_ele)

        if data.summary:
            summary_ele = self.generate_text_block('summary', data.summary,
                data.summary_type)
            root.append(summary_ele)

        if data.content:
            content = data.content

            if data.thumbnail:
                thumbnail_html = etree.Element("img")
                thumbnail_html.set("src", data.thumbnail)
                content = etree.tostring(thumbnail_html) + content

            content_ele = self.generate_text_block('content', content,
                data.content_type)
            root.append(content_ele)

        for name, value in data.custom.items():
            element = etree.Element(name)
            element.text = value
            root.append(element)

        return root


##
# Class AtomFeed
#
class AtomFeed(object):
    """
    A helper class that contains feeds. By default, it uses the AtomGenerator
    but others could be injected. It has the AtomFeed name to keep the name
    it had on werkzeug library

    Following Werkzeurg implementation, the constructor takes a lot of
    parameters. As an addition, the class will also store custom parameters for
    fields not explicitly supported by the library.

    :param feed_generator: The generator that will be used to generate the feed
                            defaults to AtomGenerator
    :param title: the title of the feed. Required.
    :param title_type: the type attribute for the title element.  One of
                       ``'html'``, ``'text'`` or ``'xhtml'``.
    :param url: the url for the feed (not the url *of* the feed)
    :param id: a globally unique id for the feed.  Must be an URI.  If
               not present the `feed_url` is used, but one of both is
               required.
    :param updated: the time the feed was modified the last time.  Must
                    be a :class:`datetime.datetime` object.  If not
                    present the latest entry's `updated` is used.
    :param feed_url: the URL to the feed.  Should be the URL that was
                     requested.
    :param author: the author of the feed.  Must be either a string (the
                   name) or a dict with name (required) and uri or
                   email (both optional).  Can be a list of (may be
                   mixed, too) strings and dicts, too, if there are
                   multiple authors. Required if not every entry has an
                   author element.
    :param icon: an icon for the feed.
    :param logo: a logo for the feed.
    :param rights: copyright information for the feed.
    :param rights_type: the type attribute for the rights element.  One of
                        ``'html'``, ``'text'`` or ``'xhtml'``.  Default is
                        ``'text'``.
    :param subtitle: a short description of the feed.
    :param subtitle_type: the type attribute for the subtitle element.
                          One of ``'text'``, ``'html'``, ``'text'``
                          or ``'xhtml'``.  Default is ``'text'``.
    :param links: additional links.  Must be a list of dictionaries with
                  href (required) and rel, type, hreflang, title, length
                  (all optional)
    :param generator: the software that generated this feed.  This must be
                      a tuple in the form ``(name, url, version)``.  If
                      you don't want to specify one of them, set the item
                      to `None`.
    :param entries: a list with the entries for the feed. Entries can also
                    be added later with :meth:`add`.

    For more information on the elements see
    http://www.atomenabled.org/developers/syndication/

    Everywhere where a list is demanded, any iterable can be used.
    """

    default_generator = ('GNU Mediagoblin', None, None)
    default_feed_generator = AtomGenerator()

    def __init__(self, title=None, entries=None, feed_generator=None,
                 **kwargs):
        self.feed_generator = feed_generator
        self.title = title
        self.title_type = kwargs.get('title_type', 'text')
        self.url = kwargs.get('url')
        self.feed_url = kwargs.get('feed_url', self.url)
        self.id = kwargs.get('id', self.feed_url)
        self.updated = kwargs.get('updated')
        self.author = kwargs.get('author', ())
        self.icon = kwargs.get('icon')
        self.logo = kwargs.get('logo')
        self.rights = kwargs.get('rights')
        self.rights_type = kwargs.get('rights_type')
        self.subtitle = kwargs.get('subtitle')
        self.subtitle_type = kwargs.get('subtitle_type', 'text')
        self.generator = kwargs.get('generator')
        if self.generator is None:
            self.generator = self.default_generator
        self.links = kwargs.get('links', [])
        self.entries = entries and list(entries) or []

        if not hasattr(self.author, '__iter__') \
           or isinstance(self.author, (basestring, dict)):
            self.author = [self.author]
        for i, author in enumerate(self.author):
            if not isinstance(author, dict):
                self.author[i] = {'name': author}

        if not self.feed_generator:
            self.feed_generator = self.default_feed_generator
        if not self.title:
            raise ValueError('title is required')
        if not self.id:
            raise ValueError('id is required')
        for author in self.author:
            if 'name' not in author:
                raise TypeError('author must contain at least a name')

        # Look for arguments that we haven't matched with object members.
        # They will be added to the custom dictionary.
        # This way we can have custom fields not specified in this class.
        self.custom = {}
        properties = dir(self)

        for name, value in kwargs.items():
            if (properties.count(name) == 0):
                self.custom[name] = value

    def add(self, *args, **kwargs):
        """Add a new entry to the feed.  This function can either be called
        with a :class:`FeedEntry` or some keyword and positional arguments
        that are forwarded to the :class:`FeedEntry` constructor.
        """
        if len(args) == 1 and not kwargs and isinstance(args[0], FeedEntry):
            args[0].generator = self.generator
            self.entries.append(args[0])
        else:
            kwargs['feed_url'] = self.feed_url
            self.entries.append(FeedEntry(feed_generator=self.feed_generator, 
                                            *args, **kwargs))

    def __repr__(self):
        return '<%s %r (%d entries)>' % (
            self.__class__.__name__,
            self.title,
            len(self.entries)
        )

    def generate(self):
        """Return an XML tree representation of the feed."""
        return self.feed_generator.generate(self)

    def to_string(self):
        """Convert the feed into a string."""
        return etree.tostring(self.generate(), encoding='UTF-8')

    def get_response(self):
        """Return a response object for the feed."""
        return BaseResponse(self.to_string(), mimetype='application/atom+xml')

    def __call__(self, environ, start_response):
        """Use the class as WSGI response object."""
        return self.get_response()(environ, start_response)

    def __unicode__(self):
        return self.to_string()

    def __str__(self):
        return self.to_string().encode('utf-8')


##
# Class FeedEntry
#
class FeedEntry(object):
    """Represents a single entry in a feed.
        
    Following Werkzeurg implementation, the constructor takes a lot of 
    parameters. As an addition, the class will also store custom parameters for
    fields not explicitly supported by the library.

    :param feed_generator: The generator that will be used to generate the feed.
                            defaults to AtomGenerator
    :param title: the title of the entry. Required.
    :param title_type: the type attribute for the title element.  One of
                       ``'html'``, ``'text'`` or ``'xhtml'``.
    :param content: the content of the entry.
    :param content_type: the type attribute for the content element.  One
                         of ``'html'``, ``'text'`` or ``'xhtml'``.
    :param summary: a summary of the entry's content.
    :param summary_type: the type attribute for the summary element.  One
                         of ``'html'``, ``'text'`` or ``'xhtml'``.
    :param url: the url for the entry.
    :param id: a globally unique id for the entry.  Must be an URI.  If
               not present the URL is used, but one of both is required.
    :param updated: the time the entry was modified the last time.  Must
                    be a :class:`datetime.datetime` object. Required.
    :param author: the author of the feed.  Must be either a string (the
                   name) or a dict with name (required) and uri or
                   email (both optional).  Can be a list of (may be
                   mixed, too) strings and dicts, too, if there are
                   multiple authors. Required if not every entry has an
                   author element.
    :param published: the time the entry was initially published.  Must
                      be a :class:`datetime.datetime` object.
    :param rights: copyright information for the entry.
    :param rights_type: the type attribute for the rights element.  One of
                        ``'html'``, ``'text'`` or ``'xhtml'``.  Default is
                        ``'text'``.
    :param links: additional links.  Must be a list of dictionaries with
                  href (required) and rel, type, hreflang, title, length
                  (all optional)
    :param xml_base: The xml base (url) for this feed item.  If not provided
                     it will default to the item url.

    For more information on the elements see
    http://www.atomenabled.org/developers/syndication/

    Everywhere where a list is demanded, any iterable can be used.
    """
    
    default_feed_generator = AtomGenerator()

    def __init__(self, title=None, content=None, feed_url=None, 
                    feed_generator=None, **kwargs):
        self.feed_generator = feed_generator
        self.title = title
        self.title_type = kwargs.get('title_type', 'text')
        self.content = content
        self.content_type = kwargs.get('content_type', 'html')
        self.url = kwargs.get('url')
        self.id = kwargs.get('id', self.url)
        self.updated = kwargs.get('updated')
        self.summary = kwargs.get('summary')
        self.summary_type = kwargs.get('summary_type', 'html')
        self.author = kwargs.get('author')
        self.published = kwargs.get('published')
        self.rights = kwargs.get('rights')
        self.links = kwargs.get('links', [])
        self.xml_base = kwargs.get('xml_base', feed_url)
        self.thumbnail = kwargs.get('thumbnail')


        if not hasattr(self.author, '__iter__') \
           or isinstance(self.author, (basestring, dict)):
            self.author = [self.author]
        for i, author in enumerate(self.author):
            if not isinstance(author, dict):
                self.author[i] = {'name': author}

        if not self.feed_generator:
            self.feed_generator = self.default_feed_generator
        if not self.title:
            raise ValueError('title is required')
        if not self.id:
            raise ValueError('id is required')
        if not self.updated:
            raise ValueError('updated is required')
            
        # Look for arguments that we haven't matched with object members.
        # They will be added to the custom dictionary.
        # This way we can have custom fields not specified in this class.
        self.custom = {}
        properties = dir(self)
        
        for name, value in kwargs.items():
            if ( properties.count(name) == 0 ):
                self.custom[name] = value
        

    def __repr__(self):
        return '<%s %r>' % (
            self.__class__.__name__,
            self.title
        )
        
    def generate(self):
        """Returns lxml element tree representation of the feed entry"""
        return self.feed_generator.generate(self)

    def to_string(self):
        """Convert the feed item into a unicode object."""
        return etree.tostring(self.generate(), encoding='utf-8')        

    def __unicode__(self):
        return self.to_string()

    def __str__(self):
        return self.to_string().encode('utf-8')



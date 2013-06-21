# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011, 2012 MediaGoblin contributors.  See AUTHORS.
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

import wtforms
import markdown
from lxml.html.clean import Cleaner

from mediagoblin import mg_globals
from mediagoblin.tools import url


# A super strict version of the lxml.html cleaner class
HTML_CLEANER = Cleaner(
    scripts=True,
    javascript=True,
    comments=True,
    style=True,
    links=True,
    page_structure=True,
    processing_instructions=True,
    embedded=True,
    frames=True,
    forms=True,
    annoying_tags=True,
    allow_tags=[
        'div', 'b', 'i', 'em', 'strong', 'p', 'ul', 'ol', 'li', 'a', 'br',
        'pre', 'code'],
    remove_unknown_tags=False,  # can't be used with allow_tags
    safe_attrs_only=True,
    add_nofollow=True,  # for now
    host_whitelist=(),
    whitelist_tags=set([]))


def clean_html(html):
    # clean_html barfs on an empty string
    if not html:
        return u''

    return HTML_CLEANER.clean_html(html)


def convert_to_tag_list_of_dicts(tag_string):
    """
    Filter input from incoming string containing user tags,

    Strips trailing, leading, and internal whitespace, and also converts
    the "tags" text into an array of tags
    """
    taglist = []
    if tag_string:

        # Strip out internal, trailing, and leading whitespace
        stripped_tag_string = u' '.join(tag_string.strip().split())

        # Split the tag string into a list of tags
        for tag in stripped_tag_string.split(','):
            tag = tag.strip()
            # Ignore empty or duplicate tags
            if tag and tag not in [t['name'] for t in taglist]:
                taglist.append({'name': tag,
                                'slug': url.slugify(tag)})
    return taglist


def media_tags_as_string(media_entry_tags):
    """
    Generate a string from a media item's tags, stored as a list of dicts

    This is the opposite of convert_to_tag_list_of_dicts
    """
    tags_string = ''
    if media_entry_tags:
        tags_string = u', '.join([tag['name'] for tag in media_entry_tags])
    return tags_string


TOO_LONG_TAG_WARNING = \
    u'Tags must be shorter than %s characters.  Tags that are too long: %s'


def tag_length_validator(form, field):
    """
    Make sure tags do not exceed the maximum tag length.
    """
    tags = convert_to_tag_list_of_dicts(field.data)
    too_long_tags = [
        tag['name'] for tag in tags
        if len(tag['name']) > mg_globals.app_config['tags_max_length']]

    if too_long_tags:
        raise wtforms.ValidationError(
            TOO_LONG_TAG_WARNING % (mg_globals.app_config['tags_max_length'],
                                    ', '.join(too_long_tags)))


# Don't use the safe mode, because lxml.html.clean is better and we are using
# it anyway
UNSAFE_MARKDOWN_INSTANCE = markdown.Markdown()


def cleaned_markdown_conversion(text):
    """
    Take a block of text, run it through MarkDown, and clean its HTML.
    """
    # Markdown will do nothing with and clean_html can do nothing with
    # an empty string :)
    if not text:
        return u''

    return clean_html(UNSAFE_MARKDOWN_INSTANCE.convert(text))

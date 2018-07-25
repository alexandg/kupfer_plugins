# Copyright (C) 2018 Geoffrey Alexander <geoff.i.alexander@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# TODO Support replacing other fields besides {searchTerms}
# TODO Support POST based search engines

# This plugin is heavily based/borrows from the firefox keyword search
# plugin included in kupfer by default.
#
# NOTE: Requires Firefox 45+
__kupfer_name__ = _("Firefox Search Plugins")
__kupfer_actions__ = ("FFSearchWithEngine", )
__kupfer_sources__ = ("FFSearchSource", )
__description__ = _("Search using Firefox search plugins")
__version__ = "0.2"
__author__ = "Geoffrey Alexander <geoff.i.alexander@gmail.com>"
from kupfer.objects import Action, Leaf, Source, TextLeaf, TextSource
from kupfer.obj.helplib import FilesystemWatchMixin
from kupfer import utils

from urllib.parse import quote
import configparser
import json
import lz4
import os


MAGIC = b"mozLz40\0"


def is_param_url(url):
    if "params" in url:
        fs = [f["value"] for f in url["params"]]
        return "{searchTerms}" in fs
    return False


def build_url_from_params(url):
    params = []
    for param in url["params"]:
        if "purpose" not in param:
            params.append("{}={}".format(param["name"], param["value"]))
    return "{}?{}".format(url["template"], "&".join(params))


def get_url_type(url):
    return None if "type" not in url else url["type"]


def is_simple_template(engine):
    url = None
    if "template" in engine:
        url = engine["template"]
    return "{searchTerms}" in url


def get_default_profile_dir():
    """Based on Kupfer Firefox Search Keywords plugin"""
    ff_dir = os.path.expanduser("~/.mozilla/firefox")
    if not os.path.exists(ff_dir):
        return None

    config = configparser.ConfigParser()
    config.read(os.path.join(ff_dir, "profiles.ini"))
    default_section = None
    for section in config.sections():
        if "Default" in config[section] and config[section]["Default"] == '1':
            default_section = config[section]
            break
    if default_section is None:
        return None

    if "Path" in default_section and "IsRelative" in default_section:
        if default_section["IsRelative"] == '1':
            return os.path.join(ff_dir, default_section["Path"])
        else:
            return os.path(default_section["Path"])

    return None


def get_search_json(profile_dir):
    search_path = os.path.join(profile_dir, "search.json.mozlz4")
    searchers = None
    with open(search_path, "rb") as infile:
        if infile.read(len(MAGIC)) != MAGIC:
            return None
        searchers = json.loads(lz4.frame.decompress(infile.read()))
    return searchers


def get_engine_url(engine):
    urls = [url for url in engine["_urls"] if get_url_type(url) is None]
    if len(urls) > 0:
        return urls[0]
    else:
        return None


def search_engines_from_json(sjson):
    engines = sjson["engines"]
    return [(e["_name"], e["description"], get_engine_url(e)) for e in engines]


class SearchFor(Action):
    """Keyword -> SearchFor -> Text"""

    def __init__(self):
        Action.__init__(self, _("Search for..."))

    def activate(self, leaf, iobj):
        url = leaf.object
        terms = iobj.object
        query = url.replace("{searchTerms}", quote(terms))
        utils.show_url(query)

    def item_types(self):
        yield SearchEngine

    def requires_object(self):
        return True

    def object_types(self):
        yield TextLeaf

    def object_source(self, for_item):
        return TextSource(placeholder=_("Search terms"))

    def valid_object(self, obj, for_item):
        return type(obj) == TextLeaf

    def get_description(self):
        return _("Search using Firefox search plugin")

    def get_icon_name(self):
        return "edit-find"


class FFSearchWithEngine(Action):
    """Text -> Self -> Keyword"""

    def __init__(self):
        Action.__init__(self, _("Search with..."))

    def activate(self, leaf, iobj):
        url = iobj.object
        query = url.replace("{searchTerms}", quote(leaf.object))
        utils.show_url(query)

    def item_types(self):
        yield TextLeaf

    def requires_object(self):
        return True

    def object_types(self):
        yield SearchEngine

    def valid_object(self, obj, for_item):
        return type(obj) == SearchEngine

    def object_source(self, for_item=None):
        return FFSearchSource()

    def get_description(self):
        return _("Search using Firefox search plugin")

    def get_icon_name(self):
        return "edit-find"


class SearchEngine(Leaf):
    def __init__(self, title, desc, url):
        if is_param_url(url):
            url = build_url_from_params(url)
        else:
            url = url["template"]

        super().__init__(url, title)
        self.title = title
        self.description = desc
        self.url = url

    def get_actions(self):
        yield SearchFor()

    def get_description(self):
        return self.description

    def get_icon_name(self):
        return "text-html"

    def get_text_representation(self):
        return self.title


class FFSearchSource(Source, FilesystemWatchMixin):
    def __init__(self):
        super().__init__(_("Firefox Search Engines"))

    def initialize(self):
        self.ff_dir = get_default_profile_dir()
        self.monitor_token = self.monitor_directories(self.ff_dir)

    def get_description(self):
        return None

    def get_icon_name(self):
        return "web-browser"

    def provides(self):
        yield SearchEngine

    def get_items(self):
        engines = search_engines_from_json(get_search_json(self.ff_dir))
        return [SearchEngine(name, desc, url) for (name, desc, url) in engines]

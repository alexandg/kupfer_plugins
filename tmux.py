# Copyright (C) 2017 Geoffrey Alexander <geoff.i.alexander@gmail.com>
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
__kupfer_name__ = _("Tmux")
__kupfer_actions__ = ("CreateSession", )
__kupfer_sources__ = ("TmuxSessionSource", )
__description__ = _("Control tmux with Kupfer")
__version__ = "0.5"
__author__ = "Geoffrey Alexander <geoff.i.alexander@gmail.com>"

from kupfer.objects import Action, Leaf, Source, TextLeaf
from kupfer import utils

import os

import libtmux


class TmuxSessionSource(Source):
    def __init__(self):
        super().__init__(_("Tmux"))

    def get_items(self):
        for s in libtmux.Server().list_sessions():
            yield TmuxSessionLeaf(s, "{}".format(s.name))

    def provides(self):
        yield TmuxSessionLeaf

    def get_description(self):
        return _("Control tmux sessions")

    def get_icon_name(self):
        return "terminal"


class TmuxSessionLeaf(Leaf):
    def get_description(self):
        num_windows = len(self.object.windows)
        return "{}: {}  [{} window{}]".format(
            self.object.id,
            self.object.name,
            num_windows,
            's' if num_windows > 1 else '')

    def get_icon_name(self):
        return "gnome-window-manager"

    def is_valid(self):
        return self.object in libtmux.Server().list_sessions()

    def get_actions(self):
        return (AttachSession(), KillSession(), RenameSession(), )


class AttachSession(Action):
    def __init__(self):
        super(AttachSession, self).__init__(_("Attach to Session"))

    def activate(self, leaf):
        cmd = ["tmux",  "attach",  "-t", "{}".format(leaf.object.name)]
        utils.spawn_in_terminal(cmd)


class KillSession(Action):
    def __init__(self):
        super(KillSession, self).__init__(_("Kill Session"))

    def activate(self, leaf):
        leaf.object.kill_session()


class RenameSession(Action):
    def __init__(self):
        super(RenameSession, self).__init__(_("Rename Session"))

    def activate(self, leaf, obj):
        leaf.object.rename_session(obj.object)

    def requires_object(self):
        return True

    def object_types(self):
        yield TextLeaf

    def valid_object(self, obj, for_item):
        return type(obj) == TextLeaf


class CreateSession(Action):
    def __init__(self):
        Action.__init__(self, _("Create Tmux Session"))

    def activate(self, leaf):
        home_dir = os.path.expanduser('~')
        libtmux.Server().new_session(leaf.object, attach=False,
                                     start_directory=home_dir)

    def item_types(self):
        yield TextLeaf

    def get_icon_name(self):
        return "terminal"

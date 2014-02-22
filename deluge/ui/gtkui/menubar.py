#
# menubar.py
#
# Copyright (C) 2007, 2008 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2011 Pedro Algarvio <pedro@algarvio.me>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#
#

import os.path
import pygtk
pygtk.require('2.0')
import gtk
import logging

import deluge.error
import deluge.component as component
from deluge.ui.client import client
import deluge.common
import common
import dialogs
from deluge.configmanager import ConfigManager
from deluge.ui.gtkui.path_chooser import PathChooser

log = logging.getLogger(__name__)

class MenuBar(component.Component):

    def __init__(self):
        log.debug("MenuBar init..")
        component.Component.__init__(self, "MenuBar")
        self.window = component.get("MainWindow")
        self.main_builder = self.window.get_builder()
        self.config = ConfigManager("gtkui.conf")

        self.builder = gtk.Builder()
        # Get the torrent menu from the gtk builder file
        self.builder.add_from_file(deluge.common.resource_filename(
            "deluge.ui.gtkui", os.path.join("glade", "torrent_menu.ui")
        ))
        # Get the torrent options menu from the gtk builder file
        self.builder.add_from_file(deluge.common.resource_filename(
            "deluge.ui.gtkui", os.path.join("glade", "torrent_menu.options.ui")
        ))
        # Get the torrent queue menu from the gtk builder file
        self.builder.add_from_file(deluge.common.resource_filename(
            "deluge.ui.gtkui", os.path.join("glade", "torrent_menu.queue.ui")
        ))

        # Attach queue torrent menu
        torrent_queue_menu = self.builder.get_object("queue_torrent_menu")
        self.builder.get_object("menuitem_queue").set_submenu(torrent_queue_menu)
        # Attach options torrent menu
        torrent_options_menu = self.builder.get_object("options_torrent_menu")
        self.builder.get_object("menuitem_options").set_submenu(torrent_options_menu)

        self.builder.get_object("download-limit-image").set_from_file(deluge.common.get_pixmap("downloading16.png"))
        self.builder.get_object("upload-limit-image").set_from_file(deluge.common.get_pixmap("seeding16.png"))

        for menuitem in ("menuitem_down_speed", "menuitem_up_speed",
            "menuitem_max_connections", "menuitem_upload_slots"):
            submenu = gtk.Menu()
            item = gtk.MenuItem(_("Set Unlimited"))
            item.set_name(menuitem)
            item.connect("activate", self.on_menuitem_set_unlimited)
            submenu.append(item)
            item = gtk.MenuItem(_("Other..."))
            item.set_name(menuitem)
            item.connect("activate", self.on_menuitem_set_other)
            submenu.append(item)
            submenu.show_all()
            self.builder.get_object(menuitem).set_submenu(submenu)

        submenu = gtk.Menu()
        item = gtk.MenuItem(_("On"))
        item.connect("activate", self.on_menuitem_set_automanaged_on)
        submenu.append(item)
        item = gtk.MenuItem(_("Off"))
        item.connect("activate", self.on_menuitem_set_automanaged_off)
        submenu.append(item)
        submenu.show_all()
        self.builder.get_object("menuitem_auto_managed").set_submenu(submenu)

        self.torrentmenu = self.builder.get_object("torrent_menu")
        self.menu_torrent = self.main_builder.get_object("menu_torrent")

        # Attach the torrent_menu to the Torrent file menu
        self.menu_torrent.set_submenu(self.torrentmenu)

        # Make sure the view menuitems are showing the correct active state
        self.main_builder.get_object("menuitem_toolbar").set_active(self.config["show_toolbar"])
        self.main_builder.get_object("menuitem_sidebar").set_active(self.config["show_sidebar"])
        self.main_builder.get_object("menuitem_statusbar").set_active(self.config["show_statusbar"])
        self.main_builder.get_object("sidebar_show_zero").set_active(self.config["sidebar_show_zero"])
        self.main_builder.get_object("sidebar_show_trackers").set_active(self.config["sidebar_show_trackers"])


        ### Connect main window Signals ###
        component.get("MainWindow").connect_signals({
            ## File Menu
            "on_menuitem_addtorrent_activate": self.on_menuitem_addtorrent_activate,
            "on_menuitem_createtorrent_activate": self.on_menuitem_createtorrent_activate,
            "on_menuitem_quitdaemon_activate": self.on_menuitem_quitdaemon_activate,
            "on_menuitem_quit_activate": self.on_menuitem_quit_activate,

            ## Edit Menu
            "on_menuitem_preferences_activate": self.on_menuitem_preferences_activate,
            "on_menuitem_connectionmanager_activate": self.on_menuitem_connectionmanager_activate,

            ## View Menu
            "on_menuitem_toolbar_toggled": self.on_menuitem_toolbar_toggled,
            "on_menuitem_sidebar_toggled": self.on_menuitem_sidebar_toggled,
            "on_menuitem_statusbar_toggled": self.on_menuitem_statusbar_toggled,

            ## Help Menu
            "on_menuitem_homepage_activate": self.on_menuitem_homepage_activate,
            "on_menuitem_faq_activate": self.on_menuitem_faq_activate,
            "on_menuitem_community_activate": self.on_menuitem_community_activate,
            "on_menuitem_about_activate": self.on_menuitem_about_activate,
            "on_menuitem_sidebar_zero_toggled":self.on_menuitem_sidebar_zero_toggled,
            "on_menuitem_sidebar_trackers_toggled":self.on_menuitem_sidebar_trackers_toggled
        })

        # Connect menubar signals
        self.builder.connect_signals({
            ## Torrent Menu
            "on_menuitem_pause_activate": self.on_menuitem_pause_activate,
            "on_menuitem_resume_activate": self.on_menuitem_resume_activate,
            "on_menuitem_updatetracker_activate": self.on_menuitem_updatetracker_activate,
            "on_menuitem_edittrackers_activate": self.on_menuitem_edittrackers_activate,
            "on_menuitem_remove_activate": self.on_menuitem_remove_activate,
            "on_menuitem_recheck_activate": self.on_menuitem_recheck_activate,
            "on_menuitem_open_folder_activate": self.on_menuitem_open_folder_activate,
            "on_menuitem_move_activate": self.on_menuitem_move_activate,
            "on_menuitem_queue_top_activate": self.on_menuitem_queue_top_activate,
            "on_menuitem_queue_up_activate": self.on_menuitem_queue_up_activate,
            "on_menuitem_queue_down_activate": self.on_menuitem_queue_down_activate,
            "on_menuitem_queue_bottom_activate": self.on_menuitem_queue_bottom_activate
        })

        self.change_sensitivity = [
            "menuitem_addtorrent"
        ]

        self.config.register_set_function("classic_mode", self._on_classic_mode)

        client.register_event_handler("TorrentStateChangedEvent", self.on_torrentstatechanged_event)
        client.register_event_handler("TorrentResumedEvent", self.on_torrentresumed_event)
        client.register_event_handler("SessionPausedEvent", self.on_sessionpaused_event)
        client.register_event_handler("SessionResumedEvent", self.on_sessionresumed_event)

    def start(self):
        for widget in self.change_sensitivity:
            self.main_builder.get_object(widget).set_sensitive(True)

        # Hide the Open Folder menuitem and separator if not connected to a
        # localhost.
        non_remote_items = [
            "menuitem_open_folder",
            "separator4"
        ]
        if not client.is_localhost():
            for widget in non_remote_items:
                self.builder.get_object(widget).hide()
                self.builder.get_object(widget).set_no_show_all(True)
        else:
            for widget in non_remote_items:
                self.builder.get_object(widget).set_no_show_all(False)

        if not self.config["classic_mode"]:
            self.main_builder.get_object("separatormenuitem").show()
            self.main_builder.get_object("menuitem_quitdaemon").show()

        # Show the Torrent menu because we're connected to a host
        self.menu_torrent.show()

        if client.get_auth_level() == deluge.common.AUTH_LEVEL_ADMIN:
            # Get known accounts to allow changing ownership
            client.core.get_known_accounts().addCallback(
                self._on_known_accounts).addErrback(self._on_known_accounts_fail
            )

    def stop(self):
        log.debug("MenuBar stopping")

        for widget in self.change_sensitivity:
            self.main_builder.get_object(widget).set_sensitive(False)

        # Hide the Torrent menu
        self.menu_torrent.hide()

        self.main_builder.get_object("separatormenuitem").hide()
        self.main_builder.get_object("menuitem_quitdaemon").hide()

    def update_menu(self):
        selected = component.get('TorrentView').get_selected_torrents()
        if not selected or len(selected) == 0:
            # No torrent is selected. Disable the 'Torrents' menu
            self.menu_torrent.set_sensitive(False)
            return

        self.menu_torrent.set_sensitive(True)
        # XXX: Should also update Pause/Resume/Remove menuitems.
        # Any better way than duplicating toolbar.py:update_buttons in here?

    def add_torrentmenu_separator(self):
        sep = gtk.SeparatorMenuItem()
        self.torrentmenu.append(sep)
        sep.show()
        return sep

    ### Callbacks ###
    def on_torrentstatechanged_event(self, torrent_id, state):
        if state == "Paused":
            self.update_menu()

    def on_torrentresumed_event(self, torrent_id):
        self.update_menu()

    def on_sessionpaused_event(self):
        self.update_menu()

    def on_sessionresumed_event(self):
        self.update_menu()

    ## File Menu ##
    def on_menuitem_addtorrent_activate(self, data=None):
        log.debug("on_menuitem_addtorrent_activate")
        component.get("AddTorrentDialog").show()

    def on_menuitem_createtorrent_activate(self, data=None):
        log.debug("on_menuitem_createtorrent_activate")
        from createtorrentdialog import CreateTorrentDialog
        CreateTorrentDialog().show()

    def on_menuitem_quitdaemon_activate(self, data=None):
        log.debug("on_menuitem_quitdaemon_activate")
        self.window.quit(shutdown=True)

    def on_menuitem_quit_activate(self, data=None):
        log.debug("on_menuitem_quit_activate")
        self.window.quit()

    ## Edit Menu ##
    def on_menuitem_preferences_activate(self, data=None):
        log.debug("on_menuitem_preferences_activate")
        component.get("Preferences").show()

    def on_menuitem_connectionmanager_activate(self, data=None):
        log.debug("on_menuitem_connectionmanager_activate")
        component.get("ConnectionManager").show()

    ## Torrent Menu ##
    def on_menuitem_pause_activate(self, data=None):
        log.debug("on_menuitem_pause_activate")
        client.core.pause_torrent(
            component.get("TorrentView").get_selected_torrents())

    def on_menuitem_resume_activate(self, data=None):
        log.debug("on_menuitem_resume_activate")
        client.core.resume_torrent(
            component.get("TorrentView").get_selected_torrents())

    def on_menuitem_updatetracker_activate(self, data=None):
        log.debug("on_menuitem_updatetracker_activate")
        client.core.force_reannounce(
            component.get("TorrentView").get_selected_torrents())

    def on_menuitem_edittrackers_activate(self, data=None):
        log.debug("on_menuitem_edittrackers_activate")
        from edittrackersdialog import EditTrackersDialog
        dialog = EditTrackersDialog(
            component.get("TorrentView").get_selected_torrent(),
            component.get("MainWindow").window)
        dialog.run()

    def on_menuitem_remove_activate(self, data=None):
        log.debug("on_menuitem_remove_activate")
        torrent_ids = component.get("TorrentView").get_selected_torrents()
        if torrent_ids:
            from removetorrentdialog import RemoveTorrentDialog
            RemoveTorrentDialog(torrent_ids).run()

    def on_menuitem_recheck_activate(self, data=None):
        log.debug("on_menuitem_recheck_activate")
        client.core.force_recheck(
            component.get("TorrentView").get_selected_torrents())

    def on_menuitem_open_folder_activate(self, data=None):
        log.debug("on_menuitem_open_folder")
        def _on_torrent_status(status):
            deluge.common.open_file(status["save_path"])
        for torrent_id in component.get("TorrentView").get_selected_torrents():
            component.get("SessionProxy").get_torrent_status(
                torrent_id, ["save_path"]).addCallback(_on_torrent_status)

    def on_menuitem_move_activate(self, data=None):
        log.debug("on_menuitem_move_activate")
        component.get("SessionProxy").get_torrent_status(
            component.get("TorrentView").get_selected_torrent(),
            ["save_path"]).addCallback(self.show_move_storage_dialog)

    def show_move_storage_dialog(self, status):
        log.debug("show_move_storage_dialog")
        builder = gtk.Builder()
        builder.add_from_file(deluge.common.resource_filename(
            "deluge.ui.gtkui", os.path.join("glade", "move_storage_dialog.ui")
        ))
        # Keep it referenced:
        #  https://bugzilla.gnome.org/show_bug.cgi?id=546802
        self.move_storage_dialog = builder.get_object("move_storage_dialog")
        self.move_storage_dialog.set_transient_for(self.window.window)
        self.move_storage_dialog_hbox = builder.get_object("hbox_entry")
        self.move_storage_path_chooser = PathChooser("move_completed_paths_list")
        self.move_storage_dialog_hbox.add(self.move_storage_path_chooser)
        self.move_storage_dialog_hbox.show_all()
        self.move_storage_path_chooser.set_text(status["save_path"])

        def on_dialog_response_event(widget, response_id):
            def on_core_result(result):
                # Delete references
                del self.move_storage_dialog
                del self.move_storage_dialog_hbox

            if response_id == gtk.RESPONSE_OK:
                log.debug("Moving torrents to %s",
                          self.move_storage_path_chooser.get_text())
                path = self.move_storage_path_chooser.get_text()
                client.core.move_storage(
                    component.get("TorrentView").get_selected_torrents(), path
                ).addCallback(on_core_result)
            self.move_storage_dialog.hide()

        self.move_storage_dialog.connect("response", on_dialog_response_event)
        self.move_storage_dialog.show()

    def on_menuitem_queue_top_activate(self, value):
        log.debug("on_menuitem_queue_top_activate")
        client.core.queue_top(component.get("TorrentView").get_selected_torrents())

    def on_menuitem_queue_up_activate(self, value):
        log.debug("on_menuitem_queue_up_activate")
        client.core.queue_up(component.get("TorrentView").get_selected_torrents())

    def on_menuitem_queue_down_activate(self, value):
        log.debug("on_menuitem_queue_down_activate")
        client.core.queue_down(component.get("TorrentView").get_selected_torrents())

    def on_menuitem_queue_bottom_activate(self, value):
        log.debug("on_menuitem_queue_bottom_activate")
        client.core.queue_bottom(component.get("TorrentView").get_selected_torrents())

    ## View Menu ##
    def on_menuitem_toolbar_toggled(self, value):
        log.debug("on_menuitem_toolbar_toggled")
        component.get("ToolBar").visible(value.get_active())

    def on_menuitem_sidebar_toggled(self, value):
        log.debug("on_menuitem_sidebar_toggled")
        component.get("SideBar").visible(value.get_active())

    def on_menuitem_statusbar_toggled(self, value):
        log.debug("on_menuitem_statusbar_toggled")
        component.get("StatusBar").visible(value.get_active())

    ## Help Menu ##
    def on_menuitem_homepage_activate(self, data=None):
        log.debug("on_menuitem_homepage_activate")
        deluge.common.open_url_in_browser("http://deluge-torrent.org")

    def on_menuitem_faq_activate(self, data=None):
        log.debug("on_menuitem_faq_activate")
        deluge.common.open_url_in_browser("http://dev.deluge-torrent.org/wiki/Faq")

    def on_menuitem_community_activate(self, data=None):
        log.debug("on_menuitem_community_activate")
        deluge.common.open_url_in_browser("http://forum.deluge-torrent.org/")

    def on_menuitem_about_activate(self, data=None):
        log.debug("on_menuitem_about_activate")
        from aboutdialog import AboutDialog
        AboutDialog().run()

    def on_menuitem_set_unlimited(self, widget):
        log.debug("widget.name: %s", widget.name)
        funcs = {
            "menuitem_down_speed": client.core.set_torrent_max_download_speed,
            "menuitem_up_speed": client.core.set_torrent_max_upload_speed,
            "menuitem_max_connections": client.core.set_torrent_max_connections,
            "menuitem_upload_slots": client.core.set_torrent_max_upload_slots
        }
        if widget.name in funcs.keys():
            for torrent in component.get("TorrentView").get_selected_torrents():
                funcs[widget.name](torrent, -1)

    def on_menuitem_set_other(self, widget):
        log.debug("widget.name: %s", widget.name)
        status_map = {
            "menuitem_down_speed": "max_download_speed",
            "menuitem_up_speed": "max_upload_speed",
            "menuitem_max_connections": "max_connections",
            "menuitem_upload_slots": "max_upload_slots"
        }

        other_dialog_info = {
            "menuitem_down_speed": [_("Set Maximum Download Speed"), _("KiB/s"), None, "downloading.svg", -1.0],
            "menuitem_up_speed": [_("Set Maximum Upload Speed"), _("KiB/s"), None, "seeding.svg", -1.0],
            "menuitem_max_connections": [_("Set Maximum Connections"), "", gtk.STOCK_NETWORK, None, -1],
            "menuitem_upload_slots": [_("Set Maximum Upload Slots"), "", gtk.STOCK_SORT_ASCENDING, None, -1]
        }

        status_key = status_map[widget.name]
        def _on_torrent_status(status):
            # widget: [header, type_str, image_stockid, image_filename, default]
            other_dialog = other_dialog_info[widget.name]
            # Update the default with value from status and show the other dialog
            other_dialog[4] = status[status_key]
            def on_value(value):
                if value and widget.name in status_map:
                    client.core.set_torrent_options(torrent_ids, {status_key:value})
            common.show_other_dialog(*other_dialog).addCallback(on_value)

        torrent_ids = component.get("TorrentView").get_selected_torrents()
        if len(torrent_ids) == 1:
            d = component.get("SessionProxy").get_torrent_status(torrent_ids[0], status_key)
        else:
            log.error("else")
            d = client.core.get_config_value(status_key)
        d.addCallback(_on_torrent_status)


    def on_menuitem_set_automanaged_on(self, widget):
        for torrent in component.get("TorrentView").get_selected_torrents():
            client.core.set_torrent_auto_managed(torrent, True)

    def on_menuitem_set_automanaged_off(self, widget):
        for torrent in component.get("TorrentView").get_selected_torrents():
            client.core.set_torrent_auto_managed(torrent, False)

    def on_menuitem_sidebar_zero_toggled(self, widget):
        self.config["sidebar_show_zero"] = widget.get_active()
        component.get("FilterTreeView").update()

    def on_menuitem_sidebar_trackers_toggled(self, widget):
        self.config["sidebar_show_trackers"] = widget.get_active()
        component.get("FilterTreeView").update()

    def _on_classic_mode(self, key, value):
        if value:
            self.main_builder.get_object("menuitem_connectionmanager").hide()
        else:
            self.main_builder.get_object("menuitem_connectionmanager").show()

    def _on_known_accounts(self, known_accounts):
        known_accounts_to_log = []
        for account in known_accounts:
            account_to_log = {}
            for key, value in account.copy().iteritems():
                if key == 'password':
                    value = '*' * len(value)
                account_to_log[key] = value
            known_accounts_to_log.append(account_to_log)
        log.debug("_on_known_accounts: %s", known_accounts_to_log)
        if len(known_accounts) <= 1:
            return

        self.builder.get_object("menuitem_change_owner").set_visible(True)

        self.change_owner_submenu = gtk.Menu()
        self.change_owner_submenu_items = {}
        maingroup = gtk.RadioMenuItem(None, None)

        self.change_owner_submenu_items[None] = gtk.RadioMenuItem(maingroup)

        for account in known_accounts:
            username = account["username"]
            item = gtk.RadioMenuItem(maingroup, username)
            self.change_owner_submenu_items[username] = item
            self.change_owner_submenu.append(item)
            item.connect("toggled", self._on_change_owner_toggled, username)

        self.change_owner_submenu.show_all()
        self.change_owner_submenu_items[None].set_active(True)
        self.change_owner_submenu_items[None].hide()
        self.builder.get_object("menuitem_change_owner").connect(
            "activate", self._on_change_owner_submenu_active
        )
        self.builder.get_object("menuitem_change_owner").set_submenu(self.change_owner_submenu)

    def _on_known_accounts_fail(self, reason):
        self.builder.get_object("menuitem_change_owner").set_visible(False)

    def _on_change_owner_submenu_active(self, widget):
        log.debug("_on_change_owner_submenu_active")
        selected = component.get("TorrentView").get_selected_torrents()
        if len(selected) > 1:
            self.change_owner_submenu_items[None].set_active(True)
            return

        torrent_owner = component.get("TorrentView").get_torrent_status(selected[0])["owner"]
        for username, item in self.change_owner_submenu_items.iteritems():
            item.set_active(username == torrent_owner)

    def _on_change_owner_toggled(self, widget, username):
        log.debug("_on_change_owner_toggled")
        update_torrents = []
        selected = component.get("TorrentView").get_selected_torrents()
        for torrent_id in selected:
            torrent_status = component.get("TorrentView").get_torrent_status(torrent_id)
            if torrent_status["owner"] != username:
                update_torrents.append(torrent_id)

        if update_torrents:
            log.debug("Setting torrent owner \"%s\" on %s", username, update_torrents)

            def failed_change_owner(failure):
                dialogs.ErrorDialog(
                    _("Ownership Change Error"),
                    _("There was an error while trying changing ownership."),
                    self.window.window, details=failure.value.logable()
                ).run()
            client.core.set_owner(
                update_torrents, username).addErrback(failed_change_owner)

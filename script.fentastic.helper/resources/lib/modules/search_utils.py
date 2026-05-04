# -*- coding: utf-8 -*-

import xbmc, xbmcgui, xbmcvfs, sys
import sqlite3 as database
from modules import xmls
from urllib.parse import quote, unquote
from threading import Thread, Event
from xml.sax.saxutils import escape

# from modules.logger import logger

MAX_HISTORY_ITEMS = 20
DEFAULT_HISTORY_ITEMS = 10

settings_path = xbmcvfs.translatePath(
    "special://profile/addon_data/script.fentastic.helper/"
)

spath_database_path = xbmcvfs.translatePath(
    "special://profile/addon_data/script.fentastic.helper/spath_cache.db"
)

search_history_xml = "script-fentastic-search_history"

default_xmls = {
    "search_history": (search_history_xml, xmls.default_history, "SearchHistory")
}

default_path = "addons://sources/video"
WINDOW_HOME = 10000
WINDOW_SEARCH_RESULTS = 1121


class SPaths:
    def __init__(self, spaths=None):
        self.connect_database()
        if spaths is None:
            self.spaths = []
        else:
            self.spaths = spaths
        self.refresh_spaths = False

    def connect_database(self):
        if not xbmcvfs.exists(settings_path):
            xbmcvfs.mkdir(settings_path)
        self.dbcon = database.connect(spath_database_path, timeout=20)
        self.dbcon.execute(
            "CREATE TABLE IF NOT EXISTS spath (spath_id INTEGER PRIMARY KEY AUTOINCREMENT, spath text)"
        )
        self.dbcur = self.dbcon.cursor()

    def add_spath_to_database(self, spath):
        self.refresh_spaths = True
        self.dbcur.execute(
            "INSERT INTO spath (spath) VALUES (?)",
            (spath,),
        )
        self.dbcon.commit()

    def remove_spath_from_database(self, spath_id):
        self.refresh_spaths = True
        self.dbcur.execute("DELETE FROM spath WHERE spath_id = ?", (spath_id,))
        self.dbcon.commit()

    def is_database_empty(self):
        self.dbcur.execute("SELECT COUNT(*) FROM spath")
        rows = self.dbcur.fetchone()[0]
        return rows == 0

    def remove_all_spaths(self):
        dialog = xbmcgui.Dialog()
        title = "FENtastic"
        prompt = "Are you sure you want to clear all search history? Once cleared, these items cannot be recovered. Proceed?"
        self.fetch_all_spaths()
        if dialog.yesno(title, prompt):
            self.refresh_spaths = True
            self.dbcur.execute("DELETE FROM spath")
            self.dbcur.execute("DELETE FROM sqlite_sequence WHERE name='spath'")
            self.dbcon.commit()
            self.make_default_xml()
            self.apply_search_history_to_skin([])
            Thread(target=self.update_settings_and_reload_skin).start()

    def fetch_all_spaths(self):
        results = self.dbcur.execute(
            "SELECT * FROM spath ORDER BY spath_id DESC"
        ).fetchall()
        return results

    def apply_search_history_to_skin(self, rows=None):
        if rows is None:
            rows = self.fetch_all_spaths()

        try:
            limit = int(xbmc.getInfoLabel("Skin.String(searchhistory.limit)"))
        except ValueError:
            limit = DEFAULT_HISTORY_ITEMS

        labels = [term for _, term in rows[:limit]]
        for i in range(MAX_HISTORY_ITEMS):
            slot = i + 1
            if i < len(labels):
                xbmc.executebuiltin(f"Skin.SetString(SearchHistory.{slot},{labels[i]})")
            else:
                xbmc.executebuiltin(f"Skin.Reset(SearchHistory.{slot})")
        xbmc.executebuiltin(f"Skin.SetString(SearchHistoryCount,{len(labels)})")

    def update_settings_and_reload_skin(self):
        xbmc.executebuiltin("Skin.SetString(SearchInput,)")
        xbmc.executebuiltin("Skin.SetString(SearchInputEncoded,)")
        xbmc.executebuiltin("Skin.SetString(SearchInputTraktEncoded, 'none')")
        xbmc.executebuiltin("Skin.SetString(DatabaseStatus, 'Empty')")
        xbmc.sleep(300)
        xbmc.executebuiltin("ReloadSkin()")
        xbmc.sleep(200)
        xbmc.executebuiltin("SetFocus(27400)")

    def make_search_history_xml(self, active_spaths, event=None):
        try:
            if not self.refresh_spaths:
                return
            if not active_spaths:
                self.make_default_xml()
                return
            xml_file = "special://skin/xml/%s.xml" % (search_history_xml)
            final_format = xmls.media_xml_start.format(main_include="SearchHistory")
            for _, spath in active_spaths:
                body = xmls.history_xml_body
                safe_spath = escape(spath)
                body = body.format(spath=safe_spath)
                final_format += body
            final_format += xmls.media_xml_end
            self.write_xml(xml_file, final_format)
        finally:
            if event is not None:
                event.set()

    def write_xml(self, xml_file, final_format):
        with xbmcvfs.File(xml_file, "w") as f:
            f.write(final_format)

    def make_default_xml(self):
        item = default_xmls["search_history"]
        final_format = item[1].format(includes_type=item[2])
        xml_file = "special://skin/xml/%s.xml" % item[0]
        with xbmcvfs.File(xml_file, "w") as f:
            f.write(final_format)

    def check_spath_exists(self, spath):
        result = self.dbcur.execute(
            "SELECT spath_id FROM spath WHERE spath = ?", (spath,)
        ).fetchone()
        return result[0] if result else None

    def open_search_window(self):
        rows = self.fetch_all_spaths()
        self.refresh_spaths = True
        self.apply_search_history_to_skin(rows)
        if rows:
            self.make_search_history_xml(rows)
            xbmc.executebuiltin("Skin.Reset(DatabaseStatus)")
        else:
            self.make_default_xml()
            xbmc.executebuiltin("Skin.SetString(DatabaseStatus, 'Empty')")
        xbmc.executebuiltin("Skin.Reset(SearchInput)")
        xbmc.executebuiltin("Skin.Reset(SearchInputEncoded)")
        xbmc.executebuiltin("Skin.SetString(SearchInputTraktEncoded,none)")
        xbmc.executebuiltin("ClearProperty(fentastic.results,1121)")
        xbmc.executebuiltin(f"ActivateWindow({WINDOW_SEARCH_RESULTS})")
        xbmc.sleep(150)
        if rows:
            xbmc.executebuiltin("SetFocus(9000)")
        else:
            xbmc.executebuiltin("SetFocus(27400)")

    def search_input(self, search_term=None):
        xbmc.log(f"[FEN HELPER] search_input() called with search_term={search_term}", xbmc.LOGINFO)
        if search_term is None:
            for arg in sys.argv:
                if arg.startswith("query="):
                    search_term = unquote(arg.replace("query=", "", 1))
                    xbmc.log(f"[FEN HELPER] search_input() found query in sys.argv: {search_term}", xbmc.LOGINFO)
                    break
        if search_term is None or not search_term.strip():
            xbmc.log(f"[FEN HELPER] search_input() search_term empty, showing keyboard", xbmc.LOGINFO)
            prompt = "Search" if xbmcgui.getCurrentWindowId() == WINDOW_HOME else "New Search"
            keyboard = xbmc.Keyboard("", prompt, False)
            keyboard.doModal()
            if keyboard.isConfirmed():
                xbmc.executebuiltin("Skin.Reset(DatabaseStatus)")
                search_term = keyboard.getText()
                if not search_term or not search_term.strip():
                    return
            else:
                return
        search_term = search_term.strip()
        xbmc.log(f"[FEN HELPER] search_input() executing search for: {search_term}", xbmc.LOGINFO)
        encoded_search_term = quote(search_term)
        xbmc.executebuiltin("Skin.Reset(DatabaseStatus)")
        xbmc.executebuiltin("Skin.SetString(current_search_provider,1)")
        xbmc.executebuiltin(f"Skin.SetString(SearchInput,{search_term})")
        xbmc.executebuiltin(f"Skin.SetString(SearchInputEncoded,{encoded_search_term})")
        xbmc.executebuiltin(
            f"Skin.SetString(SearchInputTraktEncoded,{encoded_search_term})"
        )
        if xbmcgui.getCurrentWindowId() != WINDOW_SEARCH_RESULTS:
            xbmc.log(f"[FEN HELPER] search_input() not in search results window, activating", xbmc.LOGINFO)
            xbmc.executebuiltin(f"ActivateWindow({WINDOW_SEARCH_RESULTS})")
            xbmc.sleep(150)
        existing_spath = self.check_spath_exists(search_term)
        if existing_spath:
            self.remove_spath_from_database(existing_spath)
        self.add_spath_to_database(search_term)
        rows = self.fetch_all_spaths()
        self.apply_search_history_to_skin(rows)
        self.refresh_spaths = True
        self.make_search_history_xml(rows)
        xbmc.executebuiltin("SetProperty(fentastic.results,1,1121)")
        xbmc.executebuiltin("Container(27001).Update()")
        xbmc.executebuiltin("SetFocus(2000)")
        xbmc.log(f"[FEN HELPER] search_input() completed for: {search_term}", xbmc.LOGINFO)

    def re_search(self, search_term=None):
        xbmc.log(f"[FEN HELPER] re_search() called with search_term={search_term}", xbmc.LOGINFO)
        if search_term:
            search_term = unquote(search_term)
            xbmc.log(f"[FEN HELPER] re_search() unquoted search_term: {search_term}", xbmc.LOGINFO)
        else:
            search_term = ""
            for arg in sys.argv:
                if arg.startswith("query="):
                    search_term = unquote(arg.replace("query=", "", 1))
                    xbmc.log(f"[FEN HELPER] re_search() found query in sys.argv: {search_term}", xbmc.LOGINFO)
                    break
        if not search_term:
            search_term = xbmc.getInfoLabel("ListItem.Label")
            xbmc.log(f"[FEN HELPER] re_search() fallback to ListItem.Label: {search_term}", xbmc.LOGINFO)
        if not search_term or not search_term.strip():
            xbmc.log(f"[FEN HELPER] re_search() search_term empty, returning without search", xbmc.LOGINFO)
            return
        xbmc.log(f"[FEN HELPER] re_search() calling search_input with: {search_term}", xbmc.LOGINFO)
        self.search_input(search_term)

    def remake_search_history(self):
        self.refresh_spaths = True
        active_spaths = self.fetch_all_spaths()
        self.apply_search_history_to_skin(active_spaths)
        if active_spaths:
            self.make_search_history_xml(active_spaths)
        else:
            self.make_default_xml()


# def remake_all_spaths(silent=False):
#     for item in "search_history":
#         SPaths(item).remake_search_history()
#     if not silent:
#         xbmcgui.Dialog().ok("FENtastic", "Search history remade")

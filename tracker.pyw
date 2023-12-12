import tkinter as Tk
import tkinter.font as tkFont
from tkinter import ttk, PhotoImage, messagebox, filedialog, simpledialog
import json
import urllib.request
import webbrowser
from contextlib import contextmanager
import subprocess
import sys
import zipfile
from io import BytesIO
import os
import platform
import shutil
import copy
from typing import Callable, Optional
from datetime import datetime
import calendar
import traceback

class Tracker(Tk.Tk):
    CHESTS = ["wood", "silver", "gold", "red", "blue", "purple"] # chest list
    RARES = ["bar", "sand"] # rare item
    FORBIDDEN = ["version", "last", "settings", "history", "favorites"] # forbidden raid name list
    THEME = ["light", "dark", "forest-light", "forest-dark"] # existing themes
    DEFAULT_LAYOUT = "[{'tab_image': 'bar', 'text': 'Bars', 'raids': [{'raid_image': 'bhl', 'text': 'BHL', 'loot': ['blue', 'ring3', 'bar']}, {'raid_image': 'akasha', 'text': 'Akasha', 'loot': ['blue', 'ring3', 'bar']}, {'raid_image': 'gohl', 'text': 'Grande', 'loot': ['blue', 'ring3', 'bar']}]}, {'tab_image': 'sand', 'text': 'Revans', 'raids': [{'raid_image': 'mugen', 'text': 'Mugen', 'loot': ['blue', 'wpn_mugen', 'wpn_mugen2', 'sand']}, {'raid_image': 'diaspora', 'text': 'Diaspora', 'loot': ['blue', 'wpn_diaspora', 'wpn_diaspora2', 'sand']}, {'raid_image': 'siegfried', 'text': 'Siegfried', 'loot': ['blue', 'wpn_siegfried', 'wpn_siegfried2', 'sand']}, {'raid_image': 'siete', 'text': 'Siete', 'loot': ['blue', 'wpn_siete', 'wpn_siete2', 'sand']}, {'raid_image': 'cosmos', 'text': 'Cosmos', 'loot': ['blue', 'wpn_cosmos', 'wpn_cosmos2', 'sand']}, {'raid_image': 'agastia', 'text': 'Agastia', 'loot': ['blue', 'wpn_agastia', 'wpn_agastia2', 'sand']}]}, {'tab_image': 'sand', 'text': 'Sands', 'raids': [{'raid_image': 'ennead', 'text': 'Enneads', 'loot': ['sand']}, {'raid_image': '6d', 'text': '6D', 'loot': ['fireearring', 'sand']}, {'raid_image': 'subaha', 'text': 'SuBaha', 'loot': ['sand']}, {'raid_image': 'hexa', 'text': 'Hexa', 'loot': ['sand']}]}]"
    RAID_TAB_LIMIT = 6
    MIN_WIDTH = 240
    MIN_HEIGHT = 150
    SMALL_THUMB = (20, 20)
    BIG_THUMB = (50, 50)
    GITHUB = "https://github.com/MizaGBF/GBFLT"

    def __init__(self) -> None:
        Tk.Tk.__init__(self,None)
        self.parent = None
        self.version = "0.0"
        self.python = "3.10"
        self.og_raidlayout = True # set to False if the user has modified raids.json
        self.stats_window = None # reference to the current stat window
        self.import_window = None # reference to the current import window
        self.editor_window = None # reference to the current editor window
        self.history_window = None # reference to the current history window
        errors = self.load_manifest()
        savedata, rerrors = self.load_savedata()
        errors += rerrors
        self.favorites = [] if savedata is None else savedata.get("favorites", [])
        self.history = {} if savedata is None else savedata.get("history", {})
        self.settings = {} if savedata is None else savedata.get("settings", {})
        self.call('source', 'assets/themes/main.tcl')
        self.call("set_theme", self.settings.get("theme", self.THEME[0]))
        self.title("GBF Loot Tracker v" + self.version)
        self.iconbitmap('assets/icon.ico')
        self.resizable(width=False, height=False) # not resizable
        self.minsize(self.MIN_WIDTH, self.MIN_HEIGHT)
        self.protocol("WM_DELETE_WINDOW", self.close) # call close() if we close the window
        self.assets = {} # contains loaded images
        self.raid_data = {} # contains the layout
        self.got_chest = {} # dict of raid with a chest button, and their chest button name
        self.got_rare = {} # set of raid with a bar or sand button
        self.last_tab = None # track the last tab used
        self.modified = False # if True, need to save
        layout, rerrors = self.load_raids()
        errors += rerrors
        errors += self.verify_layout(layout)
        
        # calculate windows position offset
        try:
            try: n = "/".join(platform.uname()) # use platform info as an unique identifier (sort of)
            except: n = platform.system()+"/"+platform.platform()
            if n != self.settings.get('machine', '') or 'offset' not in self.settings: # this way, we recalculate the offset if the user changed machine (as it might differ between windows/linux/etc... versions/themes)
                self.settings['machine'] = n
                self.settings['offset'] = OffsetTester(self).get_offset() # create a windows at position 100x100, update it, get its new position and retrieve the difference
        except:
            pass
        
        self.tab_tree = {} # used to memorize the tab structure, to set the active tab after loading
        self.top_tab = ttk.Notebook(self, takefocus=False)
        for ti, t in enumerate(layout): # top tabs
            tab = ttk.Frame(self.top_tab)
            self.top_tab.add(tab, text=t.get("text", ""))
            self.top_tab.tab(tab, image=self.load_asset("assets/tabs/" + t.get("tab_image", "").replace(".png", "") + ".png", self.SMALL_THUMB), compound=Tk.LEFT)
            raid_tabs = ttk.Notebook(tab, takefocus=False)
            tab_count = len(t.get("raids", []))
            for c, r in enumerate(t.get("raids", [])): # raid tabs
                if "text" not in r or  r["text"] in self.raid_data:
                    continue
                else:
                    rn = r["text"]
                    if rn in self.FORBIDDEN:
                        continue
                    else:
                        self.tab_tree[rn] = (ti, c, raid_tabs)
                        self.raid_data[rn] = {}
                        sub = ttk.Frame(raid_tabs)
                        if tab_count <= self.RAID_TAB_LIMIT: raid_tabs.add(sub, text=rn)
                        else: raid_tabs.add(sub)
                        raid_tabs.tab(sub, image=self.load_asset("assets/tabs/" + r.get("raid_image", "").replace(".png", "") + ".png", self.SMALL_THUMB), compound=Tk.LEFT)
                        self.set_tab_content(sub, r, self.raid_data[rn], True)
            raid_tabs.pack(expand=1, fill="both")
        # settings
        tab = ttk.Frame(self.top_tab)
        self.top_tab.add(tab, text="Settings")
        self.top_tab.tab(tab, image=self.load_asset("assets/others/settings.png", self.SMALL_THUMB), compound=Tk.LEFT)
        self.make_button(tab, "Toggle Theme", self.toggle_theme, 0, 0, 3, "we", ("others", "theme", self.SMALL_THUMB))
        self.make_button(tab, "Layout Editor  ", self.open_layout_editor, 1, 0, 3, "we", ("others", "layout", self.SMALL_THUMB))
        self.make_button(tab, "Restart the App", self.restart, 2, 0, 3, "we", ("others", "restart", self.SMALL_THUMB))
        self.make_button(tab, "Open Statistics", self.stats, 3, 0, 3, "we", ("others", "stats", self.SMALL_THUMB))
        self.make_button(tab, "Export to Text", self.export_to_text, 4, 0, 3, "we", ("others", "export", self.SMALL_THUMB))
        self.make_button(tab, "What's New?   ", self.show_changelog, 5, 0, 3, "we", ("others", "new", self.SMALL_THUMB))
        self.make_button(tab, "Credits           ", self.show_credits, 6, 0, 3, "we", ("others", "credits", self.SMALL_THUMB))
        self.make_button(tab, "Github Repository", self.github_repo, 0, 3, 3, "we", ("others", "github", self.SMALL_THUMB))
        self.make_button(tab, "Bug Report        ", self.github_issue, 1, 3, 3, "we", ("others", "bug", self.SMALL_THUMB))
        self.make_button(tab, "Check Updates   ", lambda : self.check_new_update(False), 2, 3, 3, "we", ("others", "update", self.SMALL_THUMB))
        self.make_button(tab, "Shortcut List       ", self.show_shortcut, 3, 3, 3, "we", ("others", "shortcut", self.SMALL_THUMB))
        self.make_button(tab, "Favorited           ", self.show_favorite, 4, 3, 3, "we", ("others", "favorite", self.SMALL_THUMB))
        self.make_button(tab, "Import from        ", self.import_data, 5, 3, 3, "we", ("others", "import", self.SMALL_THUMB))
        # check boxes
        self.show_notif = Tk.IntVar()
        ttk.Checkbutton(tab, text='Show notifications', variable=self.show_notif, command=self.toggle_notif).grid(row=0, column=6, columnspan=5, sticky="we")
        self.show_notif.set(self.settings.get("show_notif", 0))
        self.top_most = Tk.IntVar()
        ttk.Checkbutton(tab, text='Always on top', variable=self.top_most, command=self.toggle_topmost).grid(row=1, column=6, columnspan=5, sticky="we")
        self.top_most.set(self.settings.get("top_most", 0))
        if self.settings.get("top_most", 0) == 1:
            self.attributes('-topmost', True)
        self.check_update = Tk.IntVar()
        ttk.Checkbutton(tab, text='Auto Check Updates', variable=self.check_update, command=self.toggle_checkupdate).grid(row=2, column=6, columnspan=5, sticky="we")
        self.check_update.set(self.settings.get("check_update", 0))
        self.backup_save = Tk.IntVar()
        ttk.Checkbutton(tab, text='Backup Save on startup', variable=self.backup_save, command=self.toggle_backup).grid(row=3, column=6, columnspan=5, sticky="we")
        self.backup_save.set(self.settings.get("backup_save", 0))
        
        # shortcut
        self.set_general_binding(self)
        
        # notification
        self.notification = Tk.Label(self, text="")
        self.notification_after = None # after callback
        if self.settings.get("show_notif", 1) == 1: self.notification.grid(row=1, column=0, sticky="w")
        # welcome notification and easter eggs
        now = datetime.now()
        if now.day == calendar.monthrange(now.year, now.month)[1]: self.push_notif(["Immunity Lily blesses your rolls.", "GOLEM GET YE GONE!"][now.month%2]) # legfest (alternate the messages depending on the month)
        elif now.day == 31 and now.month == 10: self.push_notif("Happy Halloween!")
        elif now.day == 25 and now.month == 12: self.push_notif("Happy Christmas!")
        elif now.day == 1 and now.month == 1: self.push_notif("Happy New Year!")
        elif now.day == 14 and now.month == 2: self.push_notif("Happy Valentine!")
        elif now.day == 10 and now.month == 3: self.push_notif("Another year on Granblue Fantasy...")
        elif now.day == 1 and now.month == 4: self.push_notif("???")
        elif now.day == 29 and now.month == 4: self.push_notif("Golden Week is starting!")
        elif savedata is None: self.push_notif("First time user? Take a look at the readme!")
        else: self.push_notif("May luck be with you.") # random welcome message
        
        # end
        if self.check_python(self.python) is False:
            errors.append("Your Python version is outdated ({}.{}). Consider uninstalling it for a recent version.".format(sys.version_info.major, sys.version_info.minor))
        self.top_tab.grid(row=0, column=0, columnspan=10, sticky="wnes")
        if savedata is not None: errors += self.apply_savedata(savedata)
        if self.last_tab in self.tab_tree:
            t = self.tab_tree[self.last_tab]
            self.top_tab.select(t[0]) # select top tab
            t[2].select(t[1]) # select sub tab on stored notebook
        for rn, v in self.settings.get("detached", {}).items():
            self.detach(rn, v)
        if len(errors) > 0:
            if len(errors) > 6:
                tmp = ["And {} more errors...".format(len(errors)-6)]
                errors = errors[:6] + tmp
            messagebox.showerror("Important", "The following warnings/errors occured during startup:\n- " + "\n- ".join(errors) + "\n\nIt's recommended to close the app and fix those issues, if possible.")
        elif self.settings.get("check_update", 0) == 1:
            self.check_new_update()
        self.last_savedata_string = str(self.get_save_data()) # get current state of the save as a string
        self.after(60000, self.save_task)

    def set_general_binding(self, widget : Tk.Tk, limit_to : Optional[list] = None) -> None: # set shortcut keys to given widget/window
        key_bindings = [
            ('t', self.key_toggle_topmost),
            ('s', self.key_toggle_stat),
            ('l', self.key_toggle_theme),
            ('n', self.key_toggle_notif),
            ('e', self.key_open_editor),
            ('r', self.key_restart),
            ('u', self.key_update),
            ('m', self.key_memorize),
            ('o', self.key_open_memorized),
            ('c', self.key_close_popups),
        ]
        for k in key_bindings:
            if limit_to is None or k[0] in limit_to:
                widget.bind('<{}>'.format(k[0]), k[1])
                widget.bind('<{}>'.format(k[0].upper()), k[1])
        if limit_to is None:
            for k in ['<Prior>', '<Next>', '<Left>', '<Right>', '<Up>', '<Down>']: widget.bind(k, self.key_page)
            for i in range(1, 13): widget.bind('<Shift-F{}>'.format(i), self.key_set_fav)
            for i in range(1, 13): widget.bind('<F{}>'.format(i), self.key_select_fav)

    def set_tab_content(self, parent : Tk.Tk, layout : dict, container : dict, is_main_window : bool) -> None: # contruct a tab content (used by popup windows too)
        rn = layout["text"]
        frame = ttk.Frame(parent)
        frame.grid(row=0, column=0)
        button = self.make_button(frame, "", None, 0, 0, 1, "w", ("buttons", layout.get("raid_image", ""), self.BIG_THUMB))
        button.bind('<Button-1>', lambda ev, btn=button, rn=rn: self.count(btn, rn, "", add=True))
        button.bind('<Button-3>', lambda ev, btn=button, rn=rn: self.count(btn, rn, "", add=False))
        label = Tk.Label(frame, text="0") # Total label
        label.grid(row=1, column=0)
        hist = Tk.Label(frame, text="") # History label
        hist.grid(row=4, column=3 if is_main_window else 1, columnspan=100, sticky="w")
        container[""] = [0, label, hist, frame, layout, None] # the "" key is used for the total. this value contains: total counter, its label, the history label, the tab frame, the container frame, the detach button and the window if open
        # check for chest in the list
        if is_main_window:
            chest = None
            for l in layout.get("loot", []):
                if l.replace(".png", "") in self.CHESTS:
                    chest = l
                    self.got_chest[rn] = chest
                    break
        else:
            chest = self.got_chest.get(rn, None)
        # texts
        Tk.Label(frame, text="Total").grid(row=2, column=0)
        Tk.Label(frame, text="Chest" if chest is not None else "").grid(row=3, column=0)
        # build button and label list
        for i, l in enumerate(layout.get("loot", [])):
            if l.endswith(".png"): l = l[:-3] # strip extension to avoid possible weird behaviors
            if l in container or l == "" or (l in self.CHESTS and l != chest):
                continue
            if is_main_window and l in self.RARES:
                if rn not in self.got_rare: self.got_rare[rn] = []
                self.got_rare[rn].append(l)
            button = self.make_button(frame, "", None, 0, i+1, 1, "w", ("buttons", l, self.BIG_THUMB))
            button.bind('<Button-1>', lambda ev, btn=button, rn=rn, l=l: self.count(btn, rn, l, add=True))
            button.bind('<Button-3>', lambda ev, btn=button, rn=rn, l=l: self.count(btn, rn, l, add=False))
            d = [0, None, None] # other buttons got two labels (count and percent)
            d[1] = Tk.Label(frame, text="0")
            d[1].grid(row=1, column=i+1)
            d[2] = Tk.Label(frame, text="0%")
            d[2].grid(row=2, column=i+1)
            if chest is not None and l != chest:
                d.append(Tk.Label(frame, text="0%"))
                d[3].grid(row=3, column=i+1)
            container[l] = d
        if is_main_window:
            self.make_button(frame, "0", lambda rn=rn: self.reset(rn), 4, 0, 1, "we", ("others", "reset", self.SMALL_THUMB))
            self.make_button(frame, "P", lambda rn=rn: self.detach(rn), 4, 1, 1, "we", ("others", "detach", self.SMALL_THUMB), width=50)
            self.make_button(frame, "H", lambda rn=rn: self.show_history(rn), 4, 2, 1, "we", ("others", "history", self.SMALL_THUMB), width=50)

    def make_button(self, parent : Tk.Tk, text : str, command : Optional[Callable], row : int, column : int, columnspan : int, sticky : str, asset_tuple : Optional[tuple] = None, width : Optional[int] = None, height : Optional[int] = None) -> Tk.Button: # function to make our buttons. Asset tuple is composed of 3 elements: folder, asset name and a size tuple (in pixels)
        if asset_tuple is not None:
            asset = self.load_asset("assets/" + asset_tuple[0] + "/" + asset_tuple[1].replace(".png", "") + ".png", asset_tuple[2])
        else:
            asset = None
        button = Tk.Button(parent, image=asset, text=text, compound=Tk.LEFT, command=command, width=width, height=height)
        button.grid(row=row, column=column, columnspan=columnspan, sticky=sticky)
        return button

    def load_asset(self, path : str, size : tuple = None) -> Optional[PhotoImage]: # load an image file (if not loaded) and return it. If error/not found, return None or an empty image of specified size
        try:
            if path not in self.assets:
                self.assets[path] = PhotoImage(file=path)
            return self.assets[path]
        except:
            if size is None:
                return None
            else:
                try: 
                    if '__dummy_photo_image__'+str(size) not in self.assets: # keep a reference or it won't work
                        self.assets['__dummy_photo_image__'+str(size)] = Tk.PhotoImage(width=size[0], height=size[1])
                    return self.assets['__dummy_photo_image__'+str(size)]
                except Exception as e:
                    print("".join(traceback.format_exception(type(e), e, e.__traceback__)))

    def check_python(self, string) -> Optional[bool]: # check the python version against a version string. Return True if valid, False if outdated, None if error
        try:
            pver = string.split('.')
            if sys.version_info.major != int(pver[0]) or sys.version_info.minor < int(pver[1]):
                return False
            else:
                return True
        except:
            return None

    def verify_layout(self, layout : dict) -> list: # verify the layout for errors
        errors = []
        raid_data = {}
        got_chest = {}
        for ti, t in enumerate(layout):
            for c, r in enumerate(t.get("raids", [])): # raid tabs
                if "text" not in r:
                    errors.append("Raid '{}' doesn't have a 'Text' value in Tab '{}'".format(c, ti+1))
                    continue
                elif r["text"] in raid_data:
                    errors.append("Duplicate raid name '{}' in Tab '{}'".format(r["text"], ti+1))
                    continue
                else:
                    rn = r["text"]
                    if rn in self.FORBIDDEN:
                        errors.append("Raid name '{}' is forbidde in Tab '{}'".format(rn, ti+1))
                        continue
                    else:
                        raid_data[rn] = {}
                        # check for chest in the list
                        chest = None
                        for l in r.get("loot", []):
                            if l.replace(".png", "") in self.CHESTS:
                                chest = l
                                got_chest[rn] = chest
                                break
                        for i, l in enumerate(r.get("loot", [])):
                            if l.endswith(".png"): l = l[:-3] # strip extension to avoid possible weird behaviors
                            if l in raid_data[rn]:
                                errors.append("Raid {} '{}' in Tab '{}': '{}' is present twice in the loot list".format(c+1, rn, ti+1, l))
                                continue
                            elif l == "":
                                errors.append("Raid {} '{}' in Tab '{}': There is an empty string or an extra slash '/'".format(c+1, rn, ti+1))
                                continue
                            elif l in self.CHESTS and l != chest:
                                errors.append("Raid {} '{}' in Tab '{}': Only one chest button supported per raid".format(c+1, rn, ti+1))
                                continue
                            raid_data[rn][l] = None
        if len(errors) > 8: errors = errors[:8] + ["And more..."] # limit to 8 error messages
        return errors

    def key_toggle_topmost(self, ev : Tk.Event) -> None: # shortcut to toggle top most option
        self.top_most.set(not self.top_most.get())
        self.toggle_topmost()

    def key_toggle_stat(self, ev : Tk.Event) -> None: # shortcut to toggle stat window
        if self.stats_window is None: self.stats()
        else: self.stats_window.close()

    def key_toggle_theme(self, ev : Tk.Event) -> None: # shortcut to toggle theme
        self.toggle_theme()

    def key_toggle_notif(self, ev : Tk.Event) -> None: # shortcut to toggle the notification bar
        self.show_notif.set(not self.show_notif.get())
        self.toggle_notif()

    def key_open_editor(self, ev : Tk.Event) -> None: # shortcut to open the layout editor
        self.open_layout_editor()

    def key_restart(self, ev : Tk.Event) -> None: # shortcut to restart the app
        self.restart()

    def key_update(self, ev : Tk.Event) -> None: # shortcut to check for update
        self.check_new_update(False)

    def key_memorize(self, ev : Tk.Event) -> None: # shortcut to memorize popup positions
        memorized = {}
        for rname in self.raid_data: # check opened windows and save their positions
            if self.raid_data[rname][""][5] is not None:
                memorized[rname] = [self.raid_data[rname][""][5].winfo_rootx()-self.settings.get('offset', [0, 0])[0], self.raid_data[rname][""][5].winfo_rooty()-self.settings.get('offset', [0, 0])[1]] # save the positions
        if len(memorized) > 0 and messagebox.askquestion(title="Memorize", message="Do you want to save the positions of currently opened Raid popups?\nYou'll then be able to open them anytime using the 'O' key.") == "yes":
            self.settings['memorized'] = memorized
            self.modified = True
            self.push_notif("Popup Layout has been saved.")

    def key_open_memorized(self, ev : Tk.Event) -> None: # shortcut to load memorized popup positions
        opened = False
        for rname, p in self.settings.get('memorized', {}).items():
            if rname in self.raid_data:
                self.detach(rname, p)
                opened = True
        if opened:
            self.push_notif("Popups have been opened to their saved positions.")
        else:
            self.push_notif("No Popup Layout saved. Use the 'M' key to save one.")

    def key_close_popups(self, ev : Tk.Event) -> None: # shortcut to close opened raid popups
        closed = False
        for rname in self.raid_data: # check opened windows and save their positions
            if self.raid_data[rname][""][5] is not None:
                self.raid_data[rname][""][5].close()
                closed = True
        if closed:
            self.push_notif("Popups have been closed.")

    def key_page(self, ev : Tk.Event) -> None:  # key shortcut to change tabs
        top_pos = self.top_tab.index("current")
        top_len = len(self.top_tab.winfo_children())
        current_tab = self.top_tab.nametowidget(self.top_tab.select()).winfo_children()[0]
        if ev.keycode in [33, 38]:
            self.top_tab.select((top_pos - 1 + top_len) % top_len)
        elif ev.keycode in [34, 40]:
            self.top_tab.select((top_pos + 1) % top_len)
        if ev.keycode == 37:
            if isinstance(current_tab, ttk.Notebook):
                sub_pos = current_tab.index("current")
                sub_len = len(current_tab.winfo_children())
                current_tab.select((sub_pos - 1 + sub_len) % sub_len)
        elif ev.keycode == 39:
            if isinstance(current_tab, ttk.Notebook):
                sub_pos = current_tab.index("current")
                sub_len = len(current_tab.winfo_children())
                current_tab.select((sub_pos +1) % sub_len)

    def key_set_fav(self, ev : Tk.Event) -> None: # set a favorite
        while len(self.favorites) < 12: self.favorites.append(None) # set
        index = ev.keycode-112
        top_pos = self.top_tab.index("current")
        current_tab = self.top_tab.nametowidget(self.top_tab.select()).winfo_children()[0]
        if isinstance(current_tab, ttk.Notebook):
            sub_pos = current_tab.index("current")
            for k, v in self.tab_tree.items():
                if v[0] == top_pos and v[1] == sub_pos:
                    self.favorites[index] = k
                    self.modified = True
                    self.push_notif("'F{}' key set to '{}'.".format(index+1, k))
                    return

    def key_select_fav(self, ev : Tk.Event) -> None: # load a favorite
        index = ev.keycode-112
        try:
            t = self.tab_tree[self.favorites[index]]
            self.top_tab.select(t[0]) # select top tab
            t[2].select(t[1]) # select sub tab on stored notebook
        except:
            pass

    def save_task(self) -> None: # run alongside the loop : save and then run again in 60s
        self.save()
        self.after(60000, self.save_task)

    def clean_notif_task(self) -> None: # run alongside the loop: clean the notification bar
        try: self.notification.config(text="")
        except: pass

    def close(self) -> None: # called when we close the window
        if "detached" not in self.settings: self.settings['detached'] = {}
        for rname in self.raid_data: # check opened windows and save their positions
            if self.raid_data[rname][""][5] is not None:
                self.settings["detached"][rname] = [self.raid_data[rname][""][5].winfo_rootx()-self.settings.get('offset', [0, 0])[0], self.raid_data[rname][""][5].winfo_rooty()-self.settings.get('offset', [0, 0])[1]] # save their positions
                self.raid_data[rname][""][5].close()
                self.modified = True
            elif rname in self.settings['detached']:
                del self.settings['detached'][rname]
        self.save() # last save attempt
        if self.stats_window is not None: self.stats_window.close()
        if self.import_window is not None: self.import_window.close()
        if self.editor_window is not None: self.editor_window.close()
        if self.history_window is not None: self.history_window.close()
        for rname in self.raid_data:
            if self.raid_data[rname][""][5] is not None:
                self.raid_data[rname][""][5].close()
        self.destroy()

    def load_raids(self) -> tuple: # load raids.json
        errors = []
        try:
            with open('assets/raids.json', mode='r', encoding='utf-8') as f:
                data = json.load(f)
            if '-debug_raid' in sys.argv: # used to update DEFAULT_LAYOUT
                with open('debug_raid.txt', mode='w', encoding='utf-8') as g:
                    g.write(str(data))
                    print('debug_raid.txt created')
            self.og_raidlayout = (str(data) == self.DEFAULT_LAYOUT)
        except Exception as e:
            data = []
            errors = ["Error in raids.json: " + str(e)]
        return data, errors

    def toggle_checkupdate(self) -> None: # toggle check for update option
        self.modified = True
        self.settings["check_update"] = self.check_update.get()

    def toggle_topmost(self) -> None: # toggle always on top option
        self.modified = True
        self.settings["top_most"] = self.top_most.get()
        if self.settings["top_most"] == 1:
            self.attributes('-topmost', True)
            if self.stats_window is not None: self.stats_window.attributes('-topmost', True)
            if self.import_window is not None: self.import_window.attributes('-topmost', True)
            if self.editor_window is not None:
                self.editor_window.attributes('-topmost', True)
                if self.editor_window.preview is not None: self.editor_window.preview.attributes('-topmost', True)
            if self.history_window is not None: self.history_window.attributes('-topmost', True)
            for rname in self.raid_data:
                if self.raid_data[rname][""][5] is not None:
                    self.raid_data[rname][""][5].attributes('-topmost', True)
            self.push_notif("Windows will always be on top.")
        else:
            self.attributes('-topmost', False)
            if self.stats_window is not None: self.stats_window.attributes('-topmost', False)
            if self.import_window is not None: self.import_window.attributes('-topmost', False)
            if self.editor_window is not None:
                self.editor_window.attributes('-topmost', False)
                if self.editor_window.preview is not None: self.editor_window.preview.attributes('-topmost', False)
            if self.history_window is not None: self.history_window.attributes('-topmost', False)
            for rname in self.raid_data:
                if self.raid_data[rname][""][5] is not None:
                    self.raid_data[rname][""][5].attributes('-topmost', False)
            self.push_notif("Windows won't be on top.")

    def toggle_notif(self) -> None: # toggle for notifications
        self.modified = True
        self.settings["show_notif"] = self.show_notif.get()
        if self.settings["show_notif"] == 1:
            self.notification.grid(row=1, column=0, sticky="w")
            self.push_notif("Notifications will appear here.")
        else:
            self.notification.grid_forget()

    def toggle_backup(self) -> None: # toggle save backup
        self.modified = True
        self.settings["backup_save"] = self.backup_save.get()

    def push_notif(self, text : str) -> None: # edit the notification label and reset the counter
        self.notification.config(text=text)
        if self.notification_after is not None: self.after_cancel(self.notification_after)
        self.notification_after = self.after(4000, self.clean_notif_task) # delete after 4s

    def toggle_theme(self) -> None: # toggle the theme
        try:
            for i in range(len(self.THEME)): # search the theme
                if self.THEME[i] == self.settings.get("theme", self.THEME[0]):
                    self.settings["theme"]= self.THEME[(i+1)%len(self.THEME)] # switch to the next one
                    self.call("set_theme", self.settings["theme"])
                    self.push_notif("Theme set to '{}'.".format(self.settings["theme"]))
                    self.modified = True
                    return
            # not found
            self.settings["theme"] = self.THEME[-1]
            self.toggle_theme()
        except Exception as e:
            print("".join(traceback.format_exception(type(e), e, e.__traceback__)))

    @contextmanager
    def button_press(self, button : Tk.Button) -> None: # context used for count(), to activate the button animation when right clicking
        button.config(relief=Tk.SUNKEN, state=Tk.ACTIVE)
        try:
            yield button
        finally:
            button.after(100, lambda: button.config(relief=Tk.RAISED, state=Tk.NORMAL))

    def count(self, button : Tk.Button, rname : str, target : str, add : bool) -> None: # add/substract a value. Parameters: button pressed, raid name, button target (will be empty string if it's the total button) and a boolean to control the addition/substraction
        with self.button_press(button):
            if rname in self.raid_data:
                self.last_tab = rname
                cname = self.got_chest.get(rname, None) # chest name
                if not add: # only for substraction: take note of total normal item
                    total_item = 0
                    for k in self.raid_data[rname]:
                        if k == "" or k.replace(".png", "")  == cname:
                            pass
                        else:
                            total_item += self.raid_data[rname][k][0]
                if target != "" and target in self.raid_data[rname]:
                    # add/sub to item value
                    if add:
                        self.raid_data[rname][target][0] += 1
                        if target in self.RARES: # add new point to history if rare item
                            self.add_to_history(rname, target, self.raid_data[rname][target][0], self.raid_data[rname][""][0]+1 if rname not in self.got_chest else self.raid_data[rname][self.got_chest[rname]][0]+1)
                    else:
                        if (target.replace(".png", "") == cname and self.raid_data[rname][target][0] <= total_item) or self.raid_data[rname][target][0] == 0: return # can't decrease if it's a chest button and its value is equal to total of other items OR if its value is simply ZERO
                        self.raid_data[rname][target][0] = self.raid_data[rname][target][0] - 1
                    # chest button editing
                    if cname is not None and target.replace(".png", "") != cname: # if we haven't pressed the chest button or the total button, we increase the chest value
                        if cname in self.raid_data[rname]: # check again
                            if add:
                                self.raid_data[rname][cname][0] += 1
                            else:
                                self.raid_data[rname][cname][0] = max(0, self.raid_data[rname][cname][0] - 1)
                # total button editing
                if add:
                    self.raid_data[rname][""][0] += 1
                else:
                    if target == "" and self.raid_data[rname][""][0] <= total_item: return
                    self.raid_data[rname][""][0] = max(0, self.raid_data[rname][""][0] - 1)
                # done
                self.modified = True
                self.update_raid_ui(rname)

    def reset(self, rname : str) -> None: # raid name
        if messagebox.askquestion(title="Reset", message="Do you want to reset this tab?") == "yes": #ask for confirmation to avoid  accidental data reset
            if rname in self.raid_data:
                self.last_tab = rname
                for k in self.raid_data[rname]:
                    self.raid_data[rname][k][0] = 0
                self.modified = True
                self.update_raid_ui(rname)
                self.push_notif("Raid '{}' has been reset.".format(rname))

    def update_raid_ui(self, rname : str) -> None: # called by count() and reset()
        if self.raid_data[rname][""][5] is not None: # update detached window if it exists
            for k in self.raid_data[rname]:
                self.raid_data[rname][""][5].data[k][0] = self.raid_data[rname][k][0]
        self.update_label(rname) # update the labels for this raid
        if self.stats_window is not None: self.stats_window.update_data() # update stats window if open
        if self.history_window is not None and rname == self.history_window.rname: # update history window is open
            self.history_window.update_history()

    def detach(self, rname : str, position : Optional[list] = None) -> None: # open popup for specified raid name
        if rname in self.raid_data:
            if self.raid_data[rname][""][5] is not None:
                self.raid_data[rname][""][5].lift()
                if position is not None:
                    self.raid_data[rname][""][5].setPosition(position[0], position[1])
            else:
                self.raid_data[rname][""][5] = DetachedRaid(self, rname, position)

    def show_history(self, rname : str) -> None: # open popup to show the history of the raid
        if rname in self.raid_data:
            if self.history_window is None:
                self.history_window = History(self, rname)
            else:
                self.history_window.destroy()
                self.history_window = History(self, rname)
        else:
            messagebox.showerror("Error", "History not available for this raid")

    def update_label(self, rname : str) -> None: # update the labels of the tab content
        if rname in self.raid_data:
            self.update_label_sub(rname, self.raid_data[rname])
            if self.raid_data[rname][""][5] is not None:
                self.update_label_sub(rname, self.raid_data[rname][""][5].data)

    def update_label_sub(self, rname : str, data : dict) -> None: # sub routine of update_label: can specify the target raid data
        total = data[""][0]
        chest_count = 0
        if rname in self.got_chest: # get total of chest
            chest_count = data[self.got_chest[rname]][0]
        data[""][1].config(text="{:,}".format(total))
        # update "since the last" label
        if rname in self.got_rare:
            k = self.got_rare[rname][0]
            v = chest_count if rname in self.got_chest else total
            r = (self.got_chest[rname] + " chests" if rname in self.got_chest else "battles").capitalize()
            if data[k][0] > 0:
                try:
                    h = self.history[rname][k][data[k][0]-1]
                    if h > 0 and h <= v:
                        data[""][2].config(text="{} {} since the last {}".format(v-h, r, k.capitalize()))
                    else:
                        data[""][2].config(text="")
                except:
                    data[""][2].config(text="")
            else:
                data[""][2].config(text="")
        else:
            data[""][2].config(text="")
        # update each button values and percentage
        for k, v in data.items():
            if k == "": continue
            i = v[0]
            v[1].config(text="{:,}".format(i))
            if total > 0:
                v[2].config(text="{:.2f}%".format(min(100, 100*float(i)/total)).replace('0%', '%').replace('.0%', '%'))
            else:
                v[2].config(text="0%")
            # chest percentage
            if rname in self.got_chest and len(v) == 4:
                if chest_count > 0:
                    v[3].config(text="{:.2f}%".format(min(100, 100*float(v[0])/chest_count)).replace('0%', '%').replace('.0%', '%'))
                else:
                    v[3].config(text="0%")

    def cmpVer(self, mver : str, tver : str) -> bool: # compare version strings, True if mver greater or equal, else False
        me = mver.split('.')
        te = tver.split('.')
        for i in range(0, min(len(me), len(te))):
            if int(me[i]) < int(te[i]):
                return False
        return True

    def check_new_update(self, silent : bool = True) -> None: # request the manifest file on github and compare the versions
        try:
            with urllib.request.urlopen("https://raw.githubusercontent.com/MizaGBF/GBFLT/main/assets/manifest.json") as url:
                data = json.loads(url.read().decode("utf-8"))
            if "version" in data and self.version != "0.0" and not self.cmpVer(self.version, data["version"]):
                if messagebox.askquestion(title="Update", message="An update is available.\nCurrent version: {}\nNew Version: {}\nDo you want to download and install?\n- 'save.json' and 'assets/raids.json' (if modified) will be kept intact.\n- Other files will be overwritten.".format(self.version, data["version"])) == "yes":
                    if self.check_python(data.get("python", "3.10")) is False:
                        if messagebox.askquestion("Outdated Python", "Your python version is v{}.{}.\nAt least Python v{} is recommended.\nUninstall python and install a more recent version.\nOpen the download page?".format(sys.version_info.major, sys.version_info.minor, data.get("python", "3.10"))) == "yes":
                            webbrowser.open("https://www.python.org/downloads/", new=2, autoraise=True)
                    else:
                        self.auto_update()
            elif not silent:
                messagebox.showinfo("Update", "GBF Loot Tracker is up-to-date.")
        except Exception as e:
            print("".join(traceback.format_exception(type(e), e, e.__traceback__)))
            if not silent:
                messagebox.showerror("Error", "An error occured while checking for new updates.\nCheck your Firewall, Try again later or go to Github and update manually.")

    def auto_update(self) -> None:
        try:
            # backup
            try:
                with open('assets/raids.json', mode='rb') as f:
                    data = f.read()
                with open('assets/raids-backup.json', mode='wb') as f:
                    f.write(data)
            except:
                pass
            try:
                with open('save.json', mode='rb') as f:
                    data = f.read()
                with open('save-backup.json', mode='wb') as f:
                    f.write(data)
            except:
                pass
            # download latest
            with urllib.request.urlopen(self.GITHUB+"/archive/refs/heads/main.zip") as url:
                data = url.read()
            # read
            with BytesIO(data) as zip_content:
                with zipfile.ZipFile(zip_content, 'r') as zip_ref:
                    # list files
                    folders = set()
                    file_list = zip_ref.namelist()
                    for file in file_list:
                        if ".git" in file: continue
                        folders.add("/".join(file.split('/')[1:-1]))
                    # make folders (if missing)
                    for path in folders:
                        if path == "": continue
                        os.makedirs(os.path.dirname(path if path.endswith("/") else path+"/"), exist_ok=True)
                    # write files
                    for file in file_list:
                        if ".git" in file: continue
                        if file.split("/")[-1] in ["raids.json", "save.json"] or file.endswith("/"): continue
                        path = "/".join(file.split('/')[1:])
                        with open(path, mode="wb") as f:
                            f.write(zip_ref.read(file))
                    # update raids.json
                    if self.og_raidlayout: # if unmodified
                        for file in file_list:
                            if file.endswith("raids.json"):
                                path = "/".join(file.split('/')[1:])
                                with open(path, mode="wb") as f:
                                    f.write(zip_ref.read(file))
                                break
                    else:
                        try:
                            with open('assets/raids.json', mode='r', encoding='utf-8') as f:
                                old = json.load(f)
                            # list known raids
                            changes = ""
                            for file in file_list:
                                if file.endswith("raids.json"):
                                    # load new json
                                    try:
                                        new = json.loads(zip_ref.read(file).decode('utf-8'))
                                    except:
                                        new = None
                                    if new is not None:
                                        # tab check
                                        for tn in new:
                                            found = False
                                            for i in range(len(old)):
                                                if old[i]["text"] == tn["text"]:
                                                    found = True
                                                    break
                                            if found: # tab exists
                                                for rn in tn["raids"]:
                                                    if rn["text"] not in self.raid_data:
                                                        old[i]["raids"].append(copy.deepcopy(rn))
                                                        changes += "Adding Raid '{}' to Tab '{}'\n".format(rn["text"], tn["text"])
                                            else: # tab doesn't exist
                                                new_tab = copy.deepcopy(tn)
                                                new_tab["raids"] = []
                                                for rn in tn["raids"]:
                                                    if rn["text"] not in self.raid_data:
                                                        new_tab["raids"].append(copy.deepcopy(rn))
                                                if len(new_tab["raids"]) > 0:
                                                    old.append(new_tab)
                                                    changes += "Adding Tab '{}'\n".format(tn["text"])
                                        if changes != "" and messagebox.askquestion(title="Update", message="Some differences have been detected between your 'assets/raids.json' and the one from the latest version:\n" + changes + "\nDo you want to apply those differences to your 'assets/raids.json'?") == "yes":
                                            try:
                                                json.dumps(str(old)) # check for validity
                                                with open('assets/raids.json', mode='w', encoding='utf-8') as f:
                                                    json.dump(old, f, indent=4, ensure_ascii=False)
                                                messagebox.showinfo("Update", "'assets/raids.json' updated.\nUse the Layout Editor to make further modifications.")
                                            except Exception as ee:
                                                print("".join(traceback.format_exception(type(ee), ee, ee.__traceback__)))
                                                messagebox.showerror("Error", "Couldn't update 'assets/raids.json', it has been left untouched:\n" + str(ee))
                                    break
                        except:
                            if messagebox.askquestion(title="Update", message="An error occured while attempting to detect differences between your 'assets/raids.json' and the one from the latest version.\nDo you want to replace your 'assets/raids.json' with the new one?") == "yes":
                                for file in file_list:
                                    if file.endswith("raids.json"):
                                        new = json.loads(zip_ref.read(file).decode('utf-8'))
                                        with open('assets/raids.json', mode='w', encoding='utf-8') as f:
                                            json.dump(new, f, indent=4, ensure_ascii=False)
                                        break
            messagebox.showinfo("Update", "Update successful.\nThe application will now restart.\nIf you need to, you'll find backups of 'save.json' and 'assets/raids.json' near them.")
            self.restart()
        except Exception as e:
            print("".join(traceback.format_exception(type(e), e, e.__traceback__)))
            messagebox.showerror("Error", "An error occured while downloading or installing the update:\n" + str(e))

    def load_manifest(self) -> list: # load data from manifest.json (only the version number for now)
        try:
            with open("assets/manifest.json", mode="r", encoding="utf-8") as f:
                data = json.load(f)
                self.version = data["version"]
                self.python = data["python"]
            return []
        except Exception as e:
            print("".join(traceback.format_exception(type(e), e, e.__traceback__)))
            return ["Couldn't read 'assets/manifest.json'"]

    def load_savedata(self) -> tuple: # load save.data, return a tuple of the savedata (None if error) and an error list
        errors = []
        try:
            with open("save.json", mode="r", encoding="utf-8") as f:
                savedata = json.load(f)
            savedata = self.check_history(savedata)
            if not self.cmpVer(self.version, savedata["version"]):
                errors.append("Your save data comes from a more recent version. It might causses issues")
            if len(errors) == 0 and savedata.get("settings", {}).get("backup_save", 0):
                try: shutil.copyfile("save.json", "save-backup.json")
                except Exception as x: errors.append("Error while makine a save.json backup: " + str(x))
            return savedata, errors
        except Exception as e:
            print("".join(traceback.format_exception(type(e), e, e.__traceback__)))
            if "No such file or directory" not in str(e):
                errors.append("Error while opening save.json: " + str(e))
            return None, errors

    def check_history(self, savedata : dict) -> dict: # check the history in the savedata and updates it if needed
        if 'history' not in savedata:
            savedata["history"] = {}
        for k, v in savedata.items():
            if k in self.FORBIDDEN: continue
            for x, y in v.items():
                if x in self.RARES:
                    if k not in savedata["history"]: savedata["history"][k] = {}
                    if x not in savedata["history"][k]: savedata["history"][k][x] = []
                    while len(savedata["history"][k][x]) < y: # add data if missing (for prior versions)
                        savedata["history"][k][x].insert(0, 0)
                    if len(savedata["history"][k][x]) > y: # remove extra data
                        savedata["history"][k][x] = savedata["history"][k][x][:y]
        return savedata

    def add_to_history(self, rname : str, iname : str, val : int, total : int): # add a new point in time to a raid history
        if rname not in self.history: self.history[rname] = {}
        if iname not in self.history[rname]: self.history[rname][iname] = []
        while len(self.history[rname][iname]) < val: self.history[rname][iname].append(0)
        self.history[rname][iname][val-1] = total

    def apply_savedata(self, savedata : dict) -> list: # set raid labels, etc...
        errors = []
        missing = False
        self.last_tab = savedata.get("last", None)
        for k, v in savedata.items(): # set each raid
            if k in self.FORBIDDEN: continue
            if k in self.raid_data:
                for x, y in v.items():
                    if x in self.raid_data[k]:
                        self.raid_data[k][x][0] = y
                    else:
                        errors.append("Loot '{}' from raid '{}' isn't in use anymore and will be discarded in the next save data.".format(x, k)) # warning
            else:
                self.history.pop(k, None)
                if not missing:
                    missing = True
                    errors.append("Raid '{}' isn't in use anymore and will be discarded in the next save data.".format(k)) # warning
            self.update_label(k)
        return errors

    def save(self) -> None: # update save.json
        if self.modified:
            self.modified = False
            savedata = self.get_save_data()
            savedata_string = str(savedata)
            if savedata_string != self.last_savedata_string:
                self.last_savedata_string = savedata_string
                try:
                    with open("save.json", mode="w", encoding="utf-8") as f:
                        json.dump(savedata, f)
                    self.push_notif("Changes have been saved.")
                except Exception as e:
                    print("".join(traceback.format_exception(type(e), e, e.__traceback__)))
                    messagebox.showerror("Error", "An error occured while saving:\n"+str(e))

    def get_save_data(self) -> dict: # build the save data (as seen in save.json) and return it
        savedata = {"version":self.version, "last":self.last_tab, "settings":self.settings, "history":self.history, "favorites":self.favorites}
        for k, v in self.raid_data.items():
            savedata[k] = {}
            for x, y in v.items():
                savedata[k][x] = y[0]
        return savedata

    def open_layout_editor(self) -> None: # open assets/layout_editor.pyw
        if self.editor_window is not None: self.editor_window.lift()
        else: self.editor_window = Editor(self)

    def restart(self) -> None: # retsart the app (used to check layout changes)
        try:
            self.save()
            subprocess.Popen([sys.executable, sys.argv[0]])
            self.close()
        except Exception as e:
            messagebox.showerror("Error", "An error occured while attempting to restart the application:\n"+str(e))

    def stats(self) -> None: # open the stats window
        if self.stats_window is not None: self.stats_window.lift()
        else: self.stats_window = StatScreen(self)

    def github_repo(self) -> None: # open the github repo
        webbrowser.open(self.GITHUB, new=2, autoraise=True)
        self.push_notif("Link opened in your broswer.")

    def github_issue(self) -> None: # open the github repo on the issues page
        webbrowser.open(self.GITHUB+"/issues", new=2, autoraise=True)
        self.push_notif("Link opened in your broswer.")

    def show_shortcut(self) -> None: # open shortcut list
        messagebox.showinfo("Keyboard Shortcuts", "- T: Toggle the Always on top settings.\n- S: Toggle the Statistics window.\n- L: Toggle the Light and Dark themes.\n- N: Toggle the Notification Bar.\n- E: Open the Layout Editor.\n- R: Restart the application.\n- U: Check for updates.\n- M: Memorize the currently opened Raid Popups positions.\n- O: Open the memorized Raid popups to their saved positions.\n- C: Close all opened Raid popups.\n- Page Up or Up: Go to the top tab on the left.\n- Page Down or Down: Go to the top tab on the right.\n- Left: Go to the raid on the left.\n- Right: Go to the raid on the right.\n- Shit+F1~F12: Set the current raid to the Function Key pressed.\n- F1~F12: Go to the raid associated to this Function key.")

    def show_favorite(self) -> None: # favorite list
        msg = ""
        for i in range(12):
            if len(self.favorites) < i+1: self.favorites.append(None)
            msg += "F{}: {}\n".format(i+1, self.favorites[i])
        msg += "\nUse Shift+F1~F12 on a raid tab to set.\nAnd then the F1~F12 key itself to go quickly to that raid."
        messagebox.showinfo("Favorited Raids", msg)

    def show_changelog(self) -> None: # display the changelog
        changelog = [
            "1.55 - Fixed the Auto Update doing nothing.",
            "1.54 - Fixed the Popup and Statistics not being updated upon using the Reset button, and the History crashing if open.",
            "1.53 - Removed Reset buttons on Raid Popups. Fixed Raid Popups moving slightly on reboot (To do so, the offset is calculated once on the app startup).",
            "1.52 - Fixed a bug and tweaked the UI of the History window.",
            "1.51 - Added History window and Save Backup setting.",
            "1.50 - Added thousand separators for big numbers. Fixed some very minor UI issues.",
            "1.49 - Added raid thumbnails to stat screen.",
            "1.48 - The statistics window is now more detailed.",
            "1.47 - Raid tabs size is reduced if more than six raids are present in the same category.",
            "1.46 - Fixed keyboard navigation not working on tabs after clicking a tab."
        ]
        messagebox.showinfo("Changelog - Last Ten versions", "\n".join(changelog))

    def show_credits(self) -> None: # show credits
        messagebox.showinfo("Credits", "https://github.com/MizaGBF/GBFLT\nAuthor:\n- Mizako\n\nContributors:\n- Zell (v1.6)\n\nTesting:\n- Slugi\n\nVisual Themes:\nhttps://github.com/rdbende/Azure-ttk-theme\nhttps://github.com/rdbende/Forest-ttk-theme")

    def export_to_text(self) -> None: # export data to text
        today = datetime.now()
        report = "GBFLT {} - Loot Data Export\r\n{}\r\n\r\n".format(self.version, today.strftime("%d/%m/%Y %H:%M:%S"))
        for k, v in self.raid_data.items():
            if v[""][0] == 0: continue
            report += "### Raid {:} - {:,} times\r\n".format(k, v[""][0])
            cname = self.got_chest.get(k, "")
            total = v[cname][0]
            for x, y in v.items():
                if x == "": continue
                report += "- {:} - {:,} times".format(x, y[0])
                if x != cname: report += " ({:.2f}%)".format(100*y[0]/total).replace('0%', '%').replace('.0%', '%')
                report += "\r\n"
            if k in self.history:
                add = ""
                for x, y in self.history[k].items():
                    if len(y) == 0: continue
                    add += "- {} at: ".format(x)
                    for e in y:
                        if e <= 0: add += "?, "
                        else: add += "{}, ".format(e)
                    add = add[:-2]
                    add += "\r\n"
                if add != "":
                    report += "Drop History:\r\n" + add
            report += "\r\n"
        with open("drop_export_{}.txt".format(today.strftime("%m-%d-%Y_%H-%M-%S.%f")), mode="w", encoding="utf-8") as f:
            f.write(report)
        messagebox.showinfo("Info", "Data exported to: drop_export_{}.txt".format(today.strftime("%m-%d-%Y_%H-%M-%S.%f")))

    def import_data(self) -> None: # import data from other trackers
        if self.import_window is not None: self.import_window.lift()
        else: self.import_window = ImportDial(self)

class ImportDial(Tk.Toplevel):
    def __init__(self, parent : Tracker) -> None:
        # window
        self.parent = parent
        Tk.Toplevel.__init__(self,parent)
        self.title("GBF Loot Tracker - Data Import")
        self.resizable(width=False, height=False) # not resizable
        self.minsize(self.parent.MIN_WIDTH, self.parent.MIN_HEIGHT)
        self.iconbitmap('assets/icon.ico')
        if self.parent.settings.get("top_most", 0) == 1:
            self.attributes('-topmost', True)
        
        Tk.Label(self, text="You can import some raid data from other similar trackers.").grid(row=0, column=0, columnspan=10, sticky="w")
        Tk.Button(self, text="'Gold-Bar-Tracker'", command=lambda : self.import_data(0)).grid(row=1, column=0, columnspan=10, sticky="we") # only this one so far
        
        Tk.Label(self, text="Your tracker missing? Please notify us.").grid(row=10, column=0, columnspan=10, sticky="w")

    def import_data(self, sid : int) -> None: # importer
        if sid == 0: # DYDK GBTracker
            messagebox.showinfo("Info", "Please select 'data.json' to import the data.\nIts content will be added to your existing data.\nCancel or Backup your 'save.json' if you're uncertain.")
            path = filedialog.askopenfilename()
            if path != "":
                try:
                    with open(path, mode="r", encoding="utf-8") as f:
                        data = json.load(f)
                    matching_table = {
                        "pbhl": "BHL",
                        "akasha": "Akasha",
                        "gohl": "Grande",
                        "dragon": "6D",
                        "subhl": "SuBaha",
                        "coronaring": "blue",
                        "lineagering": "blue",
                        "intricacyring": "ring3",
                        "goldbar": "bar",
                        "hollowkey": "blue",
                        "azurite": "blue",
                        "trash": "blue",
                        "earring": "fireearring",
                        "sand": "sand",
                        "raid": ""
                    }
                    modified = False
                    for k, v in data.items():
                        if "raid" in v and matching_table.get(k, "_undefined_match_") in self.parent.raid_data:
                            if v["raid"] != 0:
                                for x, y in v.items():
                                    i = matching_table.get(x, None)
                                    if i is None: continue
                                    if i == "blue" and "blue" not in self.parent.raid_data[matching_table[k]]: i = ""
                                    self.parent.raid_data[matching_table[k]][i][0] += y
                                    modified = True
                                self.parent.update_label(matching_table[k])
                    if modified:
                        messagebox.showinfo("Info", "Data has been imported with success, when possible.\nNote: Gold Bar and Sand tracking might be incorrect until the next restart.")
                    else:
                        messagebox.showinfo("Info", "No Data has been imported: No relevant data has been found.")
                except Exception as e:
                    print("".join(traceback.format_exception(type(e), e, e.__traceback__)))
                    messagebox.showinfo("Error", "An error occured.\nThe process might have been inturrepted mid-wayt by this error:\n" + str(e) + "\n\nDid you select the right file? If so, the format might have changed, please notify us the issue.")
        self.close()

    def close(self) -> None: # called on close
        self.destroy()

class DetachedRaid(Tk.Toplevel): # detached raid window
    def __init__(self, parent : Tracker, rname : str, position : Optional[list] = None) -> None:
        # window
        self.parent = parent
        Tk.Toplevel.__init__(self,parent)
        self.title(rname)
        self.resizable(width=False, height=False) # not resizable
        self.minsize(self.parent.MIN_WIDTH, self.parent.MIN_HEIGHT)
        self.iconbitmap('assets/icon.ico')
        self.protocol("WM_DELETE_WINDOW", self.close) # call close() if we close the window
        if self.parent.settings.get("top_most", 0) == 1:
            self.attributes('-topmost', True)
        self.rname = rname
        self.data = {}
        self.parent.set_tab_content(self, self.parent.raid_data[self.rname][""][4], self.data, False) # fill window
        for k in self.parent.raid_data[self.rname]: # mirror values
            self.data[k][0] = self.parent.raid_data[self.rname][k][0]
        self.parent.update_label_sub(self.rname, self.data) # update the window
        self.parent.set_general_binding(self, ["t", "s", "l", "n", "m", "o", "c"])
        self.init_pos = None
        if position is not None: # set position if given
            self.setPosition(position[0], position[1])
        self.parent.modified = True

    def setPosition(self, x : int, y : int) -> None: # set window position
        ms = self.maxsize()
        self.geometry('+{}+{}'.format(min(max(x, 0), ms[0]-self.parent.MIN_WIDTH), min(max(y, 0), ms[1]-self.parent.MIN_HEIGHT))) # stay in screen bound
        self.init_pos = (min(max(x, 0), ms[0]-self.parent.MIN_WIDTH), min(max(y, 0), ms[1]-self.parent.MIN_HEIGHT))

    def close(self) -> None:
        self.parent.raid_data[self.rname][""][5] = None
        self.destroy()

class OffsetTester(Tk.Toplevel): # used to calculate windows offset on machine (check inside Tracker.__init__() for more details)
    def __init__(self, parent : Tracker) -> None:
        # create a simple windows
        self.parent = parent
        Tk.Toplevel.__init__(self,parent)
        self.title("Tester")
        self.resizable(width=False, height=False)
        self.minsize(self.parent.MIN_WIDTH, self.parent.MIN_HEIGHT)
        # set position to 100x100
        self.geometry('+100+100')

    def get_offset(self) -> list:
        self.update() # update once
        offset = [self.winfo_rootx()-100, self.winfo_rooty()-100] # get difference from initial position
        self.destroy() # destroy
        return offset  # return the values

class StatScreen(Tk.Toplevel): # stats window
    ITEM_COLUMN = 5
    TEXT_WIDTH = 5
    BOLD_FONT_MOD = 2
    RAID_TOP = 10
    def __init__(self, parent : Tracker) -> None:
        # window
        self.parent = parent
        Tk.Toplevel.__init__(self,parent)
        self.title("GBF Loot Tracker - Statistics")
        self.resizable(width=False, height=False) # not resizable
        self.iconbitmap('assets/icon.ico')
        self.protocol("WM_DELETE_WINDOW", self.close) # call close() if we close the window
        self.defaultfont = tkFont.nametofont('TkDefaultFont').actual() # used to make top label bold
        # base ui
        Tk.Label(self, text="Top cleared Raids", font=(self.defaultfont['family'], self.defaultfont['size']+self.BOLD_FONT_MOD, 'bold')).grid(row=0, column=0, columnspan=self.TEXT_WIDTH, sticky="w")
        Tk.Button(self, text="?", command=self.help).grid(row=0, column=self.TEXT_WIDTH*2-1, columnspan=1, sticky="we")
        self.frame = ttk.Frame(self)
        self.frame.grid(row=1, column=0, columnspan=self.TEXT_WIDTH*2, sticky="we")
        # start
        self.update_data()
        if self.parent.settings.get("top_most", 0) == 1:
            self.attributes('-topmost', True)
        self.parent.push_notif("Statistics opened.")

    def update_data(self) -> None: # update the data shown on the window
        # cleanup
        for child in self.frame.winfo_children(): # clean current elements
            child.destroy()
        # calculate stats
        data = {}
        total = {}
        raid_counts = {}
        for name, raid in self.parent.raid_data.items():
            chest = self.parent.got_chest.get(name, None)
            for loot, count in raid.items():
                data[loot] = data.get(loot, 0) + count[0]
                if loot == "" and count[0] > 0:
                    raid_counts[name] = count[0]
                    total[''] = total.get('', 0) + count[0]
                elif loot == chest or chest is None:
                    total[loot] = total.get(loot, 0) + raid[''][0]
                else:
                    total[loot] = total.get(loot, 0) + raid[chest][0]
        # sorted
        data = dict(sorted(data.items(), key=lambda item: item[1], reverse=True))
        raid_counts = dict(sorted(raid_counts.items(), key=lambda item: item[1], reverse=True))
        # display
        # raid ranking
        if len(raid_counts) > 0:
            count = 0
            for name, value in raid_counts.items():
                Tk.Label(self.frame, text="{:} - {:,} times ({:.2f}%)".format(name, value, 100 * value / data.get("", 1)).replace('0%', '%').replace('.0%', '%'), compound=Tk.LEFT, image=self.parent.load_asset("assets/tabs/" +self.parent.raid_data[name][""][4].get('raid_image', '').replace(".png", "") + ".png", self.parent.SMALL_THUMB)).grid(row=count%5, column=count//5*self.TEXT_WIDTH, columnspan=self.TEXT_WIDTH, sticky="w")
                count += 1
                if count >= self.RAID_TOP: break # stop
        ttk.Separator(self.frame, orient='horizontal').grid(row=self.RAID_TOP, column=0, columnspan=max(self.ITEM_COLUMN*2, self.TEXT_WIDTH*2), sticky="we") # separator to make it pretty
        # item data
        count = 0
        for loot, value in data.items():
            if value == 0: break
            asset = self.parent.load_asset("assets/buttons/" + (loot.replace(".png", "") if loot != "" else "unknown") + ".png", self.parent.BIG_THUMB)
            Tk.Label(self.frame, image=asset).grid(row=self.RAID_TOP + 1 + count // self.ITEM_COLUMN, column=count % self.ITEM_COLUMN * 2)
            Tk.Label(self.frame, text='{:,}\n{:.2f}%'.format(value, 100*value/float(total[loot])).replace('0%', '%').replace('.0%', '%') if loot != "" else "{:,}\nraids".format(value)).grid(row=self.RAID_TOP + 1 + count // self.ITEM_COLUMN, column=count % self.ITEM_COLUMN * 2 + 1)
            count += 1
        # message if no data
        if count == 0:
            Tk.Label(self.frame, text="No data available yet.\n\n", font=(self.defaultfont['family'], self.defaultfont['size']+self.BOLD_FONT_MOD, 'bold')).grid(row=self.RAID_TOP + 1, column=0, columnspan=self.TEXT_WIDTH, sticky="w")

    def help(self) -> None:
        messagebox.showinfo("Info", "Item percentages are calculated according to their corresponding total raid chests or raids (if no chest is present in said raid).")

    def close(self) -> None: # called on close
        self.parent.stats_window = None
        self.parent.push_notif("Statistics closed.")
        self.destroy()

class Editor(Tk.Toplevel): # editor window
    def __init__(self, parent : Tracker) -> None:
        self.parent = parent
        Tk.Toplevel.__init__(self,parent)
        self.title("GBF Loot Tracker - Layout editor")
        self.iconbitmap('assets/icon.ico')
        self.resizable(width=False, height=False) # not resizable
        self.protocol("WM_DELETE_WINDOW", self.close) # call close() if we close the window
        self.assets = {} # loaded images
        self.layout = self.load_raids() # load raids.json
        self.layout_string = str(self.layout) # and make a string out of it to detect modifications
        self.parent.make_button(self, "Verify and save changes", self.save, 0, 0, 3, "we", ("others", "save", self.parent.SMALL_THUMB))
        self.parent.make_button(self, "Add Tab", self.insert_tab, 1, 0, 1, "we", ("others", "add", self.parent.SMALL_THUMB))
        self.parent.make_button(self, "Refresh", lambda : self.update_layout(self.current_selected), 1, 1, 1, "we", ("others", "refresh", self.parent.SMALL_THUMB))
        self.parent.make_button(self, "Full Reset", self.reset, 1, 2, 1, "we", ("others", "reset", self.parent.SMALL_THUMB))
        self.top_frame = ttk.Frame(self) # top frame
        self.top_frame.grid(row=2, column=0, columnspan=3, sticky="we")
        self.tab_text_var = [] # will contain tab related string vars
        self.raid_text_var = [] # will contain raid related string vars
        self.tab_container = [] # contain widgets for tabs
        self.raid_container = [] # contain widgets for raids
        ttk.Separator(self, orient='horizontal').grid(row=3, column=0, columnspan=3, sticky="we") # separator to make it pretty
        self.selected = ttk.Frame(self) # bottom frame
        self.selected.grid(row=4, column=0, columnspan=3, sticky="we")
        self.raid_header = Tk.Label(self.selected, text="No Tab Selected")
        self.raid_header.grid(row=0, column=0, columnspan=6, sticky="w")
        self.raid_header_add = self.parent.make_button(self.selected, "Add Raid", self.reset, 1, 0, 3, "w", ("others", "add", self.parent.SMALL_THUMB))
        self.raid_header_add.grid_forget()
        self.current_selected = None # id of the current selected tab
        self.update_layout() # first update of the layout
        self.preview = None # preview window
        if self.parent.settings.get("top_most", 0) == 1:
            self.attributes('-topmost', True)

    def reset(self) -> None: # reset layout
        if messagebox.askquestion(title="Editor - Reset", message="Are you sure that you want to reset the layout?") == "yes":
            self.layout = json.loads(self.parent.DEFAULT_LAYOUT.replace("'", '"'))
            self.current_selected = None
            self.update_layout()

    def close(self) -> None: # close function
        if self.layout_string != str(self.layout) and messagebox.askquestion(title="Editor - Warning", message="You have unsaved changes. Attempt to save now?") == "yes": # ask for save if unsaved changes
            if not self.save():
                return
        self.parent.editor_window = None
        if self.preview is not None: self.preview.close()
        self.destroy()

    def load_raids(self) -> list: # load raids.json
        try:
            with open('assets/raids.json', mode='r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []

    def edit_entry(self, sv : Tk.StringVar, index : int, eindex : Optional[int], ename : str) -> None: # called by Tk.Entry widgets. Parameters are: String Variable (sv), index in the array, eindex is None for tabs or the index of current tab if element is a raid, ename is the element name
        if eindex is None:
            self.layout[index][ename] = sv.get()
        else:
            if ename == "loot":
                self.layout[eindex]["raids"][index][ename] = sv.get().split("/")
            else:
                self.layout[eindex]["raids"][index][ename] = sv.get()

    def insert_tab(self, i : Optional[int] = None) -> None: # insert a tab at given position i (if None, append)
        if i is None:
            self.layout.append({"text":"New Tab", "tab_image":"bar"})
        else:
            self.layout.insert(i+1, {"text":"New Tab", "tab_image":"bar"})
        # check if bottom frame is enabled and calculate the new index
        if self.current_selected is None:
            ti = None
        elif i is None or self.current_selected < i:
            ti = self.current_selected
        else:
            ti = self.current_selected + 1
        # update the layout
        self.update_layout(ti)

    def delete_tab(self, i : int) -> None: # delete tab at given position i
        if messagebox.askquestion(title="Editor -Delete Tab", message="Are you sure you want to delete Tab #{}?\nAll of its content will be lost.".format(i+1)) == "yes":
            del self.layout[i]
            # check if bottom frame is enabled and calculate the new index
            if self.current_selected is None or self.current_selected == i:
                ti = None
            elif self.current_selected < i:
                ti = self.current_selected
            else:
                ti = self.current_selected - 1
            # update the layout
            self.update_layout(ti)

    def move_tab(self, i : int, change : int) -> None: # move tab by change value in the array (assume the resulting position is valid)
        self.layout[i], self.layout[i+change] = self.layout[i+change], self.layout[i]
        # check if bottom frame is enabled and calculate the new index
        if self.current_selected is None:
            ti = None
        elif self.current_selected == i:
            ti = i+change
        elif self.current_selected == i+change:
            ti = i
        else:
            ti = self.current_selected
        # update the layout
        self.update_layout(ti)

    def insert_raid(self, index : int, i : Optional[int] = None) -> None: # insert a raid at position i in tab index (if None, append)
        if "raids" not in self.layout[index]: self.layout[index]["raids"] = []
        if i is None:
            self.layout[index]["raids"].append({"text":"My Raid", "raid_image":"bhl"})
        else:
            self.layout[index]["raids"].insert(i+1, {"text":"My Raid", "raid_image":"bhl"})
        # update the bottom layout
        self.update_select(index)

    def delete_raid(self, index : int, i : int) -> None: # delete a raid at position i in tab index
        if messagebox.askquestion(title="Editor -Delete Raid", message="Are you sure you want to delete Raid #{}?\nIts content will be lost.".format(i+1)) == "yes":
            del self.layout[index]["raids"][i]
            # update the bottom layout
            self.update_select(index)

    def move_raid(self, index : int, i : int, change : int) -> None: # move a raid at index i, in tab index, by change value (assume the resulting position is valid)
        self.layout[index]["raids"][i], self.layout[index]["raids"][i+change] = self.layout[index]["raids"][i+change], self.layout[index]["raids"][i]
        # update the bottom layout
        self.update_select(index)

    def move_raid_to(self, index : int, i : int) -> None: # move a raid at index i from tab index to a tab selected by the user
        target = simpledialog.askstring("Move Raid", "Move this raid to the end of which Tab? (Input its number)")
        if target is None: return
        try:
            tid = int(target)-1
            if tid < 0 or tid >= len(self.layout): raise Exception() # input check
            self.layout[tid]["raids"].append(self.layout[index]["raids"][i])
            del self.layout[index]["raids"][i]
            self.update_select(index)
        except:
            messagebox.showerror("Editor -Error", "Invalid Tab number "+str(target))

    def update_layout(self, index : Optional[int] = None) -> None: # update the top and bottom frame. Provided index will be passed to update_select()
        self.update_select(index) # update bottom layout
        
        # to avoid reconstructing the frame every time, we keep existing widgets and delete extra ones
        while len(self.tab_container) > len(self.layout):
            for w in self.tab_container[-1]: w.destroy()
            self.tab_container.pop()
            self.tab_text_var.pop()
            self.tab_text_var.pop()
        
        for i, t in enumerate(self.layout): # for each tab
            if i == len(self.tab_container): # create fresh line and store in tab_container
                self.tab_container.append([])
                label = Tk.Label(self.top_frame, text="#"+str(i+1))
                label.grid(row=i+1, column=0, sticky="w")
                self.tab_container[-1].append(label)
                label = Tk.Label(self.top_frame, text="Tab Text")
                label.grid(row=i+1, column=1, sticky="w")
                self.tab_container[-1].append(label)
                self.tab_text_var.append(Tk.StringVar())
                self.tab_text_var[-1].set(t.get("text", ""))
                self.tab_text_var[-1].trace_add("write", lambda name, index, mode, sv=self.tab_text_var[-1], i=i: self.edit_entry(sv, i, None, "text"))
                entry = ttk.Entry(self.top_frame, textvariable=self.tab_text_var[-1])
                entry.grid(row=i+1, column=2, sticky="w")
                self.tab_container[-1].append(entry)
                label = Tk.Label(self.top_frame, text="Image", compound=Tk.RIGHT, image=self.parent.load_asset("assets/tabs/" + t.get("tab_image", "").replace(".png", "") + ".png", self.parent.SMALL_THUMB))
                label.grid(row=i+1, column=3, sticky="w")
                self.tab_container[-1].append(label)
                self.tab_text_var.append(Tk.StringVar())
                self.tab_text_var[-1].set(t.get("tab_image", ""))
                self.tab_text_var[-1].trace_add("write", lambda name, index, mode, sv=self.tab_text_var[-1], i=i: self.edit_entry(sv, i, None, "tab_image"))
                entry = ttk.Entry(self.top_frame, textvariable=self.tab_text_var[-1])
                entry.grid(row=i+1, column=4, sticky="w")
                self.tab_container[-1].append(entry)
                self.tab_container[-1].append(self.parent.make_button(self.top_frame, "", lambda i=i: self.update_select(i), i+1, 5, 1, "w", ("others", "edit", self.parent.SMALL_THUMB)))
                self.tab_container[-1].append(self.parent.make_button(self.top_frame, "", lambda i=i: self.insert_tab(i), i+1, 6, 1, "w", ("others", "add", self.parent.SMALL_THUMB)))
                self.tab_container[-1].append(self.parent.make_button(self.top_frame, "", lambda i=i: self.move_tab(i, -1), i+1, 7, 1, "w", ("others", "up", self.parent.SMALL_THUMB)))
                if i == 0: self.tab_container[-1][-1].grid_forget()
                self.tab_container[-1].append(self.parent.make_button(self.top_frame, "", lambda i=i: self.move_tab(i, 1), i+1, 8, 1, "w", ("others", "down", self.parent.SMALL_THUMB)))
                if i == len(self.layout) - 1: self.tab_container[-1][-1].grid_forget()
                self.tab_container[-1].append(self.parent.make_button(self.top_frame, "", lambda i=i: self.delete_tab(i), i+1, 9, 1, "w", ("others", "del", self.parent.SMALL_THUMB)))
            else: #edit existing line
                self.tab_text_var[i*2].trace_remove("write", self.tab_text_var[i*2].trace_info()[0][1])
                self.tab_text_var[i*2].set(t.get("text", ""))
                self.tab_text_var[i*2].trace_add("write", lambda name, index, mode, sv=self.tab_text_var[i*2], i=i: self.edit_entry(sv, i, None, "text"))
                self.tab_container[i][3].config(image=self.parent.load_asset("assets/tabs/" + t.get("tab_image", "").replace(".png", "") + ".png", self.parent.SMALL_THUMB))
                self.tab_text_var[i*2+1].trace_remove("write", self.tab_text_var[i*2+1].trace_info()[0][1])
                self.tab_text_var[i*2+1].set(t.get("tab_image", ""))
                self.tab_text_var[i*2+1].trace_add("write", lambda name, index, mode, sv=self.tab_text_var[i*2+1], i=i: self.edit_entry(sv, i, None, "tab_image"))
                try:
                    if i == 0: self.tab_container[i][7].grid_forget()
                    else: self.tab_container[i][7].grid(row=i+1, column=7, columnspan=1)
                except:
                    pass
                try:
                    if i == len(self.layout) - 1: self.tab_container[i][8].grid_forget()
                    else: self.tab_container[i][8].grid(row=i+1, column=8, columnspan=1)
                except:
                    pass

    def update_select(self, index : Optional[int] = None) -> None: # update only the bottom frame. Provided index will determine if a current tab is selected or not (if None)
        if index is not None:
            # same principle as update_layout, we made it to keep update fast and lightweight
            while len(self.raid_container) > len(self.layout[index].get("raids", [])): # delete extras
                for w in self.raid_container[-1]: w.destroy()
                self.raid_container.pop()
                self.raid_text_var.pop()
                self.raid_text_var.pop()
                self.raid_text_var.pop()
            self.current_selected = index
            self.raid_header.config(text="Editing Tab #" + str(index+1))
            try:
                self.raid_header_add.grid(row=1, column=0, columnspan=3, sticky="w")
                self.raid_header_add.config(command=lambda index=index: self.insert_raid(index))
            except:
                pass
            for i, r in enumerate(self.layout[index].get("raids", [])): # for each raid
                if i == len(self.raid_container): # create fresh line and store in raid_container
                    self.raid_container.append([])
                    label = Tk.Label(self.selected, text="#"+str(i+1))
                    label.grid(row=i+2, column=0, sticky="w")
                    self.raid_container[-1].append(label)
                    label = Tk.Label(self.selected, text="Raid ID Name")
                    label.grid(row=i+2, column=1, sticky="w")
                    self.raid_container[-1].append(label)
                    self.raid_text_var.append(Tk.StringVar())
                    self.raid_text_var[-1].set(r.get("text", ""))
                    self.raid_text_var[-1].trace_add("write", lambda name, index, mode, sv=self.raid_text_var[-1], idx=index, i=i: self.edit_entry(sv, i, idx, "text"))
                    entry = ttk.Entry(self.selected, textvariable=self.raid_text_var[-1])
                    entry.grid(row=i+2, column=2, sticky="w")
                    self.raid_container[-1].append(entry)
                    label = Tk.Label(self.selected, text="Image", compound=Tk.RIGHT, image=self.parent.load_asset("assets/tabs/" + r.get("raid_image", "").replace(".png", "") + ".png", self.parent.SMALL_THUMB))
                    label.grid(row=i+2, column=3, sticky="w")
                    self.raid_container[-1].append(label)
                    self.raid_text_var.append(Tk.StringVar())
                    self.raid_text_var[-1].set(r.get("raid_image", ""))
                    self.raid_text_var[-1].trace_add("write", lambda name, index, mode, sv=self.raid_text_var[-1], idx=index, i=i: self.edit_entry(sv, i, idx, "raid_image"))
                    entry = ttk.Entry(self.selected, textvariable=self.raid_text_var[-1])
                    entry.grid(row=i+2, column=4, sticky="w")
                    self.raid_container[-1].append(entry)
                    label = Tk.Label(self.selected, text="Loots")
                    label.grid(row=i+2, column=5, sticky="w")
                    self.raid_container[-1].append(label)
                    self.raid_container[-1].append(self.parent.make_button(self.selected, "", lambda index=index, i=i: self.see_loot(index, i), i+2, 6, 1, "w", ("others", "see", self.parent.SMALL_THUMB)))
                    self.raid_text_var.append(Tk.StringVar())
                    self.raid_text_var[-1].set("/".join(r.get("loot", "")))
                    self.raid_text_var[-1].trace_add("write", lambda name, index, mode, sv=self.raid_text_var[-1], idx=index, i=i: self.edit_entry(sv, i, idx, "loot"))
                    entry = ttk.Entry(self.selected, textvariable=self.raid_text_var[-1])
                    entry.grid(row=i+2, column=7, sticky="w")
                    self.raid_container[-1].append(entry)
                    self.raid_container[-1].append(self.parent.make_button(self.selected, "", lambda index=index, i=i: self.insert_raid(index, i), i+2, 8, 1, "w", ("others", "add", self.parent.SMALL_THUMB)))
                    self.raid_container[-1].append(self.parent.make_button(self.selected, "", lambda index=index, i=i: self.move_raid_to(index, i), i+2, 9, 1, "w", ("others", "move", self.parent.SMALL_THUMB)))
                    self.raid_container[-1].append(self.parent.make_button(self.selected, "", lambda index=index, i=i: self.move_raid(index, i, -1), i+2, 10, 1, "w", ("others", "up", self.parent.SMALL_THUMB)))
                    if i == 0:  self.raid_container[-1][-1].grid_forget()
                    self.raid_container[-1].append(self.parent.make_button(self.selected, "", lambda index=index, i=i: self.move_raid(index, i, 1), i+2, 11, 1, "w", ("others", "down", self.parent.SMALL_THUMB)))
                    if i == len(self.layout[index]["raids"]) - 1:  self.raid_container[-1][-1].grid_forget()
                    self.raid_container[-1].append(self.parent.make_button(self.selected, "", lambda index=index, i=i: self.delete_raid(index, i), i+2, 12, 1, "w", ("others", "del",self.parent.SMALL_THUMB)))
                else: # add new raid
                    self.raid_text_var[i*3].trace_remove("write", self.raid_text_var[i*3].trace_info()[0][1])
                    self.raid_text_var[i*3].set(r.get("text", ""))
                    self.raid_text_var[i*3].trace_add("write", lambda name, index, mode, sv=self.raid_text_var[i*3], idx=index, i=i: self.edit_entry(sv, i, idx, "text"))
                    self.raid_container[i][3].config(image=self.parent.load_asset("assets/tabs/" + r.get("raid_image", "").replace(".png", "") + ".png", self.parent.SMALL_THUMB))
                    self.raid_text_var[i*3+1].trace_remove("write", self.raid_text_var[i*3+1].trace_info()[0][1])
                    self.raid_text_var[i*3+1].set(r.get("raid_image", ""))
                    self.raid_text_var[i*3+1].trace_add("write", lambda name, index, mode, sv=self.raid_text_var[i*3+1], idx=index, i=i: self.edit_entry(sv, i, idx, "raid_image"))
                    self.raid_container[i][6].config(command=lambda index=index, i=i: self.see_loot(index, i))
                    self.raid_text_var[i*3+2].trace_remove("write", self.raid_text_var[i*3+2].trace_info()[0][1])
                    self.raid_text_var[i*3+2].set("/".join(r.get("loot", "")))
                    self.raid_text_var[i*3+2].trace_add("write", lambda name, index, mode, sv=self.raid_text_var[i*3+2], idx=index, i=i: self.edit_entry(sv, i, idx, "loot"))
                    self.raid_container[i][8].config(command=lambda index=index, i=i: self.insert_raid(index, i))
                    self.raid_container[i][9].config(command=lambda index=index, i=i: self.move_raid_to(index, i))
                    self.raid_container[i][10].config(command=lambda index=index, i=i: self.move_raid(index, i, -1))
                    self.raid_container[i][11].config(command=lambda index=index, i=i: self.move_raid(index, i, 1))
                    self.raid_container[i][12].config(command=lambda index=index, i=i: self.delete_raid(index, i))
                    try:
                        if i == 0: self.raid_container[i][10].grid_forget()
                        else: self.raid_container[i][10].grid(row=i+2, column=10, columnspan=1)
                    except:
                        pass
                    try:
                        if i == len(self.layout[index]["raids"]) - 1: self.raid_container[i][11].grid_forget()
                        else: self.raid_container[i][11].grid(row=i+2, column=11, columnspan=1)
                    except:
                        pass
        else:
            self.raid_header.config(text="No Tab Selected")
            try: self.raid_header_add.grid_forget()
            except: pass
            self.current_selected = None

    def see_loot(self, index : str, i : int) -> None: # preview button
        if self.preview is not None: self.preview.close()
        self.preview = PreviewLoot(self, self.layout[index]["raids"][i].get("raid_image", ""), self.layout[index]["raids"][i].get("loot", ""))

    def save(self) -> bool: # save to raids.json. Return True if success, False if failure/error detected.
        errors = self.parent.verify_layout(self.layout)
        if len(errors) > 0:
            messagebox.showerror("Editor -Error", "Errors are present in the layout:\n"+"\n".join(errors))
            return False
        try:
            with open("assets/raids.json", mode="w", encoding="utf-8") as f:
                json.dump(self.layout, f, indent=4, ensure_ascii=False)
            self.layout_string = str(self.layout)
            if messagebox.askquestion(title="Editor -Success", message="'raids.json' updated with success.\nDo you want to restart the app now?\nNote: If you removed or renamed a raid, its data might be deleted from 'save.json'.") == "yes":
                self.parent.restart()
            return True
        except Exception as e:
            messagebox.showerror("Editor -Error", "An error occured while saving:\n"+str(e))
            return False

class PreviewLoot(Tk.Toplevel): # preview window
    def __init__(self, parent : Editor, rname : str, loot : list) -> None:
        # window
        self.parent = parent
        Tk.Toplevel.__init__(self,parent)
        self.title("Preview")
        self.resizable(width=False, height=False) # not resizable
        self.minsize(self.parent.parent.MIN_WIDTH, self.parent.parent.MIN_HEIGHT)
        self.iconbitmap('assets/icon.ico')
        self.protocol("WM_DELETE_WINDOW", self.close) # call close() if we close the window
        self.parent.parent.make_button(self, "", None, 0, 0, 1, "w", ("buttons", rname, self.parent.parent.BIG_THUMB))
        Tk.Label(self, text="0").grid(row=1, column=0)
        Tk.Label(self, text="Total").grid(row=2, column=0)
        chest = None
        problems = []
        # create window on the spot instead of reusing set_tab_content: it lets us check for problems and disable interactions at the cost of minimum copy paste
        for l in loot:
            if l in self.parent.parent.CHESTS:
                if chest is None:
                    chest = l
                    break
        if chest is not None:
            Tk.Label(self, text="Chest").grid(row=3, column=0)
        llist = set()
        for i, l in enumerate(loot):
            if l == "":
                problems.append("- Empty string in the loot list (Did you put one extra '/' by mistake?).")
                continue
            elif l in llist:
                problems.append("- '{}' is present twice in the loot list (Remove the duplicate to fix it).".format(l))
                continue
            elif l in self.parent.parent.CHESTS and l != chest:
                problems.append("- Multiple chests in the loot list : '{}' (Remove the unwanted chests).".format(l))
                continue
            self.parent.parent.make_button(self, "", None, 0, i+1, 1, "w", ("buttons", l, self.parent.parent.BIG_THUMB))
            Tk.Label(self, text="0").grid(row=1, column=i+1)
            Tk.Label(self, text="0%").grid(row=2, column=i+1)
            if chest is not None and l != chest: Tk.Label(self, text="0%").grid(row=3, column=i+1)
            llist.add(l)
        if len(problems) > 0: # if problems detected, add problem button
            self.parent.parent.make_button(self, "", lambda problems=problems : self.show_problems(problems), 4, 0, 1, "we", ("others", "warning", self.parent.parent.SMALL_THUMB))
        if self.parent.parent.settings.get("top_most", 0) == 1:
            self.attributes('-topmost', True)

    def show_problems(self, problems : list) -> None:
        messagebox.showerror("Warnings", "List of issues detected with this raid:\n"+"\n".join(problems))

    def close(self) -> None: # called on close
        self.parent.preview = None
        self.destroy()

class History(Tk.Toplevel): # history window
    LIMIT = 30

    def __init__(self, parent : Editor, rname : str) -> None:
        # window
        self.parent = parent
        self.rname = rname
        Tk.Toplevel.__init__(self,parent)
        self.title("History")
        self.resizable(width=False, height=False) # not resizable
        self.minsize(self.parent.MIN_WIDTH, self.parent.MIN_HEIGHT)
        self.iconbitmap('assets/icon.ico')
        self.protocol("WM_DELETE_WINDOW", self.close) # call close() if we close the window
        self.update_history()
        if self.parent.settings.get("top_most", 0) == 1:
            self.attributes('-topmost', True)

    def update_history(self) -> None:
        # cleanup
        for child in self.winfo_children(): # clean current elements
            child.destroy()
        # top line
        r = self.parent.raid_data[self.rname][""][4]
        Tk.Label(self, text=r.get("text", "Raid") + " Raid", image=self.parent.load_asset("assets/tabs/" + r.get("raid_image", "").replace(".png", "") + ".png", self.parent.SMALL_THUMB), compound=Tk.LEFT).grid(row=0, column=0, sticky="w")
        # get chest and total
        chest = self.parent.got_chest.get(self.rname, "")
        total = self.parent.raid_data[self.rname][chest][0]
        if chest == "": chest = "raids"
        else: chest += " chests"
        # position on ui
        line_index = 1
        column = 0
        # iterate over history
        for k, v in self.parent.history.get(self.rname, {}).items():
            count = self.parent.raid_data[self.rname][k][0] # bar/sand count
            if count > 0:
                if line_index != 1:
                    line_index = 1
                    column += 1
                label = Tk.Label(self, image=self.parent.load_asset("assets/tabs/" + k.replace(".png", "") + ".png", self.parent.SMALL_THUMB), compound=Tk.LEFT)
                label.grid(row=line_index, column=column, sticky="w")
                line_index += 1
                prev = 0
                min_v = None
                max_v = None
                start = max(0, count - self.LIMIT)
                if start > 0:
                    Tk.Label(self, text="(Last {} drops)".format(self.LIMIT)).grid(row=line_index, column=column, sticky="w")
                    line_index += 1
                for i in range(len(v)):
                    if i >= count: continue
                    value = v[i]
                    if value == 0:
                        prev = None
                    else:
                        try:
                            diff = value - prev
                            min_v = diff if min_v is None else min(min_v, diff)
                            max_v = diff if max_v is None else max(max_v, diff)
                            if i >= start: Tk.Label(self, text="At {:,} {:} (+{:})".format(value, chest, diff)).grid(row=line_index, column=column, sticky="w")
                        except:
                            if i >= start: Tk.Label(self, text="At {:,} {:}".format(value, chest)).grid(row=line_index, column=column, sticky="w")
                        prev = value
                        line_index += 1
                text = "Rate: {:.2f}%".format(100*count/float(total)).replace('0%', '%').replace('.0%', '%')
                if min_v is not None: text += ", Min: {:,}".format(min_v)
                if max_v is not None: text += ", Max: {:,}".format(max_v)
                try:
                    if v[count-1] > 0:
                        text += ", Avg: {:,}".format(v[count-1] // count)
                except:
                    pass
                label.config(text=text)
            else:
                Tk.Label(self, text="No Data", image=self.parent.load_asset("assets/tabs/" + k.replace(".png", "") + ".png", self.parent.SMALL_THUMB), compound=Tk.LEFT).grid(row=line_index, column=column, sticky="w")
                line_index += 1
        if line_index == 1 and column == 0:
            Tk.Label(self, text="No History available").grid(row=line_index, column=column, sticky="w")

    def close(self) -> None: # called on close
        self.parent.history_window = None
        self.destroy()

if __name__ == "__main__": # entry point
    Tracker().mainloop()
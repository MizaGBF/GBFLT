import tkinter as Tk
import tkinter.font as tkFont
from tkinter import ttk
from tkinter import PhotoImage
import time
import json
from tkinter import messagebox
import urllib.request
import webbrowser
from contextlib import contextmanager
import subprocess
import sys
import zipfile
from io import BytesIO
import os
import copy
from typing import Callable, Optional
from datetime import datetime
import traceback

class Interface(Tk.Tk):
    CHESTS = ["wood", "silver", "gold", "red", "blue", "purple"] # chest list
    RARES = ["bar", "sand"] # rare item
    FORBIDDEN = ["version", "last", "settings", "history", "favorites"] # forbidden raid name list
    THEME = ["light", "dark"] # existing themes
    NOTIF_THRESHOLD = 200 # frame before the notification is deleted
    def __init__(self):
        Tk.Tk.__init__(self,None)
        self.parent = None
        self.apprunning = True
        self.version = "0.0"
        self.stats_window = None # reference to the current stat window
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
        self.protocol("WM_DELETE_WINDOW", self.close) # call close() if we close the window
        self.assets = {} # contains loaded images
        self.raid_data = {} # contains the layout
        self.got_chest = {} # dict of raid with a chest button, and their chest button name
        self.got_rare = {} # set of raid with a bar or sand button
        self.last_tab = None # track the last tab used
        self.modified = False # if True, need to save
        data, rerrors = self.load_raids()
        errors += rerrors
        
        self.tab_tree = {} # used to memorize the tab structure, to set the active tab after loading
        self.top_tab = ttk.Notebook(self)
        for ti, t in enumerate(data): # top tabs
            tab = ttk.Frame(self.top_tab)
            self.top_tab.add(tab, text=t.get("text", ""))
            self.top_tab.tab(tab, image=self.load_asset("assets/tabs/" + t.get("tab_image", "").replace(".png", "") + ".png", (20, 20)), compound=Tk.LEFT)
            raid_tabs = ttk.Notebook(tab)
            for c, r in enumerate(t.get("raids", [])): # raid tabs
                if "text" not in r:
                    errors.append("Raid '{}' doesn't have a 'text' value in Tab '{}'".format(c, ti))
                elif r["text"] in self.raid_data:
                    errors.append("Duplicate raid name '{}' in Tab '{}'".format(r["text"], ti))
                else:
                    rn = r["text"]
                    if rn in self.FORBIDDEN:
                        errors.append("Raid name {} is forbidden in Tab '{}'".format(rn, ti))
                    else:
                        self.tab_tree[rn] = (ti, c, raid_tabs)
                        self.raid_data[rn] = {}
                        sub = ttk.Frame(raid_tabs)
                        raid_tabs.add(sub, text=rn)
                        raid_tabs.tab(sub, image=self.load_asset("assets/tabs/" + r.get("raid_image", "").replace(".png", "") + ".png", (20, 20)), compound=Tk.LEFT)
                        button = self.make_button(sub, "", None, 0, 0, 1, "w", ("buttons", r.get("raid_image", ""), (50, 50)))
                        button.bind('<Button-1>', lambda ev, btn=button, rn=rn: self.count(btn, rn, "", add=True))
                        button.bind('<Button-3>', lambda ev, btn=button, rn=rn: self.count(btn, rn, "", add=False))
                        label = Tk.Label(sub, text="0") # Total label
                        label.grid(row=1, column=0)
                        hist = Tk.Label(sub, text="") # History label
                        hist.grid(row=4, column=1, columnspan=10)
                        self.raid_data[rn][""] = [0, label, hist] # the "" key is used for the total
                        # check for chest in the list
                        chest = None
                        for l in r.get("loot", []):
                            if l.replace(".png", "") in self.CHESTS:
                                chest = l
                                self.got_chest[rn] = chest
                                break
                        # texts
                        Tk.Label(sub, text="Total").grid(row=2, column=0)
                        Tk.Label(sub, text="Chest" if chest is not None else "").grid(row=3, column=0)
                        # build button and label list
                        for i, l in enumerate(r.get("loot", [])):
                            if l.endswith(".png"): l = l[:-3] # strip extension to avoid possible weird behaviors
                            if l in self.raid_data[rn]:
                                errors.append("Raid {} '{}' in Tab '{}': '{}' is present twice in the loot list".format(c, rn, ti, l))
                                continue
                            elif l == "":
                                errors.append("Raid {} '{}' in Tab '{}': Skipped an empty string".format(c, rn, ti))
                                continue
                            elif l in self.CHESTS and l != chest:
                                errors.append("Raid {} '{}' in Tab '{}': Only one chest button supported per raid".format(c, rn, ti))
                                continue
                            if l in self.RARES:
                                if rn not in self.got_rare: self.got_rare[rn] = []
                                self.got_rare[rn].append(l)
                            button = self.make_button(sub, "", None, 0, i+1, 1, "w", ("buttons", l, (50, 50)))
                            button.bind('<Button-1>', lambda ev, btn=button, rn=rn, l=l: self.count(btn, rn, l, add=True))
                            button.bind('<Button-3>', lambda ev, btn=button, rn=rn, l=l: self.count(btn, rn, l, add=False))
                            d = [0, None, None] # other buttons got two labels (count and percent)
                            d[1] = Tk.Label(sub, text="0")
                            d[1].grid(row=1, column=i+1)
                            d[2] = Tk.Label(sub, text="0%")
                            d[2].grid(row=2, column=i+1)
                            if chest is not None and l != chest:
                                d.append(Tk.Label(sub, text="0%"))
                                d[3].grid(row=3, column=i+1)
                            self.raid_data[rn][l] = d
                    self.make_button(sub, "Reset", lambda rn=rn: self.reset(rn), 4, 0, 1, "w", ("others", "reset", (20, 20)))
            raid_tabs.pack(expand=1, fill="both")
        # settings
        tab = ttk.Frame(self.top_tab)
        self.top_tab.add(tab, text="Settings")
        self.top_tab.tab(tab, image=self.load_asset("assets/others/settings.png", (20, 20)), compound=Tk.LEFT)
        self.make_button(tab, "Toggle Theme", self.toggle_theme, 0, 0, 3, "we", ("others", "theme", (20, 20)))
        self.make_button(tab, "Layout Editor  ", self.open_layout_editor, 1, 0, 3, "we", ("others", "layout", (20, 20)))
        self.make_button(tab, "Restart the App", self.restart, 2, 0, 3, "we", ("others", "restart", (20, 20)))
        self.make_button(tab, "Open Statistics", self.stats, 3, 0, 3, "we", ("others", "stats", (20, 20)))
        self.make_button(tab, "Export to Text", self.export_to_text, 4, 0, 3, "we", ("others", "export", (20, 20)))
        self.make_button(tab, "Github Repository", self.github, 0, 3, 3, "we", ("others", "github", (20, 20)))
        self.make_button(tab, "Bug Report        ", self.github_issue, 1, 3, 3, "we", ("others", "bug", (20, 20)))
        self.make_button(tab, "Check Updates   ", lambda : self.check_new_update(False), 2, 3, 3, "we", ("others", "update", (20, 20)))
        self.make_button(tab, "Shortcut List       ", self.show_shortcut, 3, 3, 3, "we", ("others", "shortcut", (20, 20)))
        # check boxes
        self.show_notif = Tk.IntVar()
        ttk.Checkbutton(tab, text='Show notifications', variable=self.show_notif, command=self.toggle_notif).grid(row=0, column=6, columnspan=1, sticky="we")
        self.show_notif.set(self.settings.get("show_notif", 0))
        self.top_most = Tk.IntVar()
        ttk.Checkbutton(tab, text='Always on top', variable=self.top_most, command=self.toggle_topmost).grid(row=1, column=6, columnspan=1, sticky="we")
        self.top_most.set(self.settings.get("top_most", 0))
        if self.settings.get("top_most", 0) == 1:
            self.attributes('-topmost', True)
        self.check_update = Tk.IntVar()
        ttk.Checkbutton(tab, text='Auto Check Updates', variable=self.check_update, command=self.toggle_checkupdate).grid(row=2, column=6, columnspan=1, sticky="we")
        self.check_update.set(self.settings.get("check_update", 0))
        
        # shortcut
        for k in ['<t>', '<T>']:  self.bind(k, self.key_toggle_topmost)
        for k in ['<s>', '<S>']: self.bind(k, self.key_toggle_stat)
        for k in ['<l>', '<L>']: self.bind(k, self.key_toggle_theme)
        for k in ['<e>', '<E>']: self.bind(k, self.key_open_editor)
        for k in ['<r>', '<R>']: self.bind(k, self.key_restart)
        for k in ['<u>', '<U>']: self.bind(k, self.key_update)
        for k in ['<Prior>', '<Next>', '<Left>', '<Right>', '<Up>', '<Down>']: self.bind(k, self.key_page)
        for i in range(1, 13): self.bind('<Shift-F{}>'.format(i), self.key_set_fav)
        for i in range(1, 13): self.bind('<F{}>'.format(i), self.key_select_fav)
        
        # notification
        self.notification_counter = 0
        self.notification = Tk.Label(self, text="")
        if self.settings.get("show_notif", 0) == 1: self.notification.grid(row=1, column=0, sticky="w")
        
        # end
        self.top_tab.grid(row=0, column=0, columnspan=10, sticky="wnes")
        if savedata is not None: self.apply_savedata(savedata)
        if self.last_tab in self.tab_tree:
            t = self.tab_tree[self.last_tab]
            self.top_tab.select(t[0]) # select top tab
            t[2].select(t[1]) # select sub tab on stored notebook
        if len(errors) > 0:
            if len(errors) > 6:
                errors = errors[:6] + ["And {} more errors...".format(len(errors)-6)]
            messagebox.showerror("Important", "The following warnings/errors occured during startup:\n- " + "\n- ".join(errors) + "\n\nIt's recommended to close the app and fix those issues, if possible.")
        elif self.settings.get("check_update", 0) == 1:
            self.check_new_update()
        self.last_savedata_string = str(self.get_save_data()) # get current state of the save as a string

    def make_button(self, parent, text : str, command : Optional[Callable], row : int, column : int, columnspan : int, sticky : str, asset_tuple : Optional[tuple] = None): # function to make our buttons. Asset tuple is composed of 3 elements: folder, asset name and a size tuple (in pixels)
        if asset_tuple is not None:
            asset = self.load_asset("assets/" + asset_tuple[0] + "/" + asset_tuple[1].replace(".png", "") + ".png", asset_tuple[2])
        else:
            asset = None
        button = Tk.Button(parent, image=asset, text=text, compound=Tk.LEFT, command=command)
        button.grid(row=row, column=column, columnspan=columnspan, sticky=sticky)
        return button

    def load_asset(self, path : str, size : tuple = None): # load an image file (if not loaded) and return it. If error/not found, return None or an empty image of specified size
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

    def key_toggle_topmost(self, ev : Tk.Event): # shortcut to toggle top most option
        self.top_most.set(not self.top_most.get())
        self.toggle_topmost()

    def key_toggle_stat(self, ev : Tk.Event): # shortcut to toggle stat window
        if self.stats_window is None: self.stats()
        else: self.stats_window.close()

    def key_toggle_theme(self, ev : Tk.Event): # shortcut to toggle theme
        self.toggle_theme()

    def key_open_editor(self, ev : Tk.Event): # shortcut to open the layout editor
        self.open_layout_editor()

    def key_restart(self, ev : Tk.Event): # shortcut to restart the app
        self.restart()

    def key_update(self, ev : Tk.Event): # shortcut to check for update
        self.check_new_update(False)

    def key_page(self, ev : Tk.Event):  # key shortcut to change tabs
        top_pos = self.top_tab.index("current")
        top_len = len(self.top_tab.winfo_children())
        current_tab = self.top_tab.nametowidget(self.top_tab.select()).winfo_children()[0]
        match ev.keycode:
            case 33|38: #PGUP or UP
                self.top_tab.select((top_pos - 1 + top_len) % top_len)
            case 34|40: #PGDOWN or DOWN
                self.top_tab.select((top_pos + 1) % top_len)
            case 37: #LEFT
                if isinstance(current_tab, ttk.Notebook):
                    sub_pos = current_tab.index("current")
                    sub_len = len(current_tab.winfo_children())
                    current_tab.select((sub_pos - 1 + sub_len) % sub_len)
            case 39: #RIGHT
                if isinstance(current_tab, ttk.Notebook):
                    sub_pos = current_tab.index("current")
                    sub_len = len(current_tab.winfo_children())
                    current_tab.select((sub_pos +1) % sub_len)
            case _:
                pass

    def key_set_fav(self, ev : Tk.Event): # set a favorite
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
                    self.push_notif("'F{}' key set to '{}'".format(index+1, k))
                    return

    def key_select_fav(self, ev): # load a favorite
        index = ev.keycode-112
        try:
            t = self.tab_tree[self.favorites[index]]
            self.top_tab.select(t[0]) # select top tab
            t[2].select(t[1]) # select sub tab on stored notebook
        except:
            pass

    def run(self): # main loop
        count = 0
        while self.apprunning:
            self.update()
            time.sleep(0.02)
            count += 1
            if count % 3000 == 0:
                self.save()
            self.notification_counter += 1
            if self.notification_counter == self.NOTIF_THRESHOLD: # delete notification at threshold
                self.notification.config(text="")
            elif self.notification_counter > self.NOTIF_THRESHOLD:
                self.notification_counter -= 1 # to not rish the value becoming super big

    def close(self): # called when we close the window
        self.apprunning = False
        self.save() # last save attempt
        if self.stats_window is not None: self.stats_window.close()
        self.destroy()

    def load_raids(self): # load raids.json
        errors = []
        try:
            with open('assets/raids.json', mode='r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            data = []
            errors = ["Error in raids.json: " + str(e)]
        return data, errors

    def toggle_checkupdate(self): # toggle check for update option
        self.modified = True
        self.settings["check_update"] = self.check_update.get()

    def toggle_topmost(self): # toggle always on top option
        self.modified = True
        self.settings["top_most"] = self.top_most.get()
        if self.settings["top_most"] == 1:
            self.attributes('-topmost', True)
            if self.stats_window is not None: self.stats_window.attributes('-topmost', True)
            self.push_notif("Windows will always be on top")
        else:
            self.attributes('-topmost', False)
            if self.stats_window is not None: self.stats_window.attributes('-topmost', False)
            self.push_notif("Windows won't be on top")

    def toggle_notif(self): # toggle for notifications
        self.modified = True
        self.settings["show_notif"] = self.show_notif.get()
        if self.settings["show_notif"] == 1:
            self.notification.grid(row=1, column=0, sticky="w")
            self.push_notif("Notifications will appear here")
        else:
            self.notification.grid_forget()

    def push_notif(self, text : str): # edit the notification label and reset the counter
        self.notification.config(text=text)
        self.notification_counter = 0

    def toggle_theme(self): # toggle the theme
        try:
            for i in range(len(self.THEME)): # search the theme
                if self.THEME[i] == self.settings["theme"]:
                    self.settings["theme"]= self.THEME[(i+1)%len(self.THEME)] # switch to the next one
                    self.call("set_theme", self.settings["theme"])
                    self.push_notif("Theme set to '{}'".format(self.settings["theme"]))
                    self.modified = True
                    return
            # not found
            self.settings["theme"] = self.THEME[-1]
            self.toggle_theme()
        except Exception as e:
            print("".join(traceback.format_exception(type(e), e, e.__traceback__)))

    @contextmanager
    def button_press(self, button : Tk.Button): # context used for count(), to activate the button animation when right clicking
        button.config(relief=Tk.SUNKEN, state=Tk.ACTIVE)
        try:
            yield button
        finally:
            button.after(100, lambda: button.config(relief=Tk.RAISED, state=Tk.NORMAL))

    def count(self, button : Tk.Button, rname : str, target : str, add : bool): # add/substract a value. Parameters: button pressed, raid name, button target (will be empty string if it's the total button) and a boolean to control the addition/substraction
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
                self.update_label(rname) # update the labels for this raid
                if self.stats_window is not None: self.stats_window.update_data() # update stats window if open

    def reset(self, rname : str): # raid name
        if Tk.messagebox.askquestion(title="Reset", message="Do you want to reset this tab?") == "yes": #ask for confirmation to avoid  accidental data reset
            if rname in self.raid_data:
                self.last_tab = rname
                for k in self.raid_data[rname]:
                    self.raid_data[rname][k][0] = 0
                try: del self.history[rname]
                except: pass
                self.modified = True
                self.update_label(rname)
                self.push_notif("Raid '{}' has been reset".format(rname))

    def update_label(self, rname : str): # raid name
        if rname in self.raid_data:
            total = self.raid_data[rname][""][0]
            chest_count = 0
            if rname in self.got_chest: # get total of chest
                chest_count = self.raid_data[rname][self.got_chest[rname]][0]
            self.raid_data[rname][""][1].config(text=str(total))
            # update "since the last" label
            if rname in self.got_rare:
                k = self.got_rare[rname][0]
                v = chest_count if rname in self.got_chest else total
                r = (self.got_chest[rname] + " chests" if rname in self.got_chest else "battles").capitalize()
                if self.raid_data[rname][k][0] > 0:
                    h = self.history[rname][k][self.raid_data[rname][k][0]-1]
                    if h > 0 and h <= v:
                        self.raid_data[rname][""][2].config(text="{} {} since the last {}".format(v-h, r, k.capitalize()))
                    else:
                        self.raid_data[rname][""][2].config(text="")
                else:
                    self.raid_data[rname][""][2].config(text="")
            else:
                self.raid_data[rname][""][2].config(text="")
            # update each button values and percentage
            for k, v in self.raid_data[rname].items():
                if k == "": continue
                i = v[0]
                v[1].config(text =str(i))
                if total > 0:
                    v[2].config(text="{:.2f}%".format(min(100, 100*float(i)/total)).replace('.00', ''))
                else:
                    v[2].config(text="0%")
                # chest percentage
                if rname in self.got_chest and len(v) == 4:
                    if chest_count > 0:
                        v[3].config(text="{:.2f}%".format(min(100, 100*float(v[0])/chest_count)).replace('.00', ''))
                    else:
                        v[3].config(text="0%")

    def cmpVer(self, mver : str, tver : str): # compare version strings, True if mver greater or equal, else False
        me = mver.split('.')
        te = tver.split('.')
        for i in range(0, min(len(me), len(te))):
            if int(me[i]) < int(te[i]):
                return False
        return True

    def check_new_update(self, silent : bool = True): # request the manifest file on github and compare the versions
        try:
            with urllib.request.urlopen("https://raw.githubusercontent.com/MizaGBF/GBFLT/main/assets/manifest.json") as url:
                data = json.loads(url.read().decode("utf-8"))
            if "version" in data and self.version != "0.0" and not self.cmpVer(self.version, data["version"]):
                if Tk.messagebox.askquestion(title="Update", message="An update is available.\nCurrent version: {}\nNew Version: {}\nDo you want to download and install?\n- 'save.json' and 'assets/raids.json' will be kept intact.\n- Other files will be overwritten.".format(self.version, data["version"])) == "yes":
                    self.auto_update()
            elif not silent:
                messagebox.showinfo("Update", "GBF Loot Tracker is up-to-date.")
        except Exception as e:
            print("".join(traceback.format_exception(type(e), e, e.__traceback__)))
            if not silent:
                messagebox.showerror("Error", "An error occured while checking for new updates.\nCheck your Firewall, Try again later or go to Github and update manually.")

    def auto_update(self):
        try:
            with urllib.request.urlopen("https://github.com/MizaGBF/GBFLT/archive/refs/heads/main.zip") as url:
                data = url.read()
            with BytesIO(data) as zip_content:
                with zipfile.ZipFile(zip_content, 'r') as zip_ref:
                    # list files
                    folders = set()
                    file_list = zip_ref.namelist()
                    for file in file_list:
                        folders.add("/".join(file.split('/')[1:-1]))
                    # make folders (if missing)
                    for path in folders:
                        if path == "": continue
                        os.makedirs(os.path.dirname(path if path.endswith("/") else path+"/"), exist_ok=True)
                    # write files
                    for file in file_list:
                        if file.split("/")[-1] in ["raids.json", "save.json"] or file.endswith("/"): continue
                        path = "/".join(file.split('/')[1:])
                        with open(path, mode="wb") as f:
                            f.write(zip_ref.read(file))
                    # update raids.json
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
                                    if changes != "" and Tk.messagebox.askquestion(title="Update", message="Differences have been detected between your 'assets/raids.json' and the one from the latest version:\n" + changes + "\nDo you want to apply those differences to your 'assets/raids.json'?") == "yes":
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
                        if Tk.messagebox.askquestion(title="Update", message="An error occured while attempting to detect differences between your 'assets/raids.json' and the one from the latest version.\nDo you want to replace your 'assets/raids.json' with the new one?") == "yes":
                            for file in file_list:
                                if file.endswith("raids.json"):
                                    new = json.loads(zip_ref.read(file).decode('utf-8'))
                                    with open('assets/raids.json', mode='w', encoding='utf-8') as f:
                                        json.dump(new, f, indent=4, ensure_ascii=False)
                                    break
            messagebox.showinfo("Update", "Update successful.\nThe application will now restart.")
            self.restart()
        except Exception as e:
            print("".join(traceback.format_exception(type(e), e, e.__traceback__)))
            messagebox.showerror("Error", "An error occured while downloading or installing the update:\n" + str(e))

    def load_manifest(self): # load data from manifest.json (only the version number for now)
        try:
            with open("assets/manifest.json", mode="r", encoding="utf-8") as f:
                self.version = json.load(f)["version"]
            return []
        except Exception as e:
            print("".join(traceback.format_exception(type(e), e, e.__traceback__)))
            return ["Couldn't open 'assets/manifest.json'"]

    def load_savedata(self): # load save.data, return a tuple of the savedata (None if error) and an error list
        errors = []
        try:
            with open("save.json", mode="r", encoding="utf-8") as f:
                savedata = json.load(f)
            savedata = self.check_history(savedata)
            if not self.cmpVer(self.version, savedata["version"]):
                errors.append("Your save data comes from a more recent version. It might causses issues")
            return savedata, errors
        except Exception as e:
            print("".join(traceback.format_exception(type(e), e, e.__traceback__)))
            if "No such file or directory" not in str(e):
                errors.append("Error while opening save.json: " + str(e))
            return None, errors

    def check_history(self, savedata): # check the history in the savedata and updates it if needed
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

    def add_to_history(self, rname, iname, val, total): # add a new point in time to a raid history
        if rname not in self.history: self.history[rname] = {}
        if iname not in self.history[rname]: self.history[rname][iname] = []
        while len(self.history[rname][iname]) < val: self.history[rname][iname].append(0)
        self.history[rname][iname][val-1] = total

    def apply_savedata(self, savedata : dict): # set raid labels, etc...
        errors = []
        missing = False
        self.last_tab = savedata.get("last", None)
        for k, v in savedata.items(): # set each raid
            if k in self.FORBIDDEN: continue
            for x, y in v.items():
                if k in self.raid_data and x in self.raid_data[k]:
                    self.raid_data[k][x][0] = y
                else:
                    self.history.pop(x, None)
                    if not missing:
                        missing = True
                        errors.append("Values from save.json don't seem in use anymore and will be discarded (Example: {})".format(k)) # warning
            self.update_label(k)
        return errors

    def save(self): # update save.json
        if self.modified:
            self.modified = False
            savedata = self.get_save_data()
            savedata_string = str(savedata)
            if savedata_string != self.last_savedata_string:
                self.last_savedata_string = savedata_string
                try:
                    with open("save.json", mode="w", encoding="utf-8") as f:
                        json.dump(savedata, f)
                    self.push_notif("Changes have been saved")
                except Exception as e:
                    print("".join(traceback.format_exception(type(e), e, e.__traceback__)))
                    messagebox.showerror("Error", "An error occured while saving:\n"+str(e))

    def get_save_data(self): # build the save data (as seen in save.json) and return it
        savedata = {"version":self.version, "last":self.last_tab, "settings":self.settings, "history":self.history, "favorites":self.favorites}
        for k, v in self.raid_data.items():
            savedata[k] = {}
            for x, y in v.items():
                savedata[k][x] = y[0]
        return savedata

    def open_layout_editor(self): # open assets/layout_editor.pyw
        try:
            subprocess.Popen([sys.executable, "layout_editor.pyw"], cwd="assets")
            self.push_notif("Layout Editor has been opened")
        except Exception as e:
            messagebox.showerror("Error", "An error occured while opening the Layout Editor:\n"+str(e))

    def restart(self): # retsart the app (used to check layout changes)
        try:
            self.save()
            subprocess.Popen([sys.executable, sys.argv[0]])
            self.close()
        except Exception as e:
            messagebox.showerror("Error", "An error occured while attempting to restart the application:\n"+str(e))

    def stats(self): # open the stats window
        if self.stats_window is not None:
            self.stats_window.lift()
        else:
            self.stats_window = StatScreen(self)

    def github(self): # open the github repo
        webbrowser.open("https://github.com/MizaGBF/GBFLT", new=2, autoraise=True)
        self.push_notif("Link opened in your broswer")

    def github_issue(self): # open the github repo on the issues page
        webbrowser.open("https://github.com/MizaGBF/GBFLT/issues", new=2, autoraise=True)
        self.push_notif("Link opened in your broswer")

    def show_shortcut(self):
        messagebox.showinfo("Keyboard Shortcuts", "- T: Toggle the Always on top settings.\n- S: Toggle the Statistics window.\n- L: Toggle the Light and Dark themes.\n- E: Open the Layout Editor.\n- R: Restart the application.\n- U: Check for updates.\n- Page Up or Up: Go to the top tab on the left.\n- Page Down or Down: Go to the top tab on the right.\n- Left: Go to the raid on the left.\n- Right: Go to the raid on the right.\n- Shit+F1~F12: Set the current raid to the Function Key pressed.\n- F1~F12: Go to the raid associated to this Function key.")

    def export_to_text(self): # export data to text
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
                if x != cname: report += " ({:.2f}%)".format(100*y[0]/total).replace(".00", "")
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

class StatScreen(Tk.Toplevel): # stats window
    WIDTH=4
    TEXT_WIDTH=8
    BOLD_FONT_MOD=2
    def __init__(self, parent : Tk.Tk):
        # window
        self.parent = parent
        Tk.Toplevel.__init__(self,parent)
        self.title("GBF Loot Tracker - Statistics")
        self.resizable(width=False, height=False) # not resizable
        self.iconbitmap('assets/icon.ico')
        self.protocol("WM_DELETE_WINDOW", self.close) # call close() if we close the window
        self.defaultfont = tkFont.nametofont('TkDefaultFont').actual() # used to make top label bold
        self.update_data()
        if self.parent.settings.get("top_most", 0) == 1:
            self.attributes('-topmost', True)
        self.parent.push_notif("Statistics opened")

    def update_data(self): # update the data shown on the window
        # cleanup
        for child in self.winfo_children(): # clean current elements
            child.destroy()
        # calculate stats
        data = {}
        raid_counts = {}
        for n, r in self.parent.raid_data.items():
            for l, s in r.items():
                data[l] = data.get(l, 0) + s[0]
                if l == "" and s[0] > 0:
                    raid_counts[n] = s[0]
        # sorted
        data = dict(sorted(data.items(), key=lambda item: item[1], reverse=True))
        raid_counts = dict(sorted(raid_counts.items(), key=lambda item: item[1], reverse=True))
        # display
        # raid ranking
        if len(raid_counts) > 0:
            count = 0
            top = Tk.Label(self, text="Top cleared Raids", font=(self.defaultfont['family'], self.defaultfont['size']+self.BOLD_FONT_MOD, 'bold'))
            top.grid(row=0, column=0, columnspan=self.TEXT_WIDTH, sticky="w")
            for n, s in raid_counts.items():
                Tk.Label(self, text="#{:}: {:} - {:} times ({:.2f}%)".format(count+1, n, s, 100 * s / data.get("", 1)).replace(".00%", "%")).grid(row=count+1, column=0, columnspan=self.TEXT_WIDTH, sticky="w")
                count += 1
                if count >= 3: break # stop at top 3
        ttk.Separator(self, orient='horizontal').grid(row=4, column=0, columnspan=max(self.WIDTH*2, self.TEXT_WIDTH), sticky="we") # separator to make it pretty
        # item data
        count = 0
        for l, s in data.items():
            if s == 0: break
            asset = self.parent.load_asset("assets/buttons/" + (l.replace(".png", "") if l != "" else "unknown") + ".png", (50, 50))
            Tk.Label(self, image=asset).grid(row=5 + count // self.WIDTH, column=count % self.WIDTH * 2)
            Tk.Label(self, text=str(s)).grid(row=5 + count // self.WIDTH, column=count % self.WIDTH * 2 + 1)
            count += 1
        # message if no data
        if count == 0:
            Tk.Label(self, text="No Statistics available yet.                    \n\n\n", font=(self.defaultfont['family'], self.defaultfont['size']+self.BOLD_FONT_MOD, 'bold')).grid(row=5, column=0, columnspan=8)

    def close(self): # called on close
        self.parent.stats_window = None
        self.parent.push_notif("Statistics closed")
        self.destroy()

if __name__ == "__main__": # entry point
    Interface().run()
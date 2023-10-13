import tkinter as Tk
from tkinter import ttk
from tkinter import PhotoImage
import time
import json
from tkinter import messagebox

class Interface(Tk.Tk):
    VERSION_STRING = "1.5"
    CHESTS = ["wood", "silver", "gold", "red", "blue", "purple"] # chest list
    FORBIDDEN = ["version", "last"] # forbidden raid name list
    def __init__(self):
        Tk.Tk.__init__(self,None)
        self.parent = None
        self.apprunning = True
        self.title("GBF Loot Tracker v" + self.VERSION_STRING)
        self.iconbitmap('assets/icon.ico')
        self.resizable(width=False, height=False) # not resizable
        self.protocol("WM_DELETE_WINDOW", self.close) # call close() if we close the window
        self.assets = {} # contains loaded images
        self.raid_data = {} # contains the layout
        self.got_chest = {} # dict of raid with a chest button, and their chest button name
        self.add = True # True: +1, False: -1
        self.last_tab = None # track the last tab used
        self.modified = False # if True, need to save
        data, errors = self.load_raids()
        
        tab_tree = {} # used to memorize the tab structure, to set the active tab after loading
        self.top_tab = ttk.Notebook(self)
        for ti, t in enumerate(data): # top tabs
            tab = ttk.Frame(self.top_tab)
            self.top_tab.add(tab, text=t.get("text", ""))
            asset = self.load_asset("assets/tabs/" + t.get("tab_image", "").replace(".png", "") + ".png")
            if asset is not None:
                self.top_tab.tab(tab, image=asset, compound=Tk.LEFT)
            raid_tabs = ttk.Notebook(tab)
            for c, r in enumerate(t.get("raids", [])): # raid tabs
                if "text" not in r:
                    errors.append("Raid {} doesn't have a 'text' value".format(c))
                elif r["text"] in self.raid_data:
                    errors.append("Duplicate raid name: {}".format(r["text"]))
                else:
                    rn = r["text"]
                    if rn in self.FORBIDDEN:
                        errors.append("Raid name {} is forbidden".format(rn))
                    else:
                        tab_tree[rn] = (ti, c, raid_tabs)
                        self.raid_data[rn] = {}
                        sub = ttk.Frame(raid_tabs)
                        raid_tabs.add(sub, text=rn)
                        asset = self.load_asset("assets/tabs/" + r.get("raid_image", "").replace(".png", "") + ".png")
                        if asset is not None:
                            raid_tabs.tab(sub, image=asset, compound=Tk.LEFT)
                        asset = self.load_asset("assets/buttons/" + r.get("raid_image", "").replace(".png", "") + ".png")
                        if asset is None: asset = Tk.PhotoImage(width=50, height=50) # make a dummy 50x50 image if it couldn't load one
                        button = Tk.Button(sub, image=asset, text="", command=lambda rn=rn: self.count(rn, ""))
                        button.grid(row=0, column=0)
                        label = Tk.Label(sub, text="0") # Total label
                        label.grid(row=1, column=0)
                        self.raid_data[rn][""] = [0, label] # the "" key is used for the total
                        # check for chest in the list
                        chest = None
                        for l in r.get("loot", []):
                            if l.replace(".png", "") in self.CHESTS:
                                chest = l
                                self.got_chest[rn] = chest
                                break
                        # texts
                        Tk.Label(sub, text="Total").grid(row=2, column=0)
                        if chest is not None: Tk.Label(sub, text="Chest").grid(row=3, column=0)
                        # build button and label list
                        for i, l in enumerate(r.get("loot", [])):
                            if l.endswith(".png"): l = l[:-3] # strip extension to avoid possible weird behaviors
                            if l in self.raid_data[rn]:
                                errors.append("Raid {} '{}': '{}' is present twice in the loot list".format(c, rn, l))
                                continue
                            elif l == "":
                                errors.append("Raid {} '{}': Skipped an empty string".format(c, rn))
                                continue
                            elif l in self.CHESTS and l != chest:
                                errors.append("Raid {} '{}': Only one chest button supported per raid".format(c, rn))
                                continue
                            asset = self.load_asset("assets/buttons/" + l + ".png")
                            if asset is None: asset = Tk.PhotoImage(width=50, height=50)
                            button = Tk.Button(sub, image=asset, text="", command=lambda rn=rn, l=l: self.count(rn, l))
                            button.grid(row=0, column=i+1)
                            d = [0, None, None] # other buttons got two labels (count and percent)
                            d[1] = Tk.Label(sub, text="0")
                            d[1].grid(row=1, column=i+1)
                            d[2] = Tk.Label(sub, text="0%")
                            d[2].grid(row=2, column=i+1)
                            if chest is not None and l != chest:
                                d.append(Tk.Label(sub, text="0%"))
                                d[3].grid(row=3, column=i+1)
                            self.raid_data[rn][l] = d
                    button = Tk.Button(sub, text="Reset", command=lambda rn=rn: self.reset(rn)) # reset button for the tab
                    button.grid(row=4, column=0, sticky="we")
            raid_tabs.pack(expand=1, fill="both")
        self.top_tab.grid(row=0, column=0, columnspan=10, sticky="wnes")
        button = Tk.Button(self, text="Toggle", command=self.toggle) # toggle button
        button.grid(row=1, column=0, sticky="we")
        self.add_mode = Tk.Label(self, text="Add", background='#c7edcd') # add/substract label
        self.add_mode.grid(row=1, column=1, sticky="w")
        errors = errors + self.load()
        if self.last_tab in tab_tree:
            t = tab_tree[self.last_tab]
            self.top_tab.select(t[0]) # select top tab
            t[2].select(t[1]) # select sub tab on stored notebook
        if len(errors) > 0:
            if len(errors) > 6:
                errors = errors[:6] + ["And {} more errors...".format(len(errors)-6)]
            messagebox.showerror("Important", "The following occured during startup:\n- " + "\n- ".join(errors) + "\n\nIt's recommended to close the app and fix those issues.")

    def load_asset(self, path : str): # load an image file (if not loaded) and return it
        try:
            if path not in self.assets:
                self.assets[path] = PhotoImage(file=path)
            return self.assets[path]
        except:
            return None

    def run(self): # main loop
        count = 0
        while self.apprunning:
            self.update()
            time.sleep(0.02)
            count += 1
            if count % 3000 == 0:
                self.save()

    def close(self):
        self.apprunning = False
        self.save() # last save attempt
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

    def count(self, rname : str, target : str): # add/substract a value. take raid name and button target (will be empty string if it's the total button) as parameters
        if rname in self.raid_data:
            self.last_tab = rname
            if target != "" and target in self.raid_data[rname]:
                if self.add:
                    self.raid_data[rname][target][0] += 1
                else:
                    if self.raid_data[rname][target][0] == 0: return # if at zero, return now
                    self.raid_data[rname][target][0] = self.raid_data[rname][target][0] - 1
                if target.replace(".png", "") not in self.CHESTS: # if we haven't pressed a chest button or the total button, we increase the chest value
                    for k in self.raid_data[rname]:
                        if k in self.CHESTS:
                            if self.add:
                                self.raid_data[rname][k][0] += 1
                            else:
                                self.raid_data[rname][k][0] = max(0, self.raid_data[rname][k][0] - 1)
            # total button
            if self.add:
                self.raid_data[rname][""][0] += 1
            else:
                self.raid_data[rname][""][0] = max(0, self.raid_data[rname][""][0] - 1)
            self.modified = True
            self.update_label(rname) # update the labels for this raid

    def reset(self, rname : str): # raid name
        if rname in self.raid_data:
            self.last_tab = rname
            for k in self.raid_data[rname]:
                self.raid_data[rname][k][0] = 0
            self.modified = True
            self.update_label(rname)

    def update_label(self, rname : str): # raid name
        if rname in self.raid_data:
            total = self.raid_data[rname][""][0]
            chest_count = 0
            if rname in self.got_chest: # get total of chest
                chest_count = self.raid_data[rname][self.got_chest[rname]][0]
            self.raid_data[rname][""][1].config(text =str(total))
            for k, v in self.raid_data[rname].items():
                if k == "": continue
                i = v[0]
                v[1].config(text =str(i))
                if total > 0:
                    v[2].config(text="{:.2f}%".format(100*float(i)/total).replace('.00', ''))
                else:
                    v[2].config(text="0%")
                if rname in self.got_chest and len(v) == 4: # chest %
                    if chest_count > 0:
                        v[3].config(text="{:.2f}%".format(100*float(v[0])/chest_count).replace('.00', ''))
                    else:
                        v[3].config(text="0%")

    def toggle(self): # toggle add/substract
        if self.add:
            self.add_mode.config(text="Substract", background='#edc7c7')
            self.add = False
        else:
            self.add_mode.config(text="Add", background='#c7edcd')
            self.add = True

    def load(self): # load save.data, return an error list
        errors = []
        try:
            with open("save.json", mode="r", encoding="utf-8") as f:
                savedata = json.load(f)
            print("save.json loaded")
        except Exception as e:
            print(e)
            if "No such file or directory" not in str(e):
                errors.append("Error while opening save.json: " + str(e))
            return errors
        missing = False
        self.last_tab = savedata.get("last", None)
        for k, v in savedata.items(): # set each raid
            if k in self.FORBIDDEN: continue
            for x, y in v.items():
                if k in self.raid_data and x in self.raid_data[k]:
                    self.raid_data[k][x][0] = y
                else:
                    if not missing:
                        missing = True
                        errors.append("Values from save.json don't seem in use anymore and will be discarded (Example: {}/{})".format(k, x)) # warning
            self.update_label(k)
        return errors

    def save(self): # save
        if self.modified:
            self.modified = False
            savedata = {"version":self.VERSION_STRING, "last":self.last_tab} # version string in case I change the format later, for retrocompatibility and stuff
            for k, v in self.raid_data.items():
                savedata[k] = {}
                for x, y in v.items():
                    savedata[k][x] = y[0]
            try:
                with open("save.json", mode="w", encoding="utf-8") as f:
                    json.dump(savedata, f)
                print("save.json updated")
            except Exception as e:
                print(e)
                messagebox.showerror("Error", "An error occured while saving:\n"+str(e))

if __name__ == "__main__": # entry point
    Interface().run()
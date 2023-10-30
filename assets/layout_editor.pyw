import tkinter as Tk
from tkinter import ttk
from tkinter import PhotoImage
import time
import json
from tkinter import messagebox
import webbrowser

class Editor(Tk.Tk):
    CHESTS = ["wood", "silver", "gold", "red", "blue", "purple"] # chest list
    FORBIDDEN = ["version", "last", "settings"] # forbidden raid name list
    def __init__(self):
        Tk.Tk.__init__(self,None)
        self.parent = None
        self.apprunning = True
        self.title("GBF Loot Tracker - Layout editor")
        self.iconbitmap('icon.ico')
        self.resizable(width=False, height=False) # not resizable
        self.protocol("WM_DELETE_WINDOW", self.close) # call close() if we close the window
        self.assets = {} # loaded images
        self.layout = self.load_raids()
        Tk.Button(self, text="Save changes to 'raids.json'", command=self.save).grid(row=0, column=0, columnspan=2, sticky="we")
        Tk.Button(self, text="Original 'raids.json' on Github", command=self.github).grid(row=1, column=0, columnspan=2, sticky="we")
        self.top_frame = ttk.Frame(self)
        self.top_frame.grid(row=2, column=0, sticky="w")
        self.tab_text_var = []
        self.raid_text_var = []
        ttk.Separator(self, orient='horizontal').grid(row=3, column=0, columnspan=2, sticky="we")
        self.selected = ttk.Frame(self)
        self.selected.grid(row=4, column=0, columnspan=2, sticky="w")
        self.update_layout()

    def github(self):
        webbrowser.open("https://github.com/MizaGBF/GBFLT/blob/main/assets/raids.json", new=2, autoraise=True)

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
                except: pass

    def run(self): # main loop
        while self.apprunning:
            self.update()
            time.sleep(0.02)

    def close(self):
        self.apprunning = False
        self.destroy()

    def load_raids(self): # load raids.json
        try:
            with open('raids.json', mode='r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []

    def edit_entry(self, sv, index, eindex, ename):
        match eindex:
            case None:
                self.layout[index][ename] = sv.get()
            case _:
                if ename == "loot":
                    self.layout[eindex]["raids"][index][ename] = sv.get().split("/")
                else:
                    self.layout[eindex]["raids"][index][ename] = sv.get()

    def insert_tab(self, i=None):
        if i is None:
            self.layout.append({})
        else:
            self.layout.insert(i+1, {})
        self.update_layout()

    def delete_tab(self, i):
        del self.layout[i]
        self.update_layout()

    def insert_raid(self, index, i=None):
        if "raids" not in self.layout[index]: self.layout[index]["raids"] = []
        if i is None:
            self.layout[index]["raids"].append({})
        else:
            self.layout[index]["raids"].insert(i+1, {})
        self.update_select(index)

    def delete_raid(self, index, i):
        del self.layout[index]["raids"][i]
        self.update_select(index)

    def update_layout(self):
        for child in self.top_frame.winfo_children():
            child.destroy()
        self.tab_text_var = []
        self.update_select()
        Tk.Button(self.top_frame, text="Add Tab", command=self.insert_tab).grid(row=0, column=0, columnspan=3, sticky="w")
        for i, t in enumerate(self.layout):
            Tk.Label(self.top_frame, text="#"+str(i+1)).grid(row=i+1, column=0, sticky="w")
            Tk.Label(self.top_frame, text="Tab Text").grid(row=i+1, column=1, sticky="w")
            self.tab_text_var.append(Tk.StringVar())
            self.tab_text_var[-1].set(t.get("text", ""))
            self.tab_text_var[-1].trace("w", lambda name, index, mode, sv=self.tab_text_var[-1], i=i: self.edit_entry(sv, i, None, "text"))
            ttk.Entry(self.top_frame, textvariable=self.tab_text_var[-1]).grid(row=i+1, column=2, sticky="w")
            Tk.Label(self.top_frame, text="Image").grid(row=i+1, column=3, sticky="w")
            self.tab_text_var.append(Tk.StringVar())
            self.tab_text_var[-1].set(t.get("tab_image", ""))
            self.tab_text_var[-1].trace("w", lambda name, index, mode, sv=self.tab_text_var[-1], i=i: self.edit_entry(sv, i, None, "tab_image"))
            ttk.Entry(self.top_frame, textvariable=self.tab_text_var[-1]).grid(row=i+1, column=4, sticky="w")
            Tk.Button(self.top_frame, text="Edit", command=lambda i=i: self.update_select(i)).grid(row=i+1, column=5, sticky="w")
            Tk.Button(self.top_frame, text="Insert After", command=lambda i=i: self.insert_tab(i)).grid(row=i+1, column=6, sticky="w")
            Tk.Button(self.top_frame, text="Delete", command=lambda i=i: self.delete_tab(i)).grid(row=i+1, column=7, sticky="w")

    def update_select(self, index=None):
        for child in self.selected.winfo_children():
            child.destroy()
        self.raid_text_var = []
        if index is not None:
            Tk.Label(self.selected, text="Editing Tab #" + str(index+1)).grid(row=0, column=0, columnspan=6, sticky="w")
            Tk.Button(self.selected, text="Add Raid", command=lambda index=index: self.insert_raid(index)).grid(row=1, column=0, columnspan=3, sticky="w")
            for i, r in enumerate(self.layout[index].get("raids", [])):
                Tk.Label(self.selected, text="#"+str(i+1)).grid(row=i+2, column=0, sticky="w")
                Tk.Label(self.selected, text="Raid Name").grid(row=i+2, column=1, sticky="w")
                self.tab_text_var.append(Tk.StringVar())
                self.tab_text_var[-1].set(r.get("text", ""))
                self.tab_text_var[-1].trace("w", lambda name, index, mode, sv=self.tab_text_var[-1], idx=index, i=i: self.edit_entry(sv, i, idx, "text"))
                ttk.Entry(self.selected, textvariable=self.tab_text_var[-1]).grid(row=i+2, column=2, sticky="w")
                Tk.Label(self.selected, text="Image").grid(row=i+2, column=3, sticky="w")
                self.tab_text_var.append(Tk.StringVar())
                self.tab_text_var[-1].set(r.get("raid_image", ""))
                self.tab_text_var[-1].trace("w", lambda name, index, mode, sv=self.tab_text_var[-1], idx=index, i=i: self.edit_entry(sv, i, idx, "raid_image"))
                ttk.Entry(self.selected, textvariable=self.tab_text_var[-1]).grid(row=i+2, column=4, sticky="w")
                Tk.Label(self.selected, text="Loots").grid(row=i+2, column=5, sticky="w")
                self.tab_text_var.append(Tk.StringVar())
                self.tab_text_var[-1].set("/".join(r.get("loot", "")))
                self.tab_text_var[-1].trace("w", lambda name, index, mode, sv=self.tab_text_var[-1], idx=index, i=i: self.edit_entry(sv, i, idx, "loot"))
                ttk.Entry(self.selected, textvariable=self.tab_text_var[-1]).grid(row=i+2, column=6, sticky="w")
                Tk.Button(self.selected, text="Insert After", command=lambda index=index, i=i: self.insert_raid(index, i)).grid(row=i+2, column=7, sticky="w")
                Tk.Button(self.selected, text="Delete", command=lambda index=index, i=i: self.delete_raid(index, i)).grid(row=i+2, column=8, sticky="w")
        else:
            Tk.Label(self.selected, text="No Tab Selected").grid(row=0, column=0, columnspan=6, sticky="w")

    def save(self):
        # verification (the same as in tracker.pyw)
        raid_data = {}
        got_chest = {}
        for ti, t in enumerate(self.layout):
            for c, r in enumerate(t.get("raids", [])): # raid tabs
                if "text" not in r:
                    messagebox.showerror("Error", "Raid '{}' doesn't have a 'Text' value in Tab '{}'".format(c, ti+1))
                    return
                elif r["text"] in raid_data:
                    messagebox.showerror("Error", "Duplicate raid name '{}' in Tab '{}'".format(r["text"], ti+1))
                    return
                else:
                    rn = r["text"]
                    if rn in self.FORBIDDEN:
                        messagebox.showerror("Error", "Raid name '{}' is forbidde in Tab '{}'".format(rn, ti+1))
                        return
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
                                messagebox.showerror("Error", "Raid {} '{}' in Tab '{}': '{}' is present twice in the loot list".format(c+1, rn, ti+1, l))
                                return
                            elif l == "":
                                messagebox.showerror("Error", "Raid {} '{}' in Tab '{}': There is an empty string or an extra slash '/'".format(c+1, rn, ti+1))
                                return
                            elif l in self.CHESTS and l != chest:
                                messagebox.showerror("Error", "Raid {} '{}' in Tab '{}': Only one chest button supported per raid".format(c+1, rn, ti+1))
                                return
                            raid_data[rn][l] = None
        try:
            with open("raids.json", mode="w", encoding="utf-8") as f:
                json.dump(self.layout, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("Info", "'raids.json' updated with success.\nRestart GBFLT to check the changes.\nNote: If you removed or renamed a raid, its data might be deleted from 'save.json'.")
        except Exception as e:
            messagebox.showerror("Error", "An error occured while saving:\n"+str(e))

if __name__ == "__main__": # entry point
    Editor().run()
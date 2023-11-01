import tkinter as Tk
from tkinter import ttk
from tkinter import PhotoImage
import time
import json
from tkinter import messagebox, simpledialog
import webbrowser

class Editor(Tk.Tk): # note: this script take some elements from tracker.pyw
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
        self.layout = self.load_raids() # load raids.json
        self.layout_string = str(self.layout) # and make a string out of it to detect modifications
        Tk.Button(self, text="Save changes to 'raids.json'", command=self.save).grid(row=0, column=0, columnspan=2, sticky="we") # save button
        Tk.Button(self, text="Original 'raids.json' on Github", command=self.github).grid(row=1, column=0, columnspan=2, sticky="we") # open github button
        self.top_frame = ttk.Frame(self) # top frame
        self.top_frame.grid(row=2, column=0, sticky="w")
        self.tab_text_var = [] # will contain tab related string vars
        self.raid_text_var = [] # will contain raid related string vars
        ttk.Separator(self, orient='horizontal').grid(row=3, column=0, columnspan=2, sticky="we") # separator to make it pretty
        self.selected = ttk.Frame(self) # bottom frame
        self.selected.grid(row=4, column=0, columnspan=2, sticky="w")
        self.current_selected = None # id of the current selected tab
        self.update_layout() # first update of the layout

    def github(self): # open the raids.json from the github repo
        webbrowser.open("https://github.com/MizaGBF/GBFLT/blob/main/assets/raids.json", new=2, autoraise=True)

    def run(self): # main loop
        while self.apprunning:
            self.update()
            time.sleep(0.02)

    def close(self): # close function
        if self.layout_string != str(self.layout) and Tk.messagebox.askquestion(title="Warning", message="You have unsaved changes. Attempt to save now?") == "yes": # ask for save if unsaved changes
            if not self.save():
                return
        self.apprunning = False
        self.destroy()

    def load_raids(self): # load raids.json
        try:
            with open('raids.json', mode='r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []

    def edit_entry(self, sv, index, eindex, ename): # called by Tk.Entry widgets. Parameters are: String Variable (sv), index in the array, eindex is None for tabs or the index of current tab if element is a raid, ename is the element name
        match eindex:
            case None:
                self.layout[index][ename] = sv.get()
            case _:
                if ename == "loot":
                    self.layout[eindex]["raids"][index][ename] = sv.get().split("/")
                else:
                    self.layout[eindex]["raids"][index][ename] = sv.get()

    def insert_tab(self, i=None): # insert a tab at given position i (if None, append)
        if i is None:
            self.layout.append({})
        else:
            self.layout.insert(i+1, {})
        # check if bottom frame is enabled and calculate the new index
        if self.current_selected is None:
            ti = None
        elif i is None or self.current_selected < i:
            ti = self.current_selected
        else:
            ti = self.current_selected + 1
        # update the layout
        self.update_layout(ti)

    def delete_tab(self, i): # delete tab at given position i
        if Tk.messagebox.askquestion(title="Delete", message="Are you sure you want to delete Tab #{}?\nAll of its content will be lost.".format(i+1)) == "yes":
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

    def move_tab(self, i, change): # move tab by change value in the array (assume the resulting position is valid)
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

    def insert_raid(self, index, i=None): # insert a raid at position i in tab index (if None, append)
        if "raids" not in self.layout[index]: self.layout[index]["raids"] = []
        if i is None:
            self.layout[index]["raids"].append({})
        else:
            self.layout[index]["raids"].insert(i+1, {})
        # update the bottom layout
        self.update_select(index)

    def delete_raid(self, index, i): # delete a raid at position i in tab index
        if Tk.messagebox.askquestion(title="Delete", message="Are you sure you want to delete Raid #{}?\nIts content will be lost.".format(i+1)) == "yes":
            del self.layout[index]["raids"][i]
            # update the bottom layout
            self.update_select(index)

    def move_raid(self, index, i, change): # move a raid at index i, in tab index, by change value (assume the resulting position is valid)
        self.layout[index]["raids"][i], self.layout[index]["raids"][i+change] = self.layout[index]["raids"][i+change], self.layout[index]["raids"][i]
        # update the bottom layout
        self.update_select(index)

    def move_raid_to(self, index, i): # move a raid at index i from tab index to a tab selected by the user
        target = simpledialog.askstring("Move Raid", "Move the raid to the end of which Tab? (Input its number)")
        if target is None: return
        try:
            tid = int(target)-1
            if tid < 0 or tid >= len(self.layout): raise Exception() # input check
            tab = self.layout[tid]["raids"].append(self.layout[index]["raids"][i])
            del self.layout[index]["raids"][i]
            self.update_select(index)
        except:
            messagebox.showerror("Error", "Invalid Tab number "+str(target))

    def update_layout(self, index=None): # update the top and bottom frame. Provided index will be passed to update_select()
        for child in self.top_frame.winfo_children(): # clean current elements
            child.destroy()
        self.tab_text_var = [] # and string vars
        self.update_select(index) # update bottom layout
        Tk.Button(self.top_frame, text="Add Tab", command=self.insert_tab).grid(row=0, column=0, columnspan=3, sticky="w") 
        for i, t in enumerate(self.layout): # add buttons for each existing tabs
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
            if i > 0: Tk.Button(self.top_frame, text="^", command=lambda i=i: self.move_tab(i, -1)).grid(row=i+1, column=7, sticky="w")
            if i < len(self.layout) - 1: Tk.Button(self.top_frame, text="v", command=lambda i=i: self.move_tab(i, 1)).grid(row=i+1, column=8, sticky="w")
            Tk.Button(self.top_frame, text="Delete", command=lambda i=i: self.delete_tab(i)).grid(row=i+1, column=9, sticky="w")

    def update_select(self, index=None): # update only the bottom frame. Provided index will determine if a current tab is selected or not (if None)
        for child in self.selected.winfo_children(): # clean current elements
            child.destroy()
        self.raid_text_var = [] # and string vars
        if index is not None:
            self.current_selected = index
            Tk.Label(self.selected, text="Editing Tab #" + str(index+1)).grid(row=0, column=0, columnspan=6, sticky="w")
            Tk.Button(self.selected, text="Add Raid", command=lambda index=index: self.insert_raid(index)).grid(row=1, column=0, columnspan=3, sticky="w")
            for i, r in enumerate(self.layout[index].get("raids", [])): # add buttons for each existing raids of the selected tab
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
                Tk.Button(self.selected, text="Move To", command=lambda index=index, i=i: self.move_raid_to(index, i)).grid(row=i+2, column=8, sticky="w")
                if i > 0: Tk.Button(self.selected, text="^", command=lambda index=index, i=i: self.move_raid(index, i, -1)).grid(row=i+2, column=9, sticky="w")
                if i < len(self.layout[index]["raids"]) - 1: Tk.Button(self.selected, text="v", command=lambda index=index, i=i: self.move_raid(index, i, 1)).grid(row=i+2, column=10, sticky="w")
                Tk.Button(self.selected, text="Delete", command=lambda index=index, i=i: self.delete_raid(index, i)).grid(row=i+2, column=11, sticky="w")
        else:
            Tk.Label(self.selected, text="No Tab Selected").grid(row=0, column=0, columnspan=6, sticky="w")
            self.current_selected = None

    def save(self): # save to raids.json. Return True if success, False if failure/error detected.
        # verification (the same as in tracker.pyw)
        raid_data = {}
        got_chest = {}
        for ti, t in enumerate(self.layout):
            for c, r in enumerate(t.get("raids", [])): # raid tabs
                if "text" not in r:
                    messagebox.showerror("Error", "Raid '{}' doesn't have a 'Text' value in Tab '{}'".format(c, ti+1))
                    return False
                elif r["text"] in raid_data:
                    messagebox.showerror("Error", "Duplicate raid name '{}' in Tab '{}'".format(r["text"], ti+1))
                    return False
                else:
                    rn = r["text"]
                    if rn in self.FORBIDDEN:
                        messagebox.showerror("Error", "Raid name '{}' is forbidde in Tab '{}'".format(rn, ti+1))
                        return False
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
                                return False
                            elif l == "":
                                messagebox.showerror("Error", "Raid {} '{}' in Tab '{}': There is an empty string or an extra slash '/'".format(c+1, rn, ti+1))
                                return False
                            elif l in self.CHESTS and l != chest:
                                messagebox.showerror("Error", "Raid {} '{}' in Tab '{}': Only one chest button supported per raid".format(c+1, rn, ti+1))
                                return False
                            raid_data[rn][l] = None
        try:
            with open("raids.json", mode="w", encoding="utf-8") as f:
                json.dump(self.layout, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("Info", "'raids.json' updated with success.\nRestart GBF Loot Tracker to check the changes.\nNote: If you removed or renamed a raid, its data might be deleted from 'save.json'.")
            self.layout_string = str(self.layout)
            return True
        except Exception as e:
            messagebox.showerror("Error", "An error occured while saving:\n"+str(e))
            return False

if __name__ == "__main__": # entry point
    Editor().run()
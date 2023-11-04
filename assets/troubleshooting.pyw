from tkinter import messagebox
import sys
import json

err_report = ""
try:
    with open("manifest.json", mode="r", encoding="utf-8") as f:
        data = json.load(f)
        pver = data.get("python", "3.10").split(".")
except:
    err_report += "# Couldn't load 'assets/manifest.json', it might be corrupted\n"
    pver = ["3", "10"]

if sys.version_info.major != int(pver[0]) or sys.version_info.minor < int(pver[1]):
    err_report +=  "# Your python version is v{}.{}. At least Python v{} is recommended. Please uninstall Python and install a newer one.\n".format(sys.version_info.major, sys.version_info.minor, ".".join(pver))

try:
    with open("raids.json", mode="r", encoding="utf-8") as f:
        data = json.load(f)
except Exception as e:
    err_report += "# Couldn't load 'assets/raids.json', it might be corrupted: {}\n".format(e)

try:
    with open("../save.json", mode="r", encoding="utf-8") as f:
        data = json.load(f)
except Exception as e:
    if "No such file or directory" not in str(e):
        err_report += "# Couldn't load 'save.json', it might be corrupted: {}\n".format(e)

if err_report == "":
    messagebox.showinfo("Info", "No anomaly detected.")
else:
    messagebox.showerror("Error Report", "The following list of anomalies has been detected:\n" + err_report + "\nIf you don't know how to solve those issues, you might consider reinstalling GBF Loot Tracker.\nBe sure to keep your 'save.json' file if it's not corrupted.")
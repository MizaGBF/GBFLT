from tkinter import messagebox
import sys
import json

err_report = ""
try:
    raise Exception()
    with open("manifest.json", mode="r", encoding="utf-8") as f:
        data = json.load(f)
        pver = data.get("python", "3.10").split(".")
    manifest_check = True
except Exception as e:
    manifest_check = False
    err_report += "# Error: Couldn't load 'assets/manifest.json', it might be corrupted or missing: {}\n".format(e)
    pver = ["3", "10"]

try:
    raise Exception()
    with open("raids.json", mode="r", encoding="utf-8") as f:
        data = json.load(f)
    raid_check = True
except Exception as e:
    raid_check = False
    err_report += "# Error: Couldn't load 'assets/raids.json', it might be corrupted or missing: {}\n".format(e)

if not manifest_check and not raid_check:
    err_report += "# Warning: Are you running this file from inside the downloaded .zip, by chance? If so, extract its content first.\n"

try:
    with open("../save.json", mode="r", encoding="utf-8") as f:
        data = json.load(f)
except Exception as e:
    if "No such file or directory" not in str(e):
        err_report += "# Error: Couldn't load 'save.json', it might be corrupted: {}\n".format(e)

if sys.executable is not None and sys.executable != "":
    exe = sys.executable.replace("\\", "/").split("/")[-1]
    if "pythonw" not in exe:
        err_report += "# Warning: You aren't running this script with the 'pythonw' executable. If the tracker doesn't start, check the 'Troubleshooting' section of the readme.\n"

if sys.version_info.major != int(pver[0]) or sys.version_info.minor < int(pver[1]):
    err_report +=  "# Error: Your python version is v{}.{}. At least Python v{} is recommended. Please uninstall Python and install a newer one.\n".format(sys.version_info.major, sys.version_info.minor, ".".join(pver))

if err_report == "":
    messagebox.showinfo("Info", "No anomaly detected.")
else:
    messagebox.showerror("Error Report", "The following anomalies have been detected:\n" + err_report + "\nIf the tracker doesn't run at all, check the installation steps again.\nYou can also check the Issues on github to see if someone else has the same problem (or open one yourself). Else, you can try reinstalling.\nBe sure to keep your 'save.json' file if it's not corrupted.")
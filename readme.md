# Granblue Fantasy Loot Tracker  
GUI written in Python to track your Gold Bar, Sand Drops and more in the game [Granblue Fantasy](https://game.granbluefantasy.jp).  
  
![Tracker Preview 1](https://raw.githubusercontent.com/MizaGBF/GBFLT/main/assets/preview1.png)  
  
## Features  
* Lightweight.  
* No third-party dependencies required.  
* No Executable. You can even open and modify the application in a notepad.  
* Light and Dark themes based on the [Azure TTK Theme](https://github.com/rdbende/Azure-ttk-theme) and the [Forest TTK Theme](https://github.com/rdbende/Forest-ttk-theme).  
* Customizable Raid and Loot layout.  
* Keyboard shortcuts for Navigation, Utility and more.  
* Raid Tabs can be popped up.  
* Global statistics.  
* Gold Brick and Eternity Sand history.  
* Auto updater.  
* and more...  
![Tracker Preview 2](https://raw.githubusercontent.com/MizaGBF/GBFLT/main/assets/preview2.png)  
  
## Installation  
* You only need [Python 3](https://www.python.org/downloads/) (version 3.10 or higher) installed on your computer to run `tracker.pyw`.  
  
> [!TIP]
> New to Github? Click the Green `Code` button at the top of this page, then "Download ZIP" to download this repository.  
> Once downloaded, right click on the `.zip` file and extract the content. You can then delete the `.zip` file.  
> Now, go inside the newly created folder and double-click on `tracker.pyw` to see if it works. If it doesn't, check the next section.  
> (Optional) You can delete the `.github` folder if you only plan to have a normal usage of this application.  
  
## Troubleshooting  
If you downloaded this application for the first time and it doesn't run, check the following:
1. Make sure you did extract the content of the `.zip` properly and that you're not inside currently.
2. Did Windows ask you to pick an application to open the file? If yes and you picked a Python with a *rocket* on its icon: It's not Python but its launcher. Click on "More applications" then scroll down to "Search an application on this computer". Navigate to where you installed Python (probably somewhere in your `C:\` folder) and go inside. You should see a few files, including one named `pythonw.exe` (take note of the **w**). Pick this one and it should start. Make sure to make it the default application for this file so you don't have to repeat the steps above.  
3. If it still doesn't start, go into the `assets` folder and try to run `troubleshooting.pyw`. If it doesn't run too, something is very wrong with your installation (if you have multiple Python versions installed including an old one, it might be the problem). If it runs, it should tell you what's wrong (if not, open an [Issue](https://github.com/MizaGBF/GBFLT/issues)).  
  
## Usage  
* Simply double-click on `tracker.pyw`, assuming Python is installed correctly. If nothing happens, see the `Troubleshooting` section above.  
* Left Click on a button to increase the counter.  
* Right Click on a button to decrease the counter.  
* The reset button will reset the current tab.  
* The raid buttons modify the total raid done. It's also modified if another item is modified.  
* The chest buttons (if present) modify the total chest obtained. It's also modified if another item is modified.  
* The values are saved every minute or on exit, if they have been modified.  
  
## Update  
> [!CAUTION]
> The following can corrupt your `save.json` and `assets/raids.json` (if you modified it).  
> Make sure to make a copy of those files.  

To update, simply use the built-in Updater under the `Settings` tab.  
If it doesn't work or if you want to manually update, repeat the Installation process, move/copy inside your backed-up `save.json` (and  `assets/raids.json` if modified), and overwrite if asked.
  
## Keyboard Shortcuts  
* `T`: Toggle the `Always on top` settings.  
* `S`: Toggle the Statistics window.  
* `L`: Toggle the Light and Dark themes.  
* `N`: Toggle the Notification Bar.  
* `E`: Open the Layout Editor.  
* `R`: Restart the application.  
* `U`: Check for updates.  
* `M`: Memorize the currently opened Raid Popups positions.  
* `O`: Open the memorized Raid popups to their saved positions.  
* `C`: Close all opened Raid popups.  
* `Page Up` or `Up`: Go to the top tab on the left.  
* `Page Down` or `Down`: Go to the top tab on the right.  
* `Left`: Go to the raid on the left.  
* `Right`: Go to the raid on the right.  
* `Shit+F1~F12`: Set the current raid to the Function Key pressed.  
* `F1~F12`: Go to the raid associated to this Function key.

You can find a list of those shortcuts under `Settings` and then `Shortcut List`.  
  
## Support  
Just drop a star on the top right corner of this page if you want to show your support.  
  
## Bug report  
Simply open an [Issue](https://github.com/MizaGBF/GBFLT/issues) or contact me.  
  
## Pull Request  
If you wish to implement yourself new features, you can.  
I won't explain to you how to use Git to fork, make a pull request and so on.  
> [!IMPORTANT]  
> The following pull requests will be refused:  
> Changes requiring a third party dependency.  
> Changes to the default `assets/raids.json` file.  
  
## Customization  
> [!CAUTION]
> The following can corrupt your `save.json` and `assets/raids.json` (if you modified it).  
> Make sure to make a copy of those files.
  
The layout is fully editable.  
There are two ways to edit the `assets/raids.json` files:  
  
### The Easier Way:  
  
Under the `settings` tab of the tracker, press the button `Layout Editor` to open an interface allowing you to edit `assets/raids.json`. Alternatively, press the `E` key on your keyboard.  
![Editor Preview](https://raw.githubusercontent.com/MizaGBF/GBFLT/main/assets/preview3.png)  
- On the top area, you can edit a tab `Text` and `Image` values (the image must be a 20x20 pixels PNG file in the `assets/tabs` folder).  
- Clicking on a tab `Edit`button lets you open its content in the bottom area.  
- In the bottom area, in a similar fashion, you edit a raid `Text` and `Image` values (the image must be a 20x20 pixels PNG file in the `assets/tabs` folder and another 50x50 PNG file in the`assets/buttons` folder).  
- To edit the `Loots`, simply put the list of item images (each image must be a 50x50 pixels PNG file in the `assets/buttons` folder) separated by `/` characters. No duplicates allowed in a same list. Only one chest (`wood`, `silver`, `gold`, `red`, `blue`, `purple`) allowed too.  
- All values are case-sensitive.  
- You can use the 'eye' button near the loot list to check how the raid will look like. If there is a problem, a 'warning' button will be present in the preview. Press it to see the list of issues.  
  
Once you're done, click on `Save changes to 'raids.json'` at the top. If errors occured, fix what you did wrong. If no errors occured, (re)start `tracker.pyw` to check how your changes look.  
  
### The Harder Way:  
> [!WARNING]  
> The following isn't recommended, the built-in Layout Editor is good enough nowadays.  
> Those instructions are here mostly for documentation purpose.  
  
Open `assets/raids.json` in a text editor. The Windows Notepad can work or something better. You can also try an [Online JSON Editor](https://jsoneditoronline.org/).  
  
The JSON structure is the following:  
- A list of Tab objects:
    - A Tab object has the following keys:
        - "tab_image" (OPTIONAL). Must match an image file from the `assets/tabs` folder.  
        - "text" (OPTIONAL). The text displayed on the tab.
        - "raids". A list of Raid objects:
            - A Raid object has the following keys:
                - "raid_image": Must match an image file from the `assets/tabs` and `assets/buttons` folder.  
                - "text": The name of the raid to be displayed on the Tab. This name is also used in the save data.  
                - "loot": A list of strings:
                    - Each string must match a file name found in `assets/buttons`. No need to put the file extension. No duplicates allowed. Only one chest allowed max. Those strings are also used in the save data.  
  
All strings are case-sensitive.  
Images must have the following format:  
`assets/tabs`: 20x20 pixels, PNG format.  
`assets/buttons`: 50x50 pixels, PNG format.  
Looking for a particular boss icon? Check out [GBFAL](https://mizagbf.github.io/GBFAL/), then make sure to resize the image.  
Other sizes will work but might not look nice.  
  
## Further Modding  
> [!CAUTION]  
> Again, before attempting to follow any of those instructions, make sure to backup any file that you are worried to mess up irremediably.
  
If you want to add a visual theme, you have to modify the following:
- Add your theme to `assets\themes\main.tcl` to redirect it to your TCL file.  
- Edit `tracker.pyw` (line 25 on the current version) and add your theme to the rotation.
  
If you need to edit `save.json`, the file is structured this way (for version `1.53` at the time of this writing):
- An object containing:
    - "version" key and the version string of the tracker by which this file was generated.  
    - "last" key and the name of the last Raid modified.  
    - "settings" key and an object, containing the states of various settings of the tracker.  
    - "history" key and an object containing:  
        - A raid name as a key and an object structured as:  
            - A name of a rare item (supported currently: bar, sand, evolite, sunlight, shard) and a list of integer. The integers represent the total or chest count at which the item was dropped on. The list size must match the number of this item dropped. The tracker automatically set it to the appropriate size and fill with Zero (which means "Unknown") if needed.  
    - "favorites" key and a list of twelve elements (one for each function key on a keyboard, up to F12 included). Elements are either the name of a raid associated to the function key, or `null` if not associated.  
    - Every raid names as keys with an object as a value, containing the following:  
        - An item name and its associated integer. If the item name is an empty string, it matches the raid button instead. The integer is the number of times that the item dropped or the raid has been beaten.  
  
If you want to import the tracker as a python module in one of your project, know the following:  
- You must pass the path (absolute or relative) to the GBFLT folder, to the `Tracker` instance, via the `tracker_directory` parameter.  
- You can also set a parent to the `Tracker` instance, if you want to put it inside another Tkinter application. Such scenario is untested and might require some bug fixes.  
  
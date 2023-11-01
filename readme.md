# Granblue Fantasy Loot Tracker  
* GUI to track your Gold Bar and Sand Drops in [Granblue Fantasy](https://game.granbluefantasy.jp).  
![Tracker Preview 1](https://raw.githubusercontent.com/MizaGBF/GBFLT/main/assets/preview1.png)  
  
### Features  
* Lightweight.  
* No third-party dependencies required.  
* Light and Dark themes based on [the Azure TTK Theme](https://github.com/rdbende/Azure-ttk-theme).  
* Customizable layout.  
* Global statistics.  
![Tracker Preview 2](https://raw.githubusercontent.com/MizaGBF/GBFLT/main/assets/preview2.png)  
  
### Installation  
* You only need [Python 3](https://www.python.org/downloads/) installed (It has been confirmed to work on Python 3.11 and higher).  
* New to Github? Click the Green `Code` button at the top of this page, then "Download ZIP" to download this repository.  
  
### Update  
Simply use the built-in Updater under the `Settings` tab.  
If it doesn't work or if you want to manually update:  
* Backup your `save.json` and any other files you might have modified (such as `assets/raids.json`).  
* Download and overwrite your current GBFLT copy with the new one.  
* Put your backed up `save.json` (and other files) back in place (overwrite, if asked).  
  
### Usage  
* Simply double-click on `tracker.pyw`, assuming Python is installed correctly.  
* Left Click on a button to increase the counter.  
* Right Click on a button to decrease the counter.  
* The reset button will reset the current tab.  
* The raid buttons modify the total raid done. It's also modified if another item is modified.  
* The chest buttons (if present) modify the total chest obtained. It's also modified if another item is modified.  
* The values are saved every minute or on exit, if they have been modified.  
  
### Bug?  
Open an issue or contact me directly.  
  
### Customization  
The layout is fully editable.  
Before starting, I recommend to backup `save.json` and `assets/raids.json`, in case you make a very big mistake.  
There are two ways to edit the `assets/raids.json` files:  
  
- **The Easier Way:**  
  
Open the `assets` folder and double-click on `layout_editor.pyw` to open a simple interface to edit the file. Alternatively, press the button `Layout Editor` under the `settings` tab of the tracker.  
![Editor Preview](https://raw.githubusercontent.com/MizaGBF/GBFLT/main/assets/preview3.png)  
- On the top area, you can edit a tab `Text` and `Image` values (the image must be a 20x20 pixels PNG file in the `assets/tabs` folder).  
- Clicking on a tab `Edit`button lets you open its content in the bottom area.  
- In the bottom area, in a similar fashion, you edit a raid `Text` and `Image` values (the image must be a 20x20 pixels PNG file in the `assets/tabs` folder and another 50x50 PNG file in the`assets/buttons` folder).  
- To edit the `Loots`, simply put the list of item images (each image must be a 50x50 pixels PNG file in the `assets/buttons` folder) separated by `/` characters. No duplicates allowed in a same list. Only one chest (`wood`, `silver`, `gold`, `red`, `blue`, `purple`) allowed too.  
- All values are case-sensitive.  
  
Once you're done, click on `Save changes to 'raids.json'` at the top. If errors occured, fix what you did wrong. If no errors occured, (re)start `tracker.pyw` to check how your changes look.  
Contact me or open an issue if you find bugs.  
  
- **The Harder Way:**  
  
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
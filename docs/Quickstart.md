> Note : This project is still in development.
> Some things may not work as intended.

---

# Running
This project requires Python 3.13 to run from source code or Windows to run as an executable.


## Portable
1. Download Canopy-portable-<version>.exe from latest releases
2. Run Canopy-portable-<version>.exe
3. Open a web browser and go to 'http://localhost:58362/app'
4. Create a new user

## Installation (per-user)
1. Download Canopy-Installer-<version>.exe from latest releases. The version of the installer determines the version of Canopy you are using.
2. Run Canopy-Installer-<version>.exe
3. Follow the installation steps. (currently it can only be run portable)
4. Skip the folder selection
5. Edit the configuration.
6. Press next, and check 'Run after installation'
7. Continue.
8. Open a web browser and go to 'http://localhost:58362/app'
9. Create a new user


## Creating a new user
Opening the link above will bring up a login screen. 
1. Click on **'Switch to Registration'**, and enter a username. 
2. Remember, your username is **case-sensitive**. 
3. Display name can be whatever you want. It defaults to your *username if left blank*.
4. Then enter a password and click **'Create Account'**. It should automatically bring you back to the login page with your details prefilled. Press login, and youre in!


## Creating new blocks
1. Open the sidebar (burger menu) and click on the **Management Tab**
2. Click on the dropdown menu on the *right* of the grey **'CREATE NEW'** button.
3. Enter the details of the block
   1. **Title** - The name of the event, this will be displayed in the timetable view
   2. **Description** - Optional extra detail
   3. **Start Date/Time & End Date/Time** - When the event starts and ends. Make sure the *End Date/Time* is *AFTER* the *Start Date/Time*
4. Press the 'CREATE' button.
5. Once the page refreshes (you should be able to see your new block in the table), open the sidebar and go back to the timetable.
6. Your newly created block should now show up in the **Timetable tab**!


## Changing timetable view
1. Open the sidebar and click on the **Settings tab**
2. Select which view you want (horizontal/vertical)
3. Click **'SAVE'**
4. Your timetable should now be updated


## Logging out
1. Click on the user pfp in the **top right corner** next to your **display name**
2. Click on the exit icon that shows up **next** to your display name
3. You are now logged out


# Notes
- '~/.canopy-suite' contains the database, configuration files and log files.
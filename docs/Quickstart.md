Note : This project is still in development.

---

### Running
This project requires Python 3.13 to run from source code or Windows to run as an executable.

1. Download Dynamic-Timetabler-<version>.exe
2. Run Dynamic-Timetabler-<version>.exe
3. Open a web browser and go to 'http://localhost:58362/app/timetable

### Creating a new user
Opening the link above will bring up a login screen. 
1. Click on 'Switch to Registration', and enter a username. 
2. Remember, your username is case-sensitive. 
3. Display name can be whatever you want. It defaults to your username if left blank.
4. Then enter a password and click 'Create Account'. It should automatically bring you back to the login page with your details prefilled. Press login, and youre in!

You can log out by clicking your the user icon in the top right corner, and then the exit icon.

### Creating new blocks
1. Open the sidebar (burger menu) and click on the Management Tab
2. Enter the details of your Block.
   1. Title - The name of the event, this will be displayed in the timetable view
   2. Description - Optional extra detail
   3. Start Date/Time & End Date/Time - When the event starts and ends. Make sure the *End Date* is *AFTER* the *Start Date*
3. Press the 'CREATE' button.
4. Your newly created block should now show up in the Timetable tab!

### Notes
- '~/.canopy-suite' contains the database, configuration files and log files.
- For older versions (v0.0.6 and below) 'canopy-suite' is replaced with 'dynamic-timetabler'
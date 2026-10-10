Note : This project is still in development.

---
This project requires Python 3.13 to run.

1. Download this repo and navigate to the 'Dynamic-Timetabler' directory.
2. Create a virtual environment `python -m venv .venv` and activate it.
3. Install requirements `pip install -r requirements.txt`
4. On Windows, run
    `.\scripts\run.bat`
    or currently just run `flask run -h localhost -p 58362`. This port was arbitrarily chosen, you can change it if you want.
   (you may need to set an environment variable `FLASK_APP=src.app`)

   Currently I have no instructions for Linux, but it should be similar (`export FLASK_APP=src.app && flask run...).

5. To view the web interface, open a web browser and enter `http://localhost:58362` (or whatever you set the port to)

Creating a new user
I haven't created a web interface to create a user yet, so if you want to create a user you need to run
```
curl.exe -X POST http://localhost:58362/server/user/create -H "Content-Type: application/json" --data-raw '{\"username\":\"test_user\",\"display_name\":\"TEST\"}' -v
```
The username and display_name fields can be whatever you want. For linux, the command is the same, just remove the .exe from curl.

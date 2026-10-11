Note : This project is still in development.

---
This project requires Python 3.13 to run.

1. Download this repo and navigate to the 'Dynamic-Timetabler' directory.
2. Create a virtual environment `python -m venv .venv` and activate it.
3. Install requirements `pip install -r requirements.txt`
4. On Windows and Linux, run the following commands to create and initialise the database.
    ```
    flask db init
    flask db migrate -m "Initialise Database"
    flask db upgrade
    ```
    and run the `app.py` file

5. To view the web interface, open a web browser and enter `http://localhost:58362/app`

Creating a new user
I haven't created a web interface to create a user yet, so if you want to create a user you need to run
```
curl.exe -X POST http://localhost:58362/server/user/create -H "Content-Type: application/json" --data-raw '{\"username\":\"test_user\",\"display_name\":\"TEST\"}' -v
```
The username and display_name fields can be whatever you want. For linux, the command is the same, just remove the .exe from curl.

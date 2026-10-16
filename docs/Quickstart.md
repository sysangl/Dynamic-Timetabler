Note : This project is still in development.

---
This project requires Python 3.13 to run.

1. Download Dynamic-Timetabler-<version>.exe
2. Run Dynamic-Timetabler-<version>.exe
3. Open a web browser and go to 'http://localhost:58362/app/timetable

Creating a new user
I haven't created a web interface to create a user yet, so if you want to create a user you need to run
NOTE : Settings and timetable configuration will not be available unless a user has been created.
```
curl.exe -X POST http://localhost:58362/server/user/create -H "Content-Type: application/json" --data-raw '{\"username\":\"test_user\",\"display_name\":\"TEST\"}' -v
```
The username and display_name fields can be whatever you want. For linux, the command is the same, just remove the .exe from curl.


Adding Timetable Blocks
The command below will create a timetable block when run in Windows Powershell
```
Invoke-WebRequest -Uri 'http://localhost:58362/server/timetable/blocks/create' `
      -Method Post `
      -Headers @{ 'Content-Type' = 'application/json' } `
      -Body '{
            "title" : "Block Name",
            "description" : "Block Description",
            "start_datetime" : {"year":2026, "month":10, "day":13, "hour":10, "minute":0},
            "end_datetime" : {"year":2026, "month":10, "day":13, "hour":15, "minute":30},
            "colour" : "#734984"
      }' `
      -Verbose
```
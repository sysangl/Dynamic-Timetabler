This is mostly just a reference for myself on how to create various entries in the database.

# Getting stuff
```
curl.exe -X GET http://localhost:58362/<ROUTE>
```


Invoke-WebRequest -Uri 'http://127.0.0.1:58362/server/user/create' `
      -Method POST `
      -Headers @{'Content-Type' =  'application/json' } `
      -Body '{
            "username":"test",
            "display_name":"Test User"
      }' -Verbose


# ACTIVITIES

### CREATE
```
Invoke-WebRequest -Uri 'http://localhost:58362/server/activities/create' `
      -Method Put `
      -Headers @{ 'Content-Type' = 'application/json' } `
      -Body '{
            "name":"Test Activity",
            "description":"This is a test activity.",
            "priority":2,
            "repeat_mode":0,
            "repeat_interval":null,
            "frequency":null,
            "even_frequency_spacing":null,
            "min_length":null,
            "max_length":null,
            "min_time":null,
            "max_time":null,
            "time_limit_reset":null
      }' `
      -Verbose
```


# TIMETABLE ITEMS
### CREATE
```
Invoke-WebRequest -Uri 'http://localhost:58362/server/timetable/blocks/create' `
      -Method Put `
      -Headers @{ 'Content-Type' = 'application/json' } `
      -Body '{
            "title" : "Test Block",
            "description" : "Testing block, useless for now",
            "start_datetime" : {"year":2026, "month":10, "day":13, "hour":6, "minute":21},
            "end_datetime" : {"year":2026, "month":10, "day":14, "hour":9, "minute":26},
            "colour" : "#734984"
      }' `
      -Verbose
```
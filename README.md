```
      ___                             _            
     /   \_   _ _ __   __ _ _ __ ___ (_) ___             
    / /\ / | | | '_ \ / _` | '_ ` _ \| |/ __|            
   / /_//| |_| | | | | (_| | | | | | | | (__            
  /___,'  \__, |_| |_|\__,_|_| |_| |_|_|\___|            
          |___/                          
          _____ _                _        _     _      
         /__   (_)_ __ ___   ___| |_ __ _| |__ | | ___ _ __
           / /\/ | '_ ` _ \ / _ \ __/ _` | '_ \| |/ _ \ '__|
          / /  | | | | | | |  __/ || (_| | |_) | |  __/ | 
          \/   |_|_| |_| |_|\___|\__\__,_|_.__/|_|\___|_|
```

==========================================================================

![hackatime badge](https://hackatime.hackclub.com/api/v1/badge/U0A0HQ4TYJX/sysangl/Dynamic-Timetabler)

# Dynamic Timetable

A timetable/calendar/routine planner (although they're all basically the same thing) backend. The goal for this project is to automatically generate/fill a timetable. Activities can be created to set rules on the creation of timetable 'Blocks', which can change size and start times to make the most of your time. 

Missed a task? The algorithm will sort it out and reschedule it for a different time.

# Algorithm details

Main limitation of this project would probably the Graph Colouring Problem, but since the only constraints on each block (for now) is just the times, it shouldn't cause too many issues. I attempt to create a simulated annealing algorithm, but if it doesn't work nicely I'll try to make a neural network instead.

# Features!

> DONE    = Finished! May still be updated to fix bugs. <br>
> WORKING = Currently works, but will be updated as the project goes on. (Basic functionality) <br>
> WIP     = Work In Progress (still working on it/partial functionality) <br>
> FUTURE  = Haven't started work (or limited functionality not meant for users) <br>
> ?       = Thinking about adding it. <br>


| Status  | Feature                                                                                                                       |
| ------- | ----------------------------------------------------------------------------------------------------------------------------- |
| WIP     | Timetable functionality (event creation and display)                                                                          |
| WIP     | Event/Activity/Block Management                                                                                               |
| FUTURE  | User management                                                                                                               |
| FUTURE  | Dynamic Table Engine (auto generating timetables, dynamic routines)                                                           |
| WORKING | Web Interface (Basic timetable view, settings page and a basic block creation page)                                           |
| WORKING | Portable (Currently works as an .exe or python project. The source code *should* work on most platforms that support python.) |
|         |                                                                                                                               |
|         |                                                                                                                               |

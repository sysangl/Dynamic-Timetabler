```
     _____
    /  __ \
    | /  \/ __ _ _ __   ___  _ __  _   _
    | |    / _` | '_ \ / _ \| '_ \| | | |
    | \__/\ (_| | | | | (_) | |_) | |_| |
     \____/\__,_|_| |_|\___/| .__/ \__, |
                            | |     __/ |
                            |_|    |___/
```

==========================================================================

![hackatime badge](https://hackatime.hackclub.com/api/v1/badge/U0A0HQ4TYJX/sysangl/Dynamic-Timetabler)

# Canopy Suite
> Previously named Dynamic Timetabler

A productivity suite with various things to help you keep track of your time. 


*...making time management tools to help manage my time better, but now im spending all my time making time management tools to help...*


# How to run

## Reccommended (portable mode)
1. Download the latest release `Canopy-portable-<version>.exe`
2. Run the executable
3. Once a console window pops up (should show a 'Canopy' text banner), open a web browser and go to 'http://localhost:58362/app'
4. You can create a user by clicking 'Switch to Registration'

More information is located in `docs/Quickstart.md`

# Features!

> DONE    = Finished! May still be updated to fix bugs. <br>
> WORKING = Currently works, but will be updated as the project goes on. (Basic functionality) <br>
> WIP     = Work In Progress (still working on it/partial functionality) <br>
> FUTURE  = Haven't started work (or limited functionality not meant for users) <br>
> PLANNED = Planned, not going to work on it soon but it will be a feature <br>
> ?       = Thinking about adding it. <br>


| Status  | Feature                                                                                                                       |
| ------- | ----------------------------------------------------------------------------------------------------------------------------- |
| WORKING | Timetable functionality (event creation and display)                                                                          |
| WORKING | Block Management                                                                                                              |
| WORKING | User management                                                                                                               |
| WORKING | Dynamic Table Engine - Auto generating timetables                                                                             |
| FUTURE  | Dynamic Table Engine - Dynamic routines                                                                                       |
| WORKING | Web Interface (Basic timetable view, settings page and a basic block creation page)                                           |
| WORKING | Timetable layouts/views (horizontal & vertical)                                                                               |
| WORKING | Portable (Currently works as an .exe or python project. The source code *should* work on most platforms that support python.) |
| WIP     | Pomodoro Timer                                                                                                                |
| WIP     | Dashboard View                                                                                                                |
| PLANNED | Wakatime (and other time keeping software) integration                                                                        |
| PLANNED | Internet calendar integration                                                                                                 |
| PLANNED | Calendar/'Timetable Items' import/export                                                                                      |


# Algorithm stuff
> How are timetables generated?

Timetable generation uses two different algorithms.
The first is a Greedy algorithm, which selects the most optimal choice at every iteration, so it focuses on filling up your timetable as early as possible.
This is the initial timetable, sometimes it's good, but usually it's bad (suboptimal).

The second is a Simulated Annealing algorithm.
It uses the intiial greedy algorithm, and randomly applies changes to it. It has a variable called 'Temperature' which decreases as the algorithm runs. High temperatures means the algorithm is more likely to select a suboptimal solution to escape a local optima. Eventually, once the temperature cools down enough, the algorithm will start to only accept changes that make the timetable better.

(Theres a bunch of other stuff like cost calculation and penalties but that's not really too important. I'll have a more detailed explanation in the docs.)
Features
- Dynamic timetable
- task priorities
- sync between devices
- repeating tasks (you can choose when it repeats, eg every 3 days, 7 weeks or 2 years)
- weekly/monthly goals (these things dont have a set time, but dynamically fit themselves into any available time slots. > has a min/max time goal > mahybe a setting called 'allowSplit' which means either)
- some tasks have a minimum time, they can grow and shrink, but at least X minutes have to be allocated every day. (useful for stuff like homework, always spend at least an hour on one subject, but it time allows, maybe spend 2 hours)
- blocking constraints : some blocks can only go on certain days/weeks
- add support for mono/bi/tri weekly timetables (for school)
- use APIs to get important dates (school holidays, public holidays, etc)
- interactable notifications, eventually also a phone widget
- this should run self-hosted, with a main computer running the backend/server and all other devices running a client (app, web, tui)



Planned




WOrking on it





Finished




---

# Blocks

ToDo
- most basic, only has a title
- can be assigned to a day or is just there

Tasks
- a ToDo happens at a certain time
- can have a description



> All blocks have a setting that specfies have much time forward and backward it can be shifted from it's original time.
> E.g. a task at 4.00 pm with a forward bound of 30 mins and a backward bound of 2 hours can be reallocated to a time between 3.30pm to 6.00pm if a block of higher priority requires it's time slot

# Data

Block
- Can be of type : task, class, habit, hobby?, or a custom type
- stores start and end time
- stores description
- can be marked as completed
- has a priority

TImetable
- blocks are linked to a timetable
- contains the times

---

# What the backend sees/needs

Activity
+ priority
+ repeat mode
+ repeat_interval
+ frequency
+ even_frequency_spacing
+ min_length
+ max_lenght
+ min_time
+ max_time
+ time_limit_reset
- time_spent

# what the clients see/need
Activity
+ priority
+ repeat mode
+ repeat_interval
+ frequency
+ even_frequency_spacing
+ min_length
+ max_lenght
+ min_time
+ max_time
+ time_limit_reset

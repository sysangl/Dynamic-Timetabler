import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()



# Time table blocking
# What appears on and what is stored in the timetable
#

class ToDo(db.Model):
    id = db.Column(db.Uuid, primary_key=True)
    title = db.Column(db.String(60), nullable=False)

class Task(ToDo):
    description = db.Column(db.String(300))
    start_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time)

class Block(Task):
    end_date = db.Column(db.Date,nullable=False)
    end_time = db.Column(db.Time)


class ClassBlock(Block):
    pass


# Activities
# For auto-generating timetables, blocks are created from these and their constraints
#

class Activity(db.Model):
    id = db.Column(db.Uuid, primary_key = True)

    # set the priority of this acitivity
    # lower priority means this activity's blocks can be moved around
    priority = db.Column(db.Integer, nullable = False)

    # 0 - no repeat/oneshot
    # 1 - repeat every X
    # 2 - use frequency
    repeat_mode = db.Column(db.Integer, nullable = False)

    # repeat_interval -> [0,0,0,0,0]
    # repeat every [hour, day, week, month, year]
    repeat_interval = db.Column(db.Array(db.Integer)) 

    # e.g. 2 times a week, 5 times a year
    # stored as [X, Y, Z]
    # means X times every Y Z's
    # for example [2, 1, 2] means, 2 times every 1 week.
    # Z values :
    # 0 - hours
    # 1 - days
    # 2 - weeks
    # 3 - months
    # 4 - years
    #
    # note: i will see how this system goes, if it is too messy, then i will just use
    #  an array [X,Y], Y will be the number of hours
    # this simpler approach may cause problems with detecting boundaries of, for example, each week
    frequency = db.Column(db.ARRAY(db.Integer))
    # try to evenly space frequencies, or just have multiple instances randomly
    # TRUE   |   FALSE
    # -      |   -
    # X      |   X
    # -      |   X
    # -      |   -
    # X      |   -
    # -      |   X
    # -      |   -
    # X      |   -
    # -      |   -
    even_frequency_spacing = db.Column(db.Boolean)

    # the following are in minutes
    # minimum length of one block of this activity
    min_length = db.Column(db.Integer)
    # maximum length of one block of this activity
    max_length = db.Column(db.Integer)
    # minimum amount of time spenton the activity
    min_time = db.Column(db.Integer)
    # maximum time spent on activity
    # e.g. max game time of 4 hours total every day
    max_time = db.Column(db.Integer)


    # reset the time counter every [hour, day, week, month, year] 
    time_limit_reset = db.Column(db.Array(db.Integer))

    # time spent doing this activity in minutes
    time_spent = db.Column(db.Integer)

# i wanted to name this 'Class' but that would probably confusing for me
class Subject(Activity):
    teacher = db.Column(db.String(40))
    classroom = db.Column(db.String(20))



# Settings
#
#

# class Settings(db.Model):
#     default_block_length = db.Column(db.Integer) # minutes
#     starting_day = db.Column(db.Integer)
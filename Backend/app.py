from flask import Flask, request, jsonify
from models import *

app = Flask("Dynamic Timetabler")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

@app.route('/activities', methods=['GET'])
def get_activities():
    activities = Activity.query.all()
    return {'activities':[activity.serialize() for activity in activities]}

# @app.route('/activities/<uuid:id>',methods=['GET'])
# def get_activity(id):
#     activity:Activity = Activity.query.filter_by(id=id).first()
#     result = activity.serialize() if activity else -1
#     return result


@app.route('/activities', methods=['POST'])
def create_activity():
    data = request.get_json()

    activity = Activity(
        priority = data['priority'],
        repeat_mode = data['repeat_mode'],
        repeat_interval = data['repeat_interval'],

        frequency = data['frequency'],
        even_frequency_spacing = data['even_frequency_spacing'],
        min_length = data['min_length'],
        max_length = data['max_length'],
        min_time = data['min_time'],
        max_time = data['max_time'],

        time_limit_reset = data['time_limit_reset'],

        time_spent = 0

    )
    db.session.add(activity)
    db.session.commit()

    return jsonify(activity.serialize())

@app.route('/activities/<uuid:id>', methods=['PUT'])
def update_activity(id):
    pass

@app.route('/activities/<uuid:id>', methods=['DELETE'])
def delete_activity(id):
    pass
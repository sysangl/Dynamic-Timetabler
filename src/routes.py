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

    db.session.add(activity)
    db.session.commit()

    return jsonify(activity.serialize())

@app.route('/activities/<uuid:id>', methods=['PUT'])
def update_activity(id):
    pass

@app.route('/activities/<uuid:id>', methods=['DELETE'])
def delete_activity(id):
    pass
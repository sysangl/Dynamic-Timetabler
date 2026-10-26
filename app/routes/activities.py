from flask import Flask, request, jsonify, Blueprint
from app.models import (
    db,
    Activity
)
import logging

bp = Blueprint('activities',__name__)

app_logger = logging.getLogger('app')
db_logger = logging.getLogger('database')
def create_routes(app: Flask):

    @bp.route('/', methods=['GET'])
    def get_activities():
        activities = Activity.query.all()
        return jsonify({'activities':[activity.serialise() for activity in activities]}), 200

    @bp.route('/<int:id>',methods=['GET'])
    def get_activity(id):
        activity = Activity.query.filter_by(id=id).first()
        if not activity:
            return {'error':f'Activity with id "{id}" does not exist'}, 404
        result = activity.serialise() if activity else -1
        return jsonify(result)

    @bp.route('/create', methods=['PUT'])
    def create_activity():
        data = request.get_json()
        app.logger.info(f"Attempting to create an activity from: {data}")
        app_logger.info(f"Attempting to create an activity from: {data}")

        try:
            activity = Activity(
                **data
            )
        except TypeError as e:
            return jsonify({'error':'Recieved invalid datatype in a field.'})

        try:
            db_logger.info(f'Attempting to create Activity:{activity.name}')
            db.session.add(activity)
            db.session.commit()
        except Exception:
            db.session.rollback()
            db_logger.exception(f'Database error while trying to create Activity instance')
            return jsonify({'error':f'Database error while trying to create Activity instance'})
        db_logger.info(f'Successfully created Activity:{activity.name} (id:{activity.id})')
        return jsonify(activity.serialise())

    @bp.route('/<int:id>', methods=['PUT'])
    def update_activity(id):

        data = request.get_json()
        activity = Activity.query.filter_by(id=id).first()
        if not activity:
            return {'error':f'Activity with id "{id}" does not exist'}, 404
        for key in data.keys():
            try:
                activity.__setattr__(key, data[key])
            except Exception as e:
                return {'error' : f'Invalid key : {str(e)}'}, 500

        db.session.commit()
        return jsonify(activity.serialise())
        

    @bp.route('/<int:id>', methods=['DELETE'])
    def delete_activity(id):
        activity = Activity.query.filter_by(id=id).first()
        if not activity:
            return {'error':f'Activity with id "{id}" does not exist'}, 404
        assert type(activity) is Activity
        try:
            db_logger.info(f'Attempting to delete Activity:{activity.name}:({id})')
            db.session.delete(activity)
            db.session.commit()
        except Exception:
            db.session.rollback()
            return jsonify({'error':f'Database error while trying to delete Activity:{activity.name} (id:{id})'})
        db_logger.info(f'Successfully deleted Activity:{activity.name}:({id})')
        return jsonify({'success': f'Activity {activity.name} ({activity.id}) deleted successfully'}), 200
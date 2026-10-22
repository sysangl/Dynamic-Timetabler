from flask import Flask, request, jsonify, Blueprint, url_for, redirect
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta
from helpers.datetime import combine_date_time
from sqlalchemy import func, Date
from helpers.config import get_config
import pytz

from app.models import (
    db,
    ToDo,
    Task,
    Block,
    Activity
)
import logging

bp = Blueprint('timetable', __name__)

server_logger = logging.getLogger('server')
app_logger = logging.getLogger('app')
db_logger = logging.getLogger('database')


def parse_iso_date(s: str):
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return None

def create_routes(app: Flask):
    @bp.route('/', methods=['GET'])
    @login_required
    def get():
        server_logger.info(f'Fetching timetable items for User:{current_user.username} (id:{current_user.id})')

        try:
            #todos = ToDo.query.filter().all()
            #tasks = Task.query.all()
            blocks = Block.query.filter(
                    Block.owner_id == current_user.id,
                ).all()

            payload = {
                #"todos": [todo.serialise() for todo in todos],
                #"tasks": [task.serialise() for task in tasks],
                "blocks": [block.serialise() for block in blocks]
            }

            app.logger.info(payload)

        except Exception:
            server_logger.exception("Failed to fetch timetable items")
            raise
        return jsonify(payload), 200


    @bp.route('/range/', methods=['GET'])
    @login_required
    def get_range():
        start_date = parse_iso_date(request.args.get('start','').strip())
        end_date = parse_iso_date(request.args.get('end','').strip())

        server_logger.info(f'Fetching timetable items for User:{current_user.username} (id:{current_user.id})')

        if not start_date or not end_date:
            start_date = datetime.now().date()
            end_date = start_date
        else:
            if end_date < start_date:
                start_date, end_date = end_date, start_date

        app.logger.info(f'Getting blocks for {start_date} - {end_date}')

        try:
            #todos = ToDo.query.filter().all()
            #tasks = Task.query.all()
            blocks = Block.query.filter(
                    Block.owner_id == current_user.id,
                    Block.start_datetime <= datetime.combine(end_date, datetime.max.time()),
                    Block.end_datetime >= datetime.combine(start_date, datetime.min.time())
                ).all()

            payload = {
                #"todos": [todo.serialise() for todo in todos],
                #"tasks": [task.serialise() for task in tasks],
                "blocks": [block.serialise() for block in blocks]
            }

            app.logger.info(payload)

        except Exception:
            server_logger.exception("Failed to fetch timetable items")
            raise
        return jsonify(payload), 200


    @bp.route('/<string:item>/<int:id>',methods=['GET'])
    @login_required
    def get_item(item, id):
        item_class = None
        match item:
            #case 'todos':
            #    item_class = ToDo
            #case 'tasks':
            #    item_class = Task
            case 'blocks':
                item_class = Block
            case _:
                return {'error': f'"{item}" is not a valid timetable item'}, 404
        assert type(item_class) is ToDo | Task| Block
        tti = item_class.query.filter_by(id=id).first()
        if not tti:
            return {'error':f'{item} with id "{id}" does not exist'}, 404
        result = tti.serialise() if tti else -1
        return jsonify(result)
    

    @bp.route('/<string:item>/create', methods=['POST'])
    @login_required
    def create_item(item):
        app.logger.info(f"Attempting to create a {item} from: {request.form}")
        app_logger.info(f"Attempting to create a {item} from: {request.form}")

        item_class = None
        match item:
            #case 'todos':
            #    item_class = ToDo
            #case 'tasks':
            #    item_class = Task
            case 'block':
                item_class = Block
            case _:
                app.logger.info(f'"{item}" is not a valid timetable item')
                app_logger.info(f'"{item}" is not a valid timetable item')
                return {'error': f'"{item}" is not a valid timetable item'}, 404
        #assert type(item_class) is ToDo | Task| Block
        data : dict = dict(request.form)

        data['start_datetime'] = combine_date_time(request.form.get('start_date'),request.form.get('start_time'), tz=get_config()["general"]["timezone"]) # type: ignore
        data['end_datetime'] = combine_date_time(request.form.get('end_date'),request.form.get('end_time'), tz=get_config()["general"]["timezone"]) #type: ignore

        created_item = item_class(
            **data,
            owner = current_user # type: ignore
        )
        created_item.owner_id = current_user.id
        try:
            db.session.add(created_item)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            db_logger.exception(f'Database error while trying to create "{item}" instance')
            return jsonify({'error':f'Database error while trying to create {item} instance'}), 500
            
        db_logger.info(f'Successfully created a "{item}" instance for {current_user.username}')
        return redirect(url_for('app.serve_management'))

    @bp.route('/<string:item>/<int:id>', methods=['PUT'])
    @login_required
    def update_item(item,id):

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
        

    @bp.route('/<string:item>/<int:id>', methods=['DELETE'])
    @login_required
    def delete_item(item, id):
        item_class = None
        match item:
            #case 'todos':
            #    item_class = ToDo
            #case 'tasks':
            #    item_class = Task
            case 'block':
                item_class = Block
            case _:
                app.logger.info(f'"{item}" is not a valid timetable item')
                app_logger.info(f'"{item}" is not a valid timetable item')
                return {'error': f'"{item}" is not a valid timetable item'}, 404
        item_to_delete = item_class.query.filter_by(id=id).first()
        if not item_to_delete:
            return {'error':f'{item} with id "{id}" does not exist'}, 404
        if item_to_delete.owner_id != current_user.id:
            return {'error':f'{item} with id "{id}" does not belong to User:{current_user.username} (id:{current_user.id})'}, 403
        assert type(item_to_delete) is not None
        try:
            db.session.delete(item_to_delete)
            db.session.commit()
        except Exception:
            db.session.rollback()
            db_logger.exception(f'Database error while trying to delete {item}:"{item_to_delete.title}"')
            return jsonify({'error':f'Database error while trying to delete {item}:"{item_to_delete.title}'})
        db_logger.info(f'Successfully deleted {item}:"{item_to_delete.title}"')
        return jsonify({'success': f'{item} {item_to_delete.title} ({item_to_delete.id}) deleted successfully'}), 200
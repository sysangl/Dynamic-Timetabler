from flask import Flask, request, jsonify, Blueprint
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from datetime import datetime

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

def create_routes(app: Flask):
    @bp.route('/', methods=['GET'])
    @login_required
    def get_timetable():
        # data = request.get_json()
        # if data:
        #     todos = ToDo.query.filter().all()
        #     tasks = ToDo.query.filter().all()
        #     blocks = Block.query.filter().all()
        # else:
        server_logger.info(f'Fetching timetable items for User:{current_user.username} (id:{current_user.id})')
        
        try:
            #todos = ToDo.query.filter().all()
            #tasks = Task.query.all()
            blocks = Block.query.filter(Block.owner_id == current_user.id).all()

            payload = {
                #"todos": [todo.serialise() for todo in todos],
                #"tasks": [task.serialise() for task in tasks],
                "blocks": [block.serialise() for block in blocks]
            }
        except Exception:
            server_logger.exception("Failed to fetch timetable items")
            raise


        return jsonify(payload)


    @bp.route('/<string:item>', methods=['GET'])
    @login_required
    def get_timetable_items(item):
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
        #assert type(item_class) is ToDo | Task| Block
        response_items = item_class.query.filter(item_class.owner_id == current_user.id).all()
        return jsonify({f'{item}':[item.serialise() for item in response_items]}), 200

    @bp.route('/<string:item>/<int:id>',methods=['GET'])
    @login_required
    def get_timetable_item(item, id):
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
    def create_timetable_item(item):
        data = request.get_json()
        app.logger.info(f"Attempting to create a {item} from: {data}")
        app_logger.info(f"Attempting to create a {item} from: {data}")

        item_class = None
        match item:
            #case 'todos':
            #    item_class = ToDo
            #case 'tasks':
            #    item_class = Task
            case 'blocks':
                item_class = Block
            case _:
                app.logger.info(f'"{item}" is not a valid timetable item')
                app_logger.info(f'"{item}" is not a valid timetable item')
                return {'error': f'"{item}" is not a valid timetable item'}, 404
        #assert type(item_class) is ToDo | Task| Block
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
        return jsonify(created_item.serialise()), 202

    @bp.route('/<string:item>/<int:id>', methods=['PUT'])
    @login_required
    def update_timetable_item(item,id):

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
    def delete_timetable_item(item, id):
        item_class = None
        match item:
            #case 'todos':
            #    item_class = ToDo
            #case 'tasks':
            #    item_class = Task
            case 'blocks':
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
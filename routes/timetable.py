from flask import Flask, request, jsonify
from sqlalchemy.orm import joinedload
from datetime import datetime
from models import (
    db,
    ToDo,
    Task,
    Block,
    Activity
)

def create_routes(app: Flask):
    @app.route('/server/timetable', methods=['GET'])
    def get_timetable():
        # data = request.get_json()
        # if data:
        #     todos = ToDo.query.filter().all()
        #     tasks = ToDo.query.filter().all()
        #     blocks = Block.query.filter().all()
        # else:
        todos = ToDo.query.all()
        tasks = Task.query.all()
        blocks = Block.query.all()

        payload = {
            "todos": [todo.serialise() for todo in todos],
            "tasks": [task.serialise() for task in tasks],
            "blocks": [block.serialise() for block in blocks]
        }

        return jsonify(payload)


    @app.route('/server/timetable/<string:item>', methods=['GET'])
    def get_timetable_items(item):
        item_class = None
        match item:
            case 'todos':
                item_class = ToDo
            case 'tasks':
                item_class = Task
            case 'blocks':
                item_class = Block
            case _:
                return {'error': f'"{item}" is not a valid timetable item'}, 404
        #assert type(item_class) is ToDo | Task| Block
        response_items = item_class.query.all()
        return jsonify({f'{item}':[item.serialise() for item in response_items]}), 200

    @app.route('/server/timetable/<string:item>/<int:id>',methods=['GET'])
    def get_timetable_item(item, id):
        item_class = None
        match item:
            case 'todos':
                item_class = ToDo
            case 'tasks':
                item_class = Task
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
        


    @app.route('/server/timetable/<string:item>/create', methods=['POST'])
    def create_timetable_item(item):
        data = request.get_json()
        app.logger.info(f"Attempting to create an {item} from: {data}")

        item_class = None
        match item:
            case 'todos':
                item_class = ToDo
            case 'tasks':
                item_class = Task
            case 'blocks':
                item_class = Block
            case _:
                app.logger.warning(f'"{item}" is not a valid timetable item')
                return {'error': f'"{item}" is not a valid timetable item'}, 404
        #assert type(item_class) is ToDo | Task| Block
        created_item = item_class(
            **data
        )

        db.session.add(created_item)
        db.session.commit()

        return jsonify(created_item.serialise()), 202

    @app.route('/server/timetable/<string:item>/<int:id>', methods=['PUT'])
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
        

    @app.route('/server/timetable/<string:item>/<int:id>', methods=['DELETE'])
    def delete_timetable_item(item, id):
        item_class = None
        match item:
            case 'todos':
                item_class = ToDo
            case 'tasks':
                item_class = Task
            case 'blocks':
                item_class = Block
            case _:
                app.logger.warning(f'"{item}" is not a valid timetable item')
                return {'error': f'"{item}" is not a valid timetable item'}, 404
        item_to_delete = item_class.query.filter_by(id=id).first()
        if not item_to_delete:
            return {'error':f'{item} with id "{id}" does not exist'}, 404
        assert type(item_to_delete) is not None
        db.session.delete(item_to_delete)
        db.session.commit()
        return jsonify({'success': f'{item} {item_to_delete.title} ({item_to_delete.id}) deleted successfully'}), 200
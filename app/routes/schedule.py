import logging
from datetime import datetime, time
from typing import Any

from flask import Blueprint, request
from flask_login import current_user, login_required
from sqlalchemy.exc import SQLAlchemyError

from helpers.config import get_config
from helpers.datetime import combine_date_time, parse_iso_date
from helpers.server import _json_error, _json_success

from ..extensions import db
from ..models import Activity, Block, Schedule

bp = Blueprint('schedules', __name__)

log = logging.getLogger('app')



@bp.route('/', methods=['GET'])
@login_required
def get_items():
    log.info(f'Fetching timetable items for User:{current_user.username} (id:{current_user.id})')

    try:
        schedules = Schedule.query.filter(
                Schedule.owner_id == current_user.id,
            ).all()
        activities = Activity.query.filter(
                Activity.owner_id == current_user.id
        ).all()

        payload = {
            #"todos": [todo.serialise() for todo in todos],
            #"tasks": [task.serialise() for task in tasks],
            "schedules": [schedule.serialise() for schedule in schedules],
            "activities": [activity.serialise() for activity in activities]
        }

        return _json_success(payload)
    except Exception:
        log.exception("Failed to fetch schedule items.")
        return _json_error("Failed to retrieve schedule items.", 500)


@bp.route('/<string:item>/<int:id>',methods=['GET'])
@login_required
def get_item(item: str, id: int):
    item_class = None
    match item:
        case 'schedule':
            item_class = Schedule
        case 'activity':
            item_class = Activity
        case _:
            log.info(f'"{item}" is not a valid timetable item')
            return _json_error(f'"{item}" is not a valid schedule item', 404)
    si = item_class.query.filter_by(id=id).first()
    if not si:
        return _json_error(f'{item} with id "{id}" does not exist', 404)
    return _json_success(si.serialise())


@bp.route('/create', methods=['POST'])
@login_required
def create_item():
    data = request.get_json()
    tz = get_config()["general"]["timezone"]
    data['start_date'] = parse_iso_date(data.get('start_date'))
    # data['early'] = combine_date_time(data.get('start_date'),data.get('start_time'), tz=tz) # type: ignore
    # data['late'] = combine_date_time(data.get('end_date'),data.get('end_time'), tz=tz) #type: ignore

    s = Schedule(
        **data,
        owner = current_user # type: ignore
    )
    s.owner_id = current_user.id
    try:
        db.session.add(s)
        db.session.commit()
        log.info(f'Successfully created a "Schedule" instance for {current_user.username}')
        # return redirect(url_for('app.serve_management'))
        return _json_success(s.serialise(), 201)
    except Exception:
        db.session.rollback()
        log.exception('Database error while trying to create "Schedule" instance')
        return _json_error('Database error while trying to create "Schedule" instance', 500)
        


@bp.route('/<int:id>', methods=['PUT'])
@login_required
def update_item(id):
    data = request.get_json()

    s = Schedule.query.filter_by(id=id).first()
    if not s:
        return {'error':f'"Schedule" with id: {id} does not exist'}, 404
    for key in data:
        try:
            s.__setattr__(key, data[key])
        except Exception as e:  # noqa: BLE001
            return _json_error(f'Invalid key : {e!s}', 500)

    try:
        db.session.commit()
        log.info(f'Updated "Schedule" (id: {id}) for user {current_user.username}')
        return _json_success(s.serialise())
    except SQLAlchemyError:
        db.session.rollback()
        log.exception(f'Database error while updating "Schedule" (id:{id}) for user {current_user.username}')
        return _json_error('Failed to update "Schedule".', 500)

@bp.route('/<int:id>', methods=['DELETE'])
@login_required
def delete_item(id):
    s = Schedule.query.filter_by(id=id).first()
    if not s:
        return _json_error(f'"Schedule" with id "{id}" does not exist', 404)
    if s.owner_id != current_user.id:
        return _json_error(f'"Schedule" with id "{id}" does not belong to User:{current_user.username} (id:{current_user.id})', 403)

    try:
        db.session.delete(s)
        db.session.commit()
        log.info(f'Successfully deleted Schedule:"{s.title}"')
        return _json_success({'message':f'"Schedule" {s.title} ({s.id}) deleted successfully'})
    except SQLAlchemyError:
        db.session.rollback()
        log.exception(f'Database error while trying to delete Schedule:"{s.title}"')
        return _json_error(f'Database error while trying to delete Schedule:"{s.title}', 500)


@bp.route('/<int:id>/activities/blocks',methods=['GET'])
@login_required
def get_blocks_from_activity_group(id:int):
    schedules = Schedule.query.filter(
        Schedule.owner == current_user,
        Schedule.id == id
        ).all()
    return _json_success({'schedules':[s.serialise() for s in schedules]})

@bp.route('/<int:id>/activities/blocks',methods=['DELETE'])
@login_required
def delete_activity_blocks(id:int):
    schedules = Schedule.query.filter(
        Schedule.owner == current_user,
        Schedule.id == id
        ).all()
    for s in schedules:
        s.activity.blocks.remove(s)
        db.session.delete(s)
    try:
        db.session.commit()
        log.info(f'Successfully deleted all blocks in Schedule (id:{id})')
        return _json_success({'msg':'success'})
    except SQLAlchemyError:
        db.session.rollback()
        log.exception(f'Database error while trying to delete "Schedule (id:{id})" blocks')
        return _json_error(f'Database error while trying to delete "Schedule (id:{id})" blocks', 500)
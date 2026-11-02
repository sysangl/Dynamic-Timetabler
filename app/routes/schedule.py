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
    log.info(f'Fetching schedule items for User:{current_user.username} (id:{current_user.id})')

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


@bp.route('/<int:id>',methods=['GET'])
@login_required
def get_item(item: str, id: int):
    schedule = Schedule.query.filter(
        Schedule.owner == current_user,
        Schedule.id == id
    ).first()
    if not schedule:
        return _json_error(f'Schedule with id "{id}" does not exist', 404)
    return _json_success(schedule.serialise())


@bp.route('/create', methods=['POST'])
@login_required
def create_schedule():
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
        

@bp.route('/<int:id>', methods=['DELETE'])
@login_required
def delete_schedule(id):
    s = Schedule.query.filter(
        Schedule.id == id,
        Schedule.owner == current_user
        ).first()
    if not s:
        return _json_error(f'"Schedule" with id "{id}" does not exist', 404)
    try:
        db.session.delete(s)
        db.session.commit()
        log.info(f'Successfully deleted Schedule:"{s.title}"')
        return _json_success({'message':f'"Schedule" {s.title} ({s.id}) deleted successfully'})
    except SQLAlchemyError:
        db.session.rollback()
        log.exception(f'Database error while trying to delete Schedule:"{s.title}"')
        return _json_error(f'Database error while trying to delete Schedule:"{s.title}', 500)


@bp.route('/<int:id>/blocks',methods=['GET'])
@login_required
def get_schedule_blocks(id:int):
    # s = Schedule.query.filter(
    #     Schedule.owner == current_user,
    #     Schedule.id == id
    #     ).first()
    # if not s:
    #     return _json_error(f'"Schedule" with id "{id}" does not exist', 404)
    # blocks:set[Block] = set()
    # for a in s.activities:
    #     blocks += a.blocks
    
    blocks = Block.query.filter(
        Block.activity.schedule.id == id
    )
    return _json_success({'blocks':[b.serialise() for b in blocks]})

@bp.route('/<int:id>/blocks',methods=['DELETE'])
@login_required
def delete_schedule_blocks(id:int):
    blocks = Block.query.filter(
        Block.activity.schedule.id == id
    )
    # s:Schedule|None = Schedule.query.filter(
    #     Schedule.owner == current_user,
    #     Schedule.id == id
    #     ).first()
    # if not s:
    #     return _json_error(f'"Schedule" with id "{id}" does not exist', 404)
    # for a in s.activities:
    for b in blocks:
        b.activity.blocks.remove(b)
        db.session.delete(b)
    try:
        db.session.commit()
        log.info(f'Successfully deleted all blocks in Schedule (id:{id})')
        return _json_success({'msg':'success'})
    except SQLAlchemyError:
        db.session.rollback()
        log.exception(f'Database error while trying to delete "Schedule (id:{id})" blocks')
        return _json_error(f'Database error while trying to delete "Schedule (id:{id})" blocks', 500)
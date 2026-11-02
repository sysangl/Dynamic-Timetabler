import logging
import uuid
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
            "schedules": [schedule.serialise() for schedule in schedules],
            "activities": [activity.serialise() for activity in activities]
        }

        return _json_success(payload)
    except Exception:
        log.exception("Failed to fetch schedule items.")
        return _json_error("Failed to retrieve schedule items.", 500)


@bp.route('/<string:sid>',methods=['GET'])
@login_required
def get_item(sid: str):
    try:
        suuid = uuid.UUID(sid)
    except ValueError:
        return _json_error(f'"{sid}" is not a valid Schedule ID')
    schedule = Schedule.query.filter(
        Schedule.owner == current_user,
        Schedule.id == suuid
    ).first()
    if not schedule:
        return _json_error(f'Schedule with id "{sid}" does not exist', 404)
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
        return _json_success(s.serialise(), 201)
    except Exception:
        db.session.rollback()
        log.exception('Database error while trying to create "Schedule" instance')
        return _json_error('Database error while trying to create "Schedule" instance', 500)

@bp.route('/<string:sid>/activities/create', methods=['POST'])
@login_required
def create_activity(sid:str):
    data = request.get_json()
    try:
        suuid = uuid.UUID(sid)
    except ValueError:
        return _json_error(f'"{sid}" is not a valid Schedule ID')
    s:Schedule|None = Schedule.query.filter(
        Schedule.id == suuid,
        Schedule.owner == current_user
        ).first()
    if not s:
        return _json_error(f'"Schedule" with id "{sid}" does not exist', 404)
    data['min_start_time'] = time.fromisoformat(data.get('min_start_time'))
    data['preferred_days'] = str(data.get('preferred_days')).split()

    a = Activity(
        **data,
        owner=s.owner,
    )
    a.schedule = s
    a.schedule_id = s
    a.owner_id = s.owner.id
    s.activities.add(a)

    try:
        db.session.add(a)
        db.session.commit()
        log.info(f'Successfully created an Activity instance for {current_user.username}')
        return _json_success(a.serialise(), 201)
    except Exception:
        db.session.rollback()
        log.exception('Database error while trying to create "Activity" instance')
        return _json_error('Database error while trying to create "Activity" instance', 500)

@bp.route('/<string:sid>/activities',methods=['GET'])
@login_required
def get_schedule_activities(sid: str):
    try:
        suuid = uuid.UUID(sid)
    except ValueError:
        return _json_error(f'"{sid}" is not a valid Schedule ID')
    schedule = Schedule.query.filter(
        Schedule.owner == current_user,
        Schedule.id == suuid
    ).first()
    if not schedule:
        return _json_error(f'Schedule with id "{sid}" does not exist', 404)
    return _json_success({'activities':[a.serialise() for a in schedule.activities]})

@bp.route('/<string:sid>/activities/<string:aid>',methods=['DELETE'])
@login_required
def delete_schedule_activity(sid: str, aid:str):
    try:
        suuid = uuid.UUID(sid)
    except ValueError:
        return _json_error(f'"{sid}" is not a valid Schedule ID')
    schedule = Schedule.query.filter(
        Schedule.owner == current_user,
        Schedule.id == suuid
    ).first()
    if not schedule:
        return _json_error(f'Schedule with id "{sid}" does not exist', 404)

    try:
        auuid = uuid.UUID(aid)
    except ValueError:
        return _json_error(f'"{aid}" is not a vlaid Activity id')
    a = Activity.query.filter(
        Activity.schedule == schedule,
        Activity.id == auuid,
    ).first()

    if not a:
        return _json_error(f'Activity with id "{aid}" does not exist', 404)

    try:
        db.session.delete(a)
        db.session.commit()
        log.info(f'Successfully deleted Activity:"{a.title}"')
        return _json_success({'message':f'Activity {a.title} ({a.id}) deleted successfully'})
    except SQLAlchemyError:
        db.session.rollback()
        log.exception(f'Database error while trying to delete Activity:"{a.title}"')
        return _json_error(f'Database error while trying to delete Activity:"{a.title}', 500)



@bp.route('/<string:sid>', methods=['DELETE'])
@login_required
def delete_schedule(sid:str):
    try:
        suuid = uuid.UUID(sid)
    except ValueError:
        return _json_error(f'"{sid}" is not a valid Schedule ID')
    s = Schedule.query.filter(
        Schedule.id == suuid,
        Schedule.owner == current_user
        ).first()
    if not s:
        return _json_error(f'"Schedule" with id "{sid}" does not exist', 404)
    try:
        db.session.delete(s)
        db.session.commit()
        log.info(f'Successfully deleted Schedule:"{s.title}"')
        return _json_success({'message':f'"Schedule" {s.title} ({s.id}) deleted successfully'})
    except SQLAlchemyError:
        db.session.rollback()
        log.exception(f'Database error while trying to delete Schedule:"{s.title}"')
        return _json_error(f'Database error while trying to delete Schedule:"{s.title}', 500)


@bp.route('/<string:sid>/blocks',methods=['GET'])
@login_required
def get_schedule_blocks(sid:str):
    # s = Schedule.query.filter(
    #     Schedule.owner == current_user,
    #     Schedule.id == id
    #     ).first()
    # if not s:
    #     return _json_error(f'"Schedule" with id "{id}" does not exist', 404)
    # blocks:set[Block] = set()
    # for a in s.activities:
    #     blocks += a.blocks
    try:
        suuid = uuid.UUID(sid)
    except ValueError:
        return _json_error(f'"{sid}" is not a valid Schedule ID')
    blocks = Block.query.filter(
        Block.activity.schedule.id == suuid
    )
    return _json_success({'blocks':[b.serialise() for b in blocks]})

@bp.route('/<string:sid>/blocks',methods=['DELETE'])
@login_required
def delete_schedule_blocks(sid:str):
    try:
        suuid = uuid.UUID(sid)
    except ValueError:
        return _json_error(f'"{sid}" is not a valid Schedule ID')
    blocks = Block.query.filter(
        Block.activity.schedule.id == suuid
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
        log.info(f'Successfully deleted all blocks in Schedule (id:{sid})')
        return _json_success({'msg':'success'})
    except SQLAlchemyError:
        db.session.rollback()
        log.exception(f'Database error while trying to delete "Schedule (id:{sid})" blocks')
        return _json_error(f'Database error while trying to delete "Schedule (id:{sid})" blocks', 500)
import logging
import zoneinfo
from datetime import datetime, time, timedelta
from typing import Any

from flask import Blueprint, request
from flask_login import current_user, login_required
from sqlalchemy.exc import SQLAlchemyError

from helpers.config import get_config
from helpers.datetime import combine_date_time, parse_iso_date
from helpers.server import _json_error, _json_success

from ..extensions import db
from ..models import Activity, Block

bp = Blueprint("timetable", __name__)

log = logging.getLogger("app")


def validate_item_type(
    item,
) -> type[Block] | type[Activity] | tuple[dict[str, Any], int]:
    match item:
        case "block":
            item_class = Block
        case "activity":
            item_class = Activity
        case _:
            log.info(f'"{item}" is not a valid timetable item')
            return _json_error(f'"{item}" is not a valid timetable item', 404)
    return item_class


@bp.route("/", methods=["GET"])
@login_required
def get_items():
    log.info(
        f"Fetching timetable items for User:{current_user.username} (id:{current_user.id})"
    )

    try:
        # todos = ToDo.query.filter().all()
        # tasks = Task.query.all()
        blocks = Block.query.filter(
            Block.owner_id == current_user.id,
        ).all()
        activities = Activity.query.filter(Activity.owner_id == current_user.id).all()

        payload = {
            # "todos": [todo.serialise() for todo in todos],
            # "tasks": [task.serialise() for task in tasks],
            "blocks": [block.serialise() for block in blocks],
            "activities": [activity.serialise() for activity in activities],
        }

        return _json_success(payload)
    except Exception:
        log.exception("Failed to fetch timetable items.")
        return _json_error("Failed to retrieve timetable items.", 500)

@bp.route("/upcoming/", methods=["GET"])
@login_required
def get_upcoming_items():
    log.info(
        f"Fetching upcoming timetable items for User:{current_user.username} (id:{current_user.id})"
    )

    tz = zoneinfo.ZoneInfo(get_config()["general"]["timezone"])
    try:
        now = datetime.now(tz).date()

        # todos = ToDo.query.filter().all()
        # tasks = Task.query.all()
        blocks:list[Block] = Block.query.filter(
            Block.owner_id == current_user.id,
            Block.start_datetime >= now,
            Block.end_datetime <= (now+timedelta(weeks=1)),
        ).all()

        search_count = 0
        while len(blocks) < 10:
            if search_count >= 14: # stop searching if no new events are found after two weeks
                break
            blocks += Block.query.filter(
                    Block.owner_id == current_user.id,
                    Block.start_datetime >= now+timedelta(days=search_count,weeks=1),
                    Block.end_datetime <=  (now+timedelta(days=search_count+1,weeks=1)),
                ).all()
            search_count += 1

        payload:dict[str, list[dict]] = {}

        for b in blocks:
            payload.setdefault(b.start_datetime.date().isoformat(),[])
            payload[b.start_datetime.date().isoformat()].append(b.serialise())
        
        return _json_success(payload)
    except Exception:
        log.exception("Failed to fetch upcoming timetable items.")
        return _json_error("Failed to retrieve upcoming timetable items.", 500)



@bp.route("/range/", methods=["GET"])
@login_required
def get_items_in_range():
    start_str = request.args.get("start", "") or request.args.get("from", "")
    end_str = request.args.get("end", "") or request.args.get("until", "")
    start_date = parse_iso_date(start_str.strip()) if start_str else None
    end_date = parse_iso_date(end_str.strip()) if end_str else None

    log.info(
        f"Fetching timetable items for User:{current_user.username} (id:{current_user.id})"
    )

    if not start_date and not end_date:
        start_date = datetime.now().date()
        end_date = start_date
    if start_date and end_date and end_date < start_date:
        start_date, end_date = end_date, start_date

    log.info(f"Getting blocks for {start_date} - {end_date}")

    try:
        blocks = []
        blocks = Block.query.filter(
            Block.owner_id == current_user.id,
        )
        if start_date:
            blocks = blocks.filter(
                Block.end_datetime >= datetime.combine(start_date, datetime.min.time())
            )
        if end_date:
            blocks = blocks.filter(
                Block.start_datetime <= datetime.combine(end_date, datetime.max.time()),
            )

        payload = {
            # "todos": [todo.serialise() for todo in todos],
            # "tasks": [task.serialise() for task in tasks],
            "blocks": [block.serialise() for block in blocks.all()]
        }

        return _json_success(payload)

    except Exception:
        log.exception("Failed to fetch timetable items")
        return _json_error("Failed to fetch timetable items.", 500)


@bp.route("/<string:item>/<int:id>", methods=["GET"])
@login_required
def get_item(item: str, id: int):
    item_class = None
    match item:
        case "block":
            item_class = Block
        case "activity":
            item_class = Activity
        case _:
            log.info(f'"{item}" is not a valid timetable item')
            return _json_error(f'"{item}" is not a valid timetable item', 404)
    tti = item_class.query.filter_by(id=id).first()
    if not tti:
        return _json_error(f'{item} with id "{id}" does not exist', 404)
    return _json_success(tti.serialise())


@bp.route("/<string:item>/create", methods=["POST"])
@login_required
def create_item(item: str):
    data = request.get_json()
    item_class = None
    match item:
        case "block":
            item_class = Block
        case "activity":
            item_class = Activity
        case _:
            log.info(f'"{item}" is not a valid timetable item')
            return _json_error(f'"{item}" is not a valid timetable item', 404)

    tz = get_config()["general"]["timezone"]
    if item_class in {Block}:
        data["start_datetime"] = combine_date_time(
            data.get("start_date"), data.get("start_time"), tz=tz
        )  # type: ignore
        data["end_datetime"] = combine_date_time(
            data.get("end_date"), data.get("end_time"), tz=tz
        )  # type: ignore
    if item_class in {Activity}:
        data["min_start_time"] = time.fromisoformat(data.get("min_start_time"))
        data["preferred_days"] = str(data.get("preferred_days")).split()

    created_item = item_class(
        **data,
        owner=current_user,  # type: ignore
        source="user"
    )
    created_item.owner_id = current_user.id
    try:
        db.session.add(created_item)
        db.session.commit()
        log.info(
            f'Successfully created a "{item}" instance for {current_user.username}'
        )
        # return redirect(url_for('app.serve_management'))
        return _json_success(created_item.serialise(), 201)
    except Exception:
        db.session.rollback()
        log.exception(f'Database error while trying to create "{item}" instance')
        return _json_error(
            f"Database error while trying to create {item} instance", 500
        )


@bp.route("/<string:item>/<int:id>", methods=["PUT"])
@login_required
def update_item(item, id):
    data = request.get_json()

    item_class = None
    match item:
        case "block":
            item_class = Block
        case "activity":
            item_class = Activity
        case _:
            log.info(f'"{item}" is not a valid timetable item')
            return _json_error(f'"{item}" is not a valid timetable item', 404)

    item = item_class.query.filter_by(id=id).first()
    if not item:
        return {"error": f'"{item}" with id: {id} does not exist'}, 404
    for key in data:
        try:
            item.__setattr__(key, data[key])
        except Exception as e:  # noqa: BLE001
            return _json_error(f"Invalid key : {e!s}", 500)

    try:
        db.session.commit()
        log.info(f"Updated {item} (id: {id}) for user {current_user.username}")
        return _json_success(item.serialise())
    except SQLAlchemyError:
        db.session.rollback()
        log.exception(
            f"Database error while updating {item} (id:{id}) for user {current_user.username}"
        )
        return _json_error(f"Failed to update {item}.", 500)

@bp.route("/blocks", methods=["PUT"])
@login_required
def update_blocks():
    data = request.get_json()

    print(f'Update with {data}')
    updated_blocks = data['blocks']

    tz = get_config()["general"]["timezone"]
    for ubid, ubdata in updated_blocks.items():
        cb = Block.query.filter(
            Block.id == ubid,
            Block.owner == current_user
            ).first()
        if not cb:
            continue
        assert type(cb) is Block
        cb.start_datetime = combine_date_time(
            ubdata.get("start_date"), ubdata.get("start_time"), tz=tz
        )  # type: ignore
        cb.end_datetime = combine_date_time(
            ubdata.get("end_date"), ubdata.get("end_time"), tz=tz
        )  # type: ignore


    try:
        db.session.commit()
        log.info(f"Updated {len(updated_blocks)} Blocks for user {current_user.username}")
        return _json_success({"msg":f"Updated {len(updated_blocks)} Blocks"})
    except SQLAlchemyError:
        db.session.rollback()
        log.exception(
            f"Database error while mass updating Blocks for user {current_user.username}"
        )
        return _json_error("Failed to update Blocks.", 500)

@bp.route("/<string:item>/<int:id>", methods=["DELETE"])
@login_required
def delete_item(item, id):
    item_class = None
    match item:
        case "block":
            item_class = Block
        case "activity":
            item_class = Activity
        case _:
            log.info(f'"{item}" is not a valid timetable item')
            return _json_error(f'"{item}" is not a valid timetable item', 404)

    item_to_delete = item_class.query.filter_by(id=id).first()
    if not item_to_delete:
        return _json_error(f'{item} with id "{id}" does not exist', 404)
    if item_to_delete.owner_id != current_user.id:
        return _json_error(
            f'{item} with id "{id}" does not belong to User:{current_user.username} (id:{current_user.id})',
            403,
        )

    try:
        db.session.delete(item_to_delete)
        db.session.commit()
        log.info(f'Successfully deleted {item}:"{item_to_delete.title}"')
        return _json_success(
            {
                "message": f"{item} {item_to_delete.title} ({item_to_delete.id}) deleted successfully"
            }
        )
    except SQLAlchemyError:
        db.session.rollback()
        log.exception(
            f'Database error while trying to delete {item}:"{item_to_delete.title}"'
        )
        return _json_error(
            f'Database error while trying to delete {item}:"{item_to_delete.title}', 500
        )

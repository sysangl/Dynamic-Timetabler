from __future__ import annotations

from ..extensions import db


class BaseModel(db.Model):
    __abstract__ = True
    def __repr__(self) -> str:
        classname = self.__class__.__name__
        primary_key = getattr(self,'id',None)
        return f'<{classname} id:{primary_key}>'
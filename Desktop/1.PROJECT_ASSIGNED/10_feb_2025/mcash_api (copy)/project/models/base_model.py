from datetime import datetime,timezone
from sqlalchemy import Column,  DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()


class BaseModel(Base):
    __abstract__ = True
    created_on = Column(DateTime, default=datetime.now(timezone.utc))
    updated_on = Column(DateTime, onupdate= datetime.now(timezone.utc) )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
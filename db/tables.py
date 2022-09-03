import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import Column, String, JSON, DATETIME

from db.base import MainDB


class BaseTable(MainDB.Base):
    __abstract__ = True

    # dump - any random stuff i forgot
    dump = Column(JSON, nullable=True)

    def __repr__(self) -> str:
        return '\n' + '\n'.join((f'{key:30s}:  {val}' for key, val in vars(self).items()
                                 if not key.startswith('_'))) + '\n'

    def update_from_dict(self, updated: dict):
        """
        Updates current object with a dict object. Useful for updating row or creating new objects from dict.
        :param updated:
        :return:
        """
        for key, value in updated.items():
            if '_ts' in key and value:  # turn all timestamps into datetime objects
                value = value.split('.')[0]
                value = datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')
                value = value.replace(tzinfo=ZoneInfo('America/Toronto'))
            setattr(self, key, value)
        return self

    def to_dict(self) -> dict:
        self_dict: dict = self.__dict__.copy()
        self_dict.pop('_sa_instance_state', None)

        # turn all ts back to strings
        for key, val in self_dict.copy().items():
            if '_ts' in key and val and not isinstance(val, str):
                self_dict[key] = val.strftime('%Y-%m-%dT%H:%M:%S')
        return self_dict


class Product(BaseTable):
    __tablename__ = 'products'

    _id = Column(String(255), primary_key=True, nullable=False, name='id')
    product_struct = Column(JSON, unique=False, nullable=True)  # from UserStruct.to_dict()
    dump = Column(JSON, unique=False, nullable=True)

    # ts
    product_added_ts = Column(DATETIME(timezone=True), nullable=True)
    product_updated_ts = Column(DATETIME(timezone=True), nullable=True)
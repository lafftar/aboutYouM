import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import Column, String, JSON, DATETIME, Integer

from db.base import MainDB


class BaseTable(MainDB.Base):
    __abstract__ = True

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
    def __hash__(self):
        return hash(self.dump)


    __tablename__ = 'products'

    """        
    This class is a [[ DIRECT ]] representation of a product in our db, which should be (🤞🏿) an exact replica of the 
    aboutyou db.
    
    IF YOU EDIT A PRODUCT OF THIS CLASS, YOU ARE DIRECTLY EDITING THE LOCAL DB.    
    """
    pid = Column(Integer, primary_key=True, nullable=False)

    # @todo - add these.
    # ts, these are just when it was added/updated to the local db. ( or maybe global db??? )
    # product_added_ts = Column(DATETIME(timezone=True), nullable=True)
    # product_updated_ts = Column(DATETIME(timezone=True), nullable=True)

    # dump - any random stuff i forgot, in this case, the entire product dict
    dump = Column(JSON, nullable=True)

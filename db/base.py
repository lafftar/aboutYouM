from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

from utils.root import get_project_root


class MainDB:
    # create connection engine
    base_db_engine = create_engine(f'sqlite:///{get_project_root()}/db/base.db')

    # init tables
    Base = declarative_base()

    @staticmethod
    def init_tables():
        """
        You need to import `tables` to wherever you plan on using this.
        :return:
        """
        MainDB.Base.metadata.create_all(MainDB.base_db_engine)

import asyncio

from colorama import Fore
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.orm import Session, sessionmaker

from db.base import MainDB
from db.tables import Product
from utils.custom_logger import Log
from utils.terminal import color_wrap


log = Log("[DB - ABOUT YOU.DE]")


class DB:
    # create db session
    main_session: Session = sessionmaker(bind=MainDB.base_db_engine, expire_on_commit=False)
    MainDB.init_tables()

    @staticmethod
    async def update_product(acc: Product):
        """
        Will update account or make a new account.
        :param acc:
        :return: None
        """

        def _update_product():
            with DB.main_session.begin() as short_session:
                current_acc_info: Product | None = \
                    short_session.query(Product) \
                        .filter(Product.email == acc.email) \
                        .first()
                try:
                    if current_acc_info:
                        current_acc_info.update_from_dict(acc.to_dict())
                        log.debug(color_wrap(Fore.WHITE + f'Updated {acc.email} in db.'))
                    else:
                        short_session.add(acc)
                        log.debug(color_wrap(Fore.WHITE + f'Added {acc.email} to db.'))
                except InvalidRequestError:
                    log.exception('Error Adding/Updating Account.')
                    input('Waiting')

        # update directly
        await asyncio.get_event_loop().run_in_executor(None, _update_product)

    @staticmethod
    async def return_product(email: str) -> Product | None:
        """
        :param email:
        :return: account or None
        """

        def _return_product():
            with DB.main_session.begin() as short_session:
                current_acc_info: Product | None = \
                    short_session.query(Product) \
                        .filter(Product.email == email) \
                        .first()

                if not current_acc_info:
                    log.debug(color_wrap(Fore.RED + f'Did not find {email} in db.'))
                    return
                log.debug(color_wrap(Fore.WHITE + f'Found {email} in db.'))
                return current_acc_info

        return await asyncio.get_event_loop().run_in_executor(None, _return_product)


if __name__ == "__main__":
    asyncio.run(DB.return_product('tibabalase@gmail.com'))

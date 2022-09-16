"""
We need some bulk func eventually, but:
    - https://stackoverflow.com/a/3663101/9420670

Like. now.
"""
import asyncio

from colorama import Fore
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.orm import Session, sessionmaker

from base_classes.db_monitor import ping_new_product
from db.base import MainDB
from db.tables import Product
from utils.custom_logger import Log
from utils.terminal import color_wrap

log = Log("[DB]")


class DB:
    # create db session
    main_session: Session = sessionmaker(bind=MainDB.base_db_engine, expire_on_commit=False)
    MainDB.init_tables()

    @staticmethod
    async def update_product(product: Product):
        """
        Will update product or make a new product.
        :param product:
        :return: None
        """

        def _update_product() -> tuple[str, dict]:
            resp, old_prod_json = None, None

            with DB.main_session.begin() as short_session:
                product_in_db: Product | None = \
                    short_session.query(Product) \
                        .filter(Product.pid == product.pid) \
                        .first()
                try:

                    if product_in_db:
                        old_prod_json = product_in_db.dump
                        if product_in_db.dump.get('updatedAt') == product.dump.get('updatedAt'):
                            # log.debug(
                            #     color_wrap(Fore.LIGHTMAGENTA_EX + f'No need to update {product.pid} in db.')
                            # )
                            pass
                        else:
                            product_in_db.update_from_dict(product.to_dict())
                            log.debug(color_wrap(Fore.LIGHTMAGENTA_EX + f'Updated {product.pid} in db.'))
                    else:
                        short_session.add(product)
                        resp = 'NEW'
                        log.debug(color_wrap(Fore.BLUE + f'Added {product.pid} to db.'))
                except InvalidRequestError:
                    log.exception('Error Adding/Updating Account.')
                    input('Waiting')

                return resp, old_prod_json

        resp, old_prod_json = await asyncio.get_event_loop().run_in_executor(None, _update_product)
        # ping for new product
        if resp == 'NEW':
            await ping_new_product(product.dump)

    @staticmethod
    async def return_product(pid: int) -> Product | None:
        """
        :param pid:
        :return: product or None
        """

        def _return_product():
            with DB.main_session.begin() as short_session:
                current_prod_info: Product | None = \
                    short_session.query(Product) \
                        .filter(Product.pid == pid) \
                        .first()

                if not current_prod_info:
                    log.debug(color_wrap(Fore.RED + f'Did not find {pid} in db.'))
                    return
                log.debug(color_wrap(Fore.GREEN + f'Found {pid} in db.'))
                return current_prod_info

        return await asyncio.get_event_loop().run_in_executor(None, _return_product)


if __name__ == "__main__":
    from random import randint
    prod = asyncio.run(DB.return_product(5918925))
    asyncio.run(
        DB.update_product(
            product=Product(
                pid=randint(10_000, 20_000),
                dump=prod.dump
            )
        )
    )

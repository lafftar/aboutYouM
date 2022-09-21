"""
We need some bulk func eventually, but:
    - https://stackoverflow.com/a/3663101/9420670

Like. now.
"""
import asyncio
from asyncio import sleep

import sqlalchemy
from colorama import Fore
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.orm import Session, sessionmaker

from base_pinger.pinger import ping_new_product
from base_pinger.updated_product import ping_updated_product
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
    async def return_pids() -> list[int]:
        def _return_pids():
            with DB.main_session.begin() as short_session:
                product_pids: list[tuple[int]] = short_session.query(Product.pid).all()
                return [pid[0] for pid in product_pids]

        return await asyncio.get_event_loop().run_in_executor(None, _return_pids)

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

                if product_in_db:
                    old_prod_json = product_in_db.dump

                    if product_in_db.dump == product.dump:
                        # log.debug(
                        #     color_wrap(Fore.LIGHTMAGENTA_EX + f'No need to update {product.pid} in db.')
                        # )
                        pass
                    else:
                        # @todo turn this back on pls
                        product_in_db.update_from_dict(product.to_dict())
                        resp = 'UPDATED'
                        log.debug(color_wrap(Fore.LIGHTMAGENTA_EX + f'Updated {product.pid} in db.'))

                        # @todo
                        # add create task to add what changes were noticed to the `changes` key in the `product_changes`
                        # table. hopefully just call .diff() with the struct.Product dataclass
                else:
                    short_session.add(product)
                    resp = 'NEW'
                    log.debug(color_wrap(Fore.BLUE + f'Added {product.pid} to db.'))

                return resp, old_prod_json

        _resp, _old_prod_json = None, None
        for _ in range(5):
            try:
                _resp, _old_prod_json = await asyncio.get_event_loop().run_in_executor(None, _update_product)
                break
            except sqlalchemy.exc.OperationalError:
                log.error(f'Database locked when trying to update {product.pid}')
                await sleep(3)

        # only 2 situations we need to care about
        if _resp == 'NEW':
            await ping_new_product(product.dump)
        if _resp == 'UPDATED':
            await ping_updated_product(old_product_json=_old_prod_json, new_product_json=product.dump)

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


    def test_update_product():
        pid = 8610865
        prod = asyncio.run(DB.return_product(pid))
        prod.dump['variants'][0]['stock']['quantity'] = randint(1, 10)
        asyncio.run(
            DB.update_product(
                product=Product(
                    pid=pid,
                    dump=prod.dump
                )
            )
        )


    def test_return_product():
        # return a pid from the db, pretty print it with our struct.Product class
        from utils import structs
        print(structs.Product.from_json(asyncio.run(DB.return_product(8610865)).dump))

    test_update_product()

import asyncio
from asyncio import sleep, Semaphore
from json import dumps, JSONDecodeError
from pprint import pprint
from random import randint, choice
from time import time

import httpx

from base_classes.req_sender import ReqSender
from db.db_fx import DB
from db.tables import Product
from utils.custom_logger import Log
from utils.root import get_project_root
from utils.tools import print_req_info


class Test:
    """
    This will contain the test suite that covers ranges we care about.

    """
    log: Log = Log('[TEST]', do_update_title=False)

    async def test(self):
        async with DBCrawler() as db_crawler:
            db_crawler: DBCrawler
            await db_crawler.run()  # this will raise if not good.
        self.log.info('[TEST GOOD]')


# this will inherit from the abstract classes that make all this possible (shouts to our silent heros 💗💙💚)
class DBCrawler(Test, ReqSender):
    """
    There should really only ever be 1 obj of this class per shopId.
    """
    sem: Semaphore = Semaphore(1)  # general use semaphore

    def __init__(self):
        super().__init__()

        self.current_page_num: int = 0
        self.amt_of_prods_per_page: int = 1000
        self.shop_id: int = 692
        self.log: Log = Log(f'[DB CRAWLER] [{self.shop_id}]', do_update_title=False)
        self.pids: list = []

    async def refresh_pids(self):
        """
        this fetches all the pids from the db, and adds them to the class pids.
            pids should be updated by `pid_grabber`
        :return:
        """
        pids = await DB.return_pids()
        with open(f'{get_project_root()}/program_data/pids.txt') as file:
            _pids = [int(line.strip()) for line in file.readlines()]
        self.pids = [str(item) for item in set(pids + _pids)]
        self.log.fmt = f'[DB CRAWLER] [{self.shop_id}] [{len(self.pids)}]'.rjust(35)

    @staticmethod
    async def parse_products(entities: dict) -> list[Product]:
        """
        entities: json of product page
        """
        products: list[Product] = []

        for item in entities:
            item: dict

            pid: int = item.get('id')
            _dump: dict = item
            product: Product = Product(pid=pid, dump=_dump)
            products.append(product)
            asyncio.create_task(DB.update_product(product=product))

        return products

    async def fetch_150_pids(self, pids: list[str]):
        """
        This has the byproduct of updating/adding the product to our db.
        """
        params = {
            "ids": ','.join(pids),
            "with": "attributes:key(name|brand|colorDetail|vendorSize),variants,price,"
                    "variants.attributes:key(vendorSize),priceRange",
            "page": "1",
            "perPage": "1000",
            "forceNonLegacySuffix": "true",
            "shopId": f"{self.shop_id}"
        }

        # send the req
        req = httpx.Request(
            method="GET",
            url="https://api-cloud.aboutyou.de/v1/products",
            params=params,
            headers={
                'HOST': 'api-cloud.aboutyou.de'
            }
        )

        resp = await self.send_req(req=req, client=httpx.AsyncClient(proxies=await self.good_proxy))

        # error handle
        if not resp or resp.status_code == 429:
            self.log.error('429.')
            return

        try:
            _json = resp.json()
        except JSONDecodeError:
            print_req_info(resp, True, False)
            return

        await self.parse_products(entities=_json.get('entities'))

        return

    async def fetch_all_pids(self):
        max_pids = 150  # literally cant send more than 150 because of 414 @todo - check if it takes json
        await asyncio.gather(*
                             [
                                 self.fetch_150_pids(pids=pids)
                                 for pids in [self.pids[x:x + max_pids] for x in range(0, len(self.pids), max_pids)]
                             ]
                             )

    async def run(self):
        """
        This launches flows that check the about you db on intervals we choose, categories we select.
        :return:
        20345 - cat id
        692 - shop id
        """
        self.log.info('STARTED PID MONITOR.')
        while True:
            try:
                await self.__aenter__()

                while True:
                    with Timer() as timer:
                        await self.refresh_pids()
                        self.current_page_num = 0
                        await self.fetch_all_pids()
                    self.log.info('\n\n\n'
                                  f'{"[CHECKED]".rjust(35)}: {len(self.pids)}\n'
                                  f'{"[TOOK]".rjust(35)}: {timer.time_took}\n\n')
                    await sleep(3)
                    self.log.info(f'NEXT CYCLE.')
            except Exception:
                self.log.exception('HUH!')
            finally:
                await self.__aexit__(None, None, None)


class Timer:
    def __init__(self):
        self.t1 = 0
        self.time_took = 0

    def __enter__(self):
        self.t1 = time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.time_took = f'{time() - self.t1:.2f}s'


# Testing
if __name__ == "__main__":
    asyncio.run(DBCrawler().run())
    # import cProfile
    # cProfile.run("asyncio.run(DBCrawler().run())")

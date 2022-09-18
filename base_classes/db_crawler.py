import asyncio
from asyncio import sleep, Semaphore
from json import dumps, JSONDecodeError
from pprint import pprint
from random import randint, choice

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
        self.log.fmt = f'[DB CRAWLER] [{self.shop_id}] [{len(self.pids)}]'

    async def parse_products(self, entities: dict) -> list[Product]:
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

    async def fetch_product(self):
        """
        This has the byproduct of updating/adding the product to our db.
        """
        async with self.sem:
            this_task_page_num = self.current_page_num
            self.current_page_num += 1
            self.log.debug(f'Fetching page #{this_task_page_num}.')

        max_pids = 150  # literally cant send more than 150 because of 414 @todo - check if it takes json
        for pids in [self.pids[x:x+max_pids] for x in range(0, len(self.pids), max_pids)]:
            params = {
                "ids": ','.join(pids),
                "with": "attributes:key(name|brand|colorDetail|vendorSize),variants,price,"
                        "variants.attributes:key(vendorSize),priceRange",
                "page": f"{self.current_page_num}",
                "perPage": f"{self.amt_of_prods_per_page}",
                "forceNonLegacySuffix": "true",
                "shopId": f"{self.shop_id}"
            }

            # grab the first page
            req = httpx.Request(
                method="GET",
                url="https://api-cloud.aboutyou.de/v1/products",
                params=params,
                headers={
                    'HOST': 'api-cloud.aboutyou.de'
                }
            )

            resp = await self.send_req(req=req, client=httpx.AsyncClient(proxies=choice(
                'http://thescrapingbook:zv1WIZKndCvriyM6@proxy.packetstream.io:31112'
            )))

            if not resp or resp.status_code == 429:
                continue

            try:
                _json = resp.json()
            except JSONDecodeError:
                print_req_info(resp, True, False)
                return

            await self.parse_products(entities=_json.get('entities'))

        return

    async def fetch_all_products(self):
        # eventually launch resilient tasks in the same event loop, hopefully pull and update all product in like,
        # a second.
        # @todo

        await self.fetch_product()

        # print task info
        _pagination_dict: dict = self.resp.json().get('pagination')
        pagination = ''.join(
            [
                f'\t\t{key.ljust(15)}: {val}\n'
                for key, val in _pagination_dict.items()
            ]
        )
        self.log.debug('\n\n'
                       '\t[[ PAGINATION ]]\n\n'
                       f'{pagination}\n'
                       f'\n'
                       f'\t[[ FETCHING {_pagination_dict.get("last")} PAGES. '
                       f'FOUND {_pagination_dict.get("total")} PRODUCTS ]]\n'
                       f'\n')

        # no horror while loops 😭
        await asyncio.gather(*[self.fetch_product() for _ in range(_pagination_dict.get('last') + 1)])
        await sleep(0.3)
        print()

    async def run(self):
        """
        This launches flows that check the about you db on intervals we choose, categories we select.
        :return:
        20345 - cat id
        692 - shop id
        """
        while True:
            try:
                await self.__aenter__()

                while True:
                    await self.refresh_pids()
                    self.current_page_num = 0
                    await self.fetch_all_products()
                    await sleep(10)
            except Exception:
                self.log.exception('HUH!')
            finally:
                await self.__aexit__(None, None, None)


# Testing
if __name__ == "__main__":
    asyncio.run(DBCrawler().run())
    # import cProfile
    # cProfile.run("asyncio.run(DBCrawler().run())")
import asyncio
from asyncio import sleep, Semaphore
from json import JSONDecodeError
from random import shuffle
from statistics import mean

import httpx
from colorama import Fore

from base_classes.req_sender import ReqSender
from db.db_fx import DB
from db.tables import Product
from utils.custom_logger import Log
from utils.root import get_project_root
from utils.terminal import color_wrap
from utils.tools import print_req_info, Timer


class Test:
    """
    This will contain the test suite that covers ranges we care about.

    """
    log: Log = Log('[TEST]', do_update_title=False)

    async def test(self):
        async with PIDMonitor() as db_crawler:
            db_crawler: PIDMonitor
            await db_crawler.run()  # this will raise if not good.
        self.log.info('[TEST GOOD]')


# this will inherit from the abstract classes that make all this possible (shouts to our silent heros 💗💙💚)
class PIDMonitor(Test, ReqSender):
    """
    There should really only ever be 1 obj of this class per shopId.
    """
    sem: Semaphore = Semaphore(1)  # general use semaphore

    def __init__(self):
        super().__init__()

        self.current_page_num: int = 0
        self.amt_of_prods_per_page: int = 1000
        self.shop_id: int = 692
        self.log: Log = Log(f'[PID MONITOR] [{self.shop_id}]', do_update_title=False)
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
        shuffle(self.pids)
        self.log.fmt = f'[PID MONITOR] [{self.shop_id}] [{len(self.pids)}]'.rjust(35)
        self.log.debug(f'{color_wrap("Refreshed PIDs")}')

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

    async def fetch_150_pids(self, pids: list[str]) -> tuple | None:
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
            # "shopId": f"{self.shop_id}",
            # "cacheBreaker": f"{randint(0, 10_000)}"
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
        async with httpx.AsyncClient(proxies=await self.good_proxy) as c:
            resp = await self.send_req(req=req, client=c)

        # error handle
        if not resp or resp.status_code == 429:
            self.log.error('429.')
            return

        try:
            _json = resp.json()
        except JSONDecodeError:
            print_req_info(resp, True, False)
            return

        status = str(resp.status_code), \
                     str(round(len(resp.content) / 1024)),\
                     resp.headers.get("Age") or "0", \
                     resp.headers.get("Cf-Cache-Status")
        msg = color_wrap(', '.join(status), fore_color=Fore.LIGHTBLUE_EX)
        self.log.debug(msg)
        await self.parse_products(entities=_json.get('entities'))

        return status

    async def fetch_all_pids(self) -> tuple:
        max_pids = 150  # literally cant send more than 150 because of 414 @todo - check if it takes json
        tasks = [
                                 self.fetch_150_pids(pids=pids)
                                 for pids in [self.pids[x:x + max_pids] for x in range(0, len(self.pids), max_pids)]
                             ]
        statii = await asyncio.gather(*tasks)

        hits = 0
        cache_ages = []
        for status in statii:
            if not status:
                continue
            status_code, _, cache_age, cache_status = status
            cache_ages.append(int(cache_age))
            if cache_status == "HIT":
                hits += 1

        if hits:
            hits = (hits * 100) / len(tasks)

        avg_cache_age = 0
        if cache_ages:
            avg_cache_age = mean(cache_ages)

        return hits, avg_cache_age, len(tasks)

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
                        hits, avg_cache_age, task_num = await self.fetch_all_pids()
                    self.log.info('\n\n\n'
                                  f'{"[PIDS]".rjust(35)}: {len(self.pids)}\n'
                                  f'{"[TASKS]".rjust(35)}: {task_num}\n'
                                  f'{"[AVG CACHE AGE]".rjust(35)}: {avg_cache_age:.2f}s\n'
                                  f'{"[CACHE HIT %]".rjust(35)}: {hits:.2f}%\n'
                                  f'{"[TOOK]".rjust(35)}: {timer.time_took}\n\n')
                    await sleep(10)
                    self.log.info(f'NEXT CYCLE.')
            except Exception:
                self.log.exception('HUH!')
            finally:
                await self.__aexit__(None, None, None)


# Testing
if __name__ == "__main__":
    asyncio.run(PIDMonitor().run())
    # import cProfile
    # cProfile.run("asyncio.run(DBCrawler().run())")

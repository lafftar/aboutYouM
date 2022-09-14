import asyncio
from asyncio import sleep, Semaphore
from json import dumps
from random import randint

import httpx

from base.req_sender import ReqSender
from db.db_fx import DB
from db.tables import Product
from utils.custom_logger import Log
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
            if randint(1, 3) % 2 == 0:
                self.log.debug(f'Fetching page #{this_task_page_num}.')

        params = {
            "with": "attributes:key(brand|brandLogo|brandAlignment|captchaRequired|name|quantityPerPack|plusSize|"
                    "colorDetail|sponsorBadge|sponsoredType|maternityNursing|exclusive|genderage|"
                    "specialSizesProduct|materialStyle|sustainabilityIcons|assortmentType|dROPS|"
                    "brandCooperationBadge|secondHandType),advancedAttributes:"
                    "key(materialCompositionTextile|siblings),variants,variants.attributes:"
                    "key(shopSize|categoryShopFilterSizes|cup|cupsize|vendorSize|length|dimension3|sizeType|sort),"
                    "variants.lowestPriorPrice,images.attributes:legacy(false):"
                    "key(imageNextDetailLevel|imageBackground|imageFocus|imageGender|imageType|imageView),"
                    "priceRange,lowestPriorPrice",
            "filters[category]": "20202",
            "sortDir": "asc",
            "sortScore": "category_scores",
            "sortChannel": "web_default",
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

        await self.send_req(req=req)

        await self.parse_products(entities=self.resp.json().get('entities'))

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
        for iter_num in range(_pagination_dict.get('last') + 1):
            await self.fetch_product()

    async def run(self):
        """
        This launches flows that check the about you db on intervals we choose, categories we select.
        :return:
        20345 - cat id
        692 - shop id
        """
        try:
            await self.__aenter__()

            while True:
                self.current_page_num = 0
                await self.fetch_all_products()
                await sleep(1)

                self.log.info('\n\n\n\nPUT A CRAWL SUMMARY HERE\n\n')
                await sleep(60)
        except Exception:
            self.log.exception('HUH!')
        finally:
            await self.__aexit__(None, None, None)


# Testing
if __name__ == "__main__":
    asyncio.run(DBCrawler().run())

import asyncio
from asyncio import sleep

import httpx

from base.req_sender import ReqSender
from utils.custom_logger import Log
from utils.structs import Product


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
    log: Log = Log('[DB CRAWLER]', do_update_title=False)

    def __init__(self):
        super().__init__()

    async def parse_products(self, entities: dict) -> list[Product]:
        """
        entities: json of product page
        """

    async def fetch_product(self):
        pass

    async def fetch_all_products(self):
        pass

    async def run(self):
        """
        This launches flows that check the about you db on intervals we choose, categories we select.
        :return:
        20345 - cat id
        692 - shop id
        """
        self.req = httpx.Request(
            method="GET",
            url="https://api-cloud.aboutyou.de/v1/products"
                "?with=attributes:key(brand|brandLogo|brandAlignment|captchaRequired|name|quantityPerPack|plusSize|colorDetail|sponsorBadge|sponsoredType|maternityNursing|exclusive|genderage|specialSizesProduct|materialStyle|sustainabilityIcons|assortmentType|dROPS|brandCooperationBadge|secondHandType),advancedAttributes:key(materialCompositionTextile|siblings),variants,variants.attributes:key(shopSize|categoryShopFilterSizes|cup|cupsize|vendorSize|length|dimension3|sizeType|sort),variants.lowestPriorPrice,images.attributes:legacy(false):key(imageNextDetailLevel|imageBackground|imageFocus|imageGender|imageType|imageView),priceRange,lowestPriorPrice"
                "&filters[category]=20202"
                "&sortDir=asc"
                "&sortScore=category_scores"
                "&sortChannel=web_default"
                "&perPage=500"
                "&forceNonLegacySuffix=true"
                "&shopId=692",
            headers={
                'HOST': 'api-cloud.aboutyou.de'
            }
        )
        try:
            await self.__aenter__()
            await self.send_req()
            await sleep(0.01)
            self.log.debug('DB Crawler is G2G! Get to work!')
        except Exception:
            self.log.exception('HUH!')
        finally:
            await self.__aexit__(None, None, None)


# Testing
if __name__ == "__main__":
    asyncio.run(DBCrawler().run())

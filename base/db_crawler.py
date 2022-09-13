import asyncio
from asyncio import sleep

import httpx

from base.req_sender import ReqSender
from utils.custom_logger import Log


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

    async def run(self):
        """
        This launches flows that check the about you db on intervals we choose, categories we select.
        :return:
        """
        self.req = httpx.Request(
            method="GET",
            url="https://api-cloud.aboutyou.de/v1/filters",
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

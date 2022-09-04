import asyncio
from asyncio import sleep
from random import uniform

import httpx

from utils.custom_logger import Log
from utils.structs import GlobalNetworkState
from utils.tools import print_req_info


class Test:
    """
    This will contain the test suite that covers ranges we care about.

    """
    log: Log = Log('[TEST]', do_update_title=False)

    async def test(self):
        self.log.info('[TEST GOOD]')


# @todo
"""
- Proxy (3proxy or python native), use solely to measure data sent through network. 
"""


# Central Request Handler. All requests should go through this.
class ReqSender(Test):
    log: Log = Log('[REQ SENDER]', do_update_title=False)
    network_state: GlobalNetworkState = GlobalNetworkState()

    def __init__(self):
        self.client: httpx.AsyncClient | None = None
        self.req: httpx.Request | None = None
        self.resp: httpx.Response | None = None

    # these should be the only way this class is used. fail gracefully otherwise.
    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            verify=False
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    @staticmethod
    async def send_httpx_req(c: httpx.AsyncClient, req: httpx.Request, num_tries: int = 5) -> \
            httpx.Response | None:
        """
        :param req:
        :param c:
        :param num_tries:

        :return:
        """
        for _ in range(num_tries):
            try:
                item = await c.send(req)
                return item
            except (
                    httpx.ConnectTimeout, httpx.ProxyError, httpx.ConnectError,
                    httpx.ReadError, httpx.ReadTimeout, httpx.WriteTimeout, httpx.RemoteProtocolError,
            ) as e:
                # @todo
                """
                eventually have an error handler, maybe all static methods, take a httpx resp and log to -->
                    DB|Discord|Daily CSV as needed.
                """
                ReqSender.log.error(e)
                await sleep(uniform(0.5, 2.2))
        ReqSender.log.error(f'Tried to send request with METHOD [{req.method}] and URL [{req.url[:15]}...] '
                            f'{num_tries} times.')

    async def handle_antibot(self) -> list:
        """
        Handles all anti bot it detects on page (stores all interesting tidbits in a struct for logging.)
        :return: list of threats identified, and steps taken, maybe a list of some struct down the line
        """
        pass

    async def send_req(self):
        self.resp = await self.send_httpx_req(c=self.client, req=self.req)
        print_req_info(self.resp, True, True)

        if not self.resp:
            raise Exception("No Response Received.")

        anti_bot_tests: list = await self.handle_antibot()
        # if ~any action needed~ -> raise.

    async def run(self):
        self.req = httpx.Request(
            method="GET",
            url="http://api.ipify.org"
        )
        try:
            await self.__aenter__()
            await self.send_req()
        except Exception:
            self.log.exception('HUH!')
        finally:
            await self.__aexit__(None, None, None)


# Testing
if __name__ == "__main__":
    asyncio.run(ReqSender().run())

import asyncio
from asyncio import sleep
from random import uniform, choice

import aiohttp
import httpx
from aiohttp import BaseConnector, ClientTimeout, ClientProxyConnectionError

from utils.custom_logger import Log
from utils.root import get_project_root
from utils.structs import GlobalNetworkState, Proxy
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
    timeout: int = 2.5
    log: Log = Log('[REQ SENDER]', do_update_title=False)
    network_state: GlobalNetworkState = GlobalNetworkState()

    with open(f'{get_project_root()}/program_data/proxies.txt') as file:
        dcs = [Proxy(line.strip()) for line in file.readlines()]

    def __init__(self):
        self.client: httpx.AsyncClient | None = None
        self.client_: aiohttp.ClientSession | None = None
        self.req: httpx.Request | None = None
        self.resp: httpx.Response | None = None

    # these should be the only way this class is used. fail gracefully otherwise.
    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            verify=False,
            timeout=self.timeout
        )

        # using this to do odd things like test proxies. encountered unreliable dcs'
        self.client_ = aiohttp.ClientSession(
            trust_env=True,
            timeout=ClientTimeout(self.timeout)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
        await self.client_.close()

    @property
    async def good_proxy(self) -> str:
        for _ in range(10):
            proxy = str(choice(self.dcs))
            try:
                await self.client_.get('http://api.ipify.org', proxy=proxy)
                return proxy
            except (ClientProxyConnectionError, TimeoutError):
                continue
            except Exception as e:
                if 'TimeoutError' in repr(e):
                    continue
                self.log.error(f'Error while checking proxy - {repr(e)}')

        raise Exception("Could not find good proxy after 10 tries!")

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
        ReqSender.log.error(f'Tried to send request with METHOD [{req.method}] and URL [{str(req.url)[:15]}...] '
                            f'{num_tries} times.')

    async def handle_antibot(self) -> list:
        """
        Handles all anti bot it detects on page (stores all interesting tidbits in a struct for logging.)
        :return: list of threats identified, and steps taken, maybe a list of some struct down the line
        """
        pass

    async def send_req(self, req: httpx.Request = None, client: httpx.AsyncClient = None) -> httpx.Response:
        if not client:
            client = self.client  # to allow for callers to provide their own proxies n stuff

        if req:
            resp = await self.send_httpx_req(c=client, req=req)
        else:
            resp = await self.send_httpx_req(c=client, req=self.req)

        if not resp:
            raise Exception("No Response Received.")

        self.resp = resp
        anti_bot_tests: list = await self.handle_antibot()
        # if ~any action needed~ -> raise.
        return resp

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

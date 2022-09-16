import asyncio

from base_classes.db_crawler import DBCrawler
from base_classes.req_sender import ReqSender
from utils.custom_logger import Log


# this will inherit from the abstract classes that make all this possible (shouts to our silent heros 💗💙💚)
from utils.structs import TaskNetworkState


class Test:
    """
    This will contain the test suite that covers ranges we care about.

    """
    log: Log = Log('[TEST]', do_update_title=False)

    async def test(self):
        self.log.info('[TEST GOOD]')


class Base(DBCrawler, ReqSender, Test):
    log: Log = Log('[BASE]', do_update_title=False)

    # @todo - not sure if this should be per class or per object/task yet.
    task_network_state: TaskNetworkState = TaskNetworkState()

    def __init__(self):
        super().__init__()

    async def run(self):
        pass


# # Testing
if __name__ == "__main__":
    asyncio.run(Base().test())

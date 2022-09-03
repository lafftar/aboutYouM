import asyncio

from utils.custom_logger import Log


# this will inherit from the abstract classes that make all this possible (shouts to our silent heros 💗💙💚)
class RestockMonitor:
    log: Log = Log('[RESTOCK MONITOR]', do_update_title=False)

    @staticmethod
    async def test():
        RestockMonitor.log.info('[TEST GOOD]')


# # Testing
if __name__ == "__main__":
    asyncio.run(RestockMonitor.test())
    
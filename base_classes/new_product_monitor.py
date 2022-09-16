import asyncio

from base_classes._base import Base
from utils.custom_logger import Log


# this will make changes to state (DB/DBOT Triggers), if a product that has never been encountered, is encountered.
class NewProductMonitor(Base):
    log: Log = Log('[NEW PRODUCT MONITOR]', do_update_title=False)

    @staticmethod
    async def ping_new_product(product_json: dict):
        pass


# # Testing
if __name__ == "__main__":
    asyncio.run(NewProductMonitor().ping_new_product(
        Product(

        )
    ))
    
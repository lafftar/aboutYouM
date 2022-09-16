import asyncio

from db.db_fx import DB
from db.tables import Product
from utils.custom_logger import Log

log: Log = Log('[DB TEST]')

async def test_db_fx():
    # funcs
    pid: int = 1337133713371337
    msg: str = "Nothing to see here, just testing the db!"
    await DB.update_product(
        product=Product(
            pid=pid,
            dump={
                "message": msg
            }
        )
    )
    product: Product = await DB.return_product(pid)

    # assertions
    assert isinstance(product, Product)
    assert product.pid == pid
    assert product.dump.get('message') == msg

    log.info('DB Tested! No Problems!')


if __name__ == "__main__":
    asyncio.run(test_db_fx())

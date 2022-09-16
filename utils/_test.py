import asyncio

from db.db_fx import DB
from utils.structs import Product


async def test_structs():
    row = await DB.return_product(5914490)
    product = Product.from_json(
        row.dump
    )

    print(product)


async def test():
    await asyncio.gather(*[
        test_structs(),
    ])


if __name__ == "__main__":
    asyncio.run(test())


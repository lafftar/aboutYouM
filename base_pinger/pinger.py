"""
This will somehow be called by triggers on the db, before inserts, comparing data and pinging if necessary.
For now, we do this in the db_fx


- New Product Monitor

@todo
- Restock Monitor
- Price Monitor
"""

from base_pinger._base import _send_webhook, log
from utils.structs import Product
from utils.terminal import color_wrap


# i'll move this when `pinger.py` becomes big again.
async def ping_new_product(product_json: dict):
    product = Product.from_json(product_json)

    title = 'New Product!'
    if product.is_sold_out:
        title += ' (Sold Out)'

    await _send_webhook(product, title)

    log.debug(f'New Product -  {color_wrap(product.title)}')


if __name__ == "__main__":
    pass

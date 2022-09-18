"""
This runs every 30 or so minutes
 - Checks the 1M+ PIDs in abyou db, looks for anything sold out,
    checks if any of our terms are in there, adds them to the db if they are.
"""
import asyncio
from asyncio import Semaphore, sleep
from json import JSONDecodeError
from random import choice

import httpx

from base_classes.req_sender import ReqSender
from db.db_fx import DB
from utils.custom_logger import Log
from utils import structs
from db import tables
from utils.tools import print_req_info

log: Log = Log('[PID GRABBER]', do_update_title=False)
sem: Semaphore = Semaphore(25)  # trying not to get dc's banned ✨✨✨✨


def return_req(page_no: int):
    return httpx.Request(
        method='GET',
        url='https://api-cloud.aboutyou.de/v1/products',
        params={
            "with": "attributes:key(name|brand|colorDetail|vendorSize),variants,price,"
                    "variants.attributes:key(vendorSize),priceRange",
            "page": page_no,
            "perPage": "1000",
            "forceNonLegacySuffix": "true",
            # "shopId": f"692",
            "includeSoldOut": "true"
        }
    )


async def fetch_page(page_no: int) -> tuple[httpx.Response, list[structs.Product]] | None:
    async with sem:
        async with httpx.AsyncClient(proxies='http://thescrapingbook:zv1WIZKndCvriyM6@proxy.packetstream.io:31112') \
                as c:
            resp = await c.send(return_req(page_no))

    products: list[structs.Product] = []

    try:
        _json = resp.json()
    except JSONDecodeError:
        print_req_info(resp, True, False)
        return

    for item in _json.get('entities'):
        item: dict

        _dump: dict = item
        try:
            product: structs.Product = structs.Product.from_json(_dump)
        except AttributeError:
            continue
        if product.is_active:
            continue
        if product.price < 25:
            continue
        if not any(_item in product.title.lower() for _item in
                   ('shoes', 'sneaker', 'yeezy', 'dunk ', 'new balance')
                   ):
            continue
        products.append(product)
        print(product)
        product_row: tables.Product = tables.Product(pid=product.pid, dump=_dump)
        asyncio.create_task(DB.update_product(product=product_row))

    return resp, products


async def _run():
    resp, products = await fetch_page(0)

    # print task info
    _pagination_dict: dict = resp.json().get('pagination')
    pagination = ''.join(
        [
            f'\t\t{key.ljust(15)}: {val}\n'
            for key, val in _pagination_dict.items()
        ]
    )
    log.debug('\n\n'
              '\t[[ PAGINATION ]]\n\n'
              f'{pagination}\n'
              f'\n'
              f'\t[[ FETCHING {_pagination_dict.get("last")} PAGES. '
              f'FOUND {_pagination_dict.get("total")} PRODUCTS ]]\n'
              f'\n')

    await asyncio.gather(*[fetch_page(page_no) for page_no in range(_pagination_dict.get('last') + 1)])


async def run():
    while True:
        try:
            await _run()
        except Exception:
            log.exception('HUH')

        print()
        log.info('Sleeping for 1 hour!! I just scraped like a million PIDs!')
        await sleep(3600)


if __name__ == "__main__":
    asyncio.run(run())

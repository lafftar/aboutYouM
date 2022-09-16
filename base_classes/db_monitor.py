"""
This will somehow be called by triggers on the db, before inserts, comparing data and pinging if necessary.
For now, we do this in the db_fx


- New Product Monitor

@todo
- Restock Monitor
- Price Monitor
"""
import asyncio

from utils.structs import Product
from utils.webhook import send_webhook
from discord import Colour


async def ping_new_product(product_json: dict):
    product = Product.from_json(product_json)

    webhook_urls = [
        'https://discord.com/api/webhooks/1020054473076375633/'
        'sec7Y3MuSicDZnwJicTTbvffmu1nLS6ywU4dkoop7_NXlts8IMJa8-d_egDNjpBEOFKF'
    ]

    # @todo - this is only temporary!
    for text in ('sneaker', 'shoe', 'nike', 'travis', 'adidas', 'puma', 'dunk'):
        if text in product.title.lower():
            webhook_urls.append(
                'https://discord.com/api/webhooks/1019663978621837402/'
                'QsbnlzUJVDLT7VJgvvz7w-f_y88RVeWjbV4WbHfUk4L95RPiYdzLXicDcre37cSDugAe'
            )
            break

    embed = product.to_embed()

    embed.title = 'New Product!'
    if product.is_sold_out:
        embed.title += ' (Sold Out)'

    embed.url = product.url
    embed.color = Colour.teal()

    for webhook_url in webhook_urls:
        await send_webhook(embed=embed,
                           webhook_url=webhook_url,
                           title='Product Test',
                           color=Colour.teal())

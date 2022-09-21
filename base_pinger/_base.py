import asyncio

from discord import Colour

from utils.custom_logger import Log
from utils.structs import Product
from utils.webhook import send_webhook


BASE_DISCORD_WEBHOOKS = [
    # mine
    'https://discord.com/api/webhooks/1020054473076375633/'
    'sec7Y3MuSicDZnwJicTTbvffmu1nLS6ywU4dkoop7_NXlts8IMJa8-d_egDNjpBEOFKF',
    # server
    'https://discord.com/api/webhooks/1019663978621837402/'
    'QsbnlzUJVDLT7VJgvvz7w-f_y88RVeWjbV4WbHfUk4L95RPiYdzLXicDcre37cSDugAe'
]
log: Log = Log('[PINGER]', do_update_title=False)


def pretty(title: str, msg: Product | str, log_):
    """

    :param title:
    :param msg:
    :param log_: this is the function from `utils.custom_logger.Log`, like `log.error()`
    :return:
    """
    sep = '#' * 50
    log_(f'\n\n[{title}]\n{msg}\n[{sep}]\n')


async def _send_webhook(product: Product, title: str, description: str = None):
    embed = product.to_embed()

    embed.title = title

    embed.url = product.url
    embed.description = description
    embed.color = Colour.blurple()

    await asyncio.gather(*
                         (send_webhook(embed=embed, webhook_url=webhook_url) for webhook_url in BASE_DISCORD_WEBHOOKS)
                         )

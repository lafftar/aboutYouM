import asyncio
import aiohttp
from asyncio import sleep
from discord import Colour, Embed, Webhook, File
from discord.abc import MISSING

from utils.custom_logger import logger


async def send_webhook(
        file: File = MISSING,
        content: str = '',
        embed_dict: dict = None,
        embed: Embed = None, title: str = '',
        webhook_url: str = None,
        color: Colour = None,
        title_link='https://discord.com'
):

    # ez defaults
    if not color:
        color = Colour.dark_red()
    if not webhook_url:
        webhook_url = 'https://discord.com/api/webhooks/927893447808008273' \
                      '/UlFfNapvHqzB2z4D_D_RPXgXRmRufwOcKTO3zZ6UaI8T-_mPQQx4UbaaIy6xTgIN_-eY'

    if not embed and embed_dict:
        # create embed
        embed = Embed(title=title, color=color, url=title_link)
        embed.set_footer(text='WINX4 Bots - winwinwinwin#0001',
                         icon_url='https://images6.alphacoders.com/909/thumb-1920-909641.png')

        for key, value in embed_dict.items():
            embed.add_field(name=f'{key}', value=f'{value}', inline=False)

    for _ in range(3):
        try:
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as webhook_client:
                webhook = Webhook.from_url(
                    url=webhook_url,
                    session=webhook_client)
                await webhook.send(username='aboutYouM',
                                   avatar_url=
                                   'https://i.pinimg.com/originals/2f/08/ab/2f08ab311cb92ed2cfafc691b12a8ce2.jpg',
                                   embed=embed,
                                   content=content,
                                   file=file
                                   )
            break
        except Exception:
            logger().exception('Webhook Failed')
            await sleep(2)


if __name__ == "__main__":
    async def run():
        # send webhook
        embed_dict = {
            'Email': f'||test||',
            'IP': f'||test.te.tes.tes||'
        }
        await send_webhook(embed_dict=embed_dict,
                           webhook_url='https://discord.com/api/webhooks/1020054473076375633/'
                                       'sec7Y3MuSicDZnwJicTTbvffmu1nLS6ywU4dkoop7_NXlts8IMJa8-d_egDNjpBEOFKF',
                           title='Account Created',
                           color=Colour.teal())


    asyncio.run(run())

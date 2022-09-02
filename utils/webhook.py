import asyncio
from asyncio import sleep
import aiohttp
from discord import Colour, Embed, AsyncWebhookAdapter, Webhook

from utils.custom_logger import logger


async def send_webhook(embed_dict, title: str = '',  webhook_url: str = None, color: Colour = None,
                       title_link='https://discord.com'):
    if not color:
        color = Colour.dark_red()
    if not webhook_url:
        webhook_url = 'https://discord.com/api/webhooks/989659295421440081/' \
                      'NqQqUz4kA4LL_mW9FBnNZSAO_XlktmyKrPDmhtzUqsqCr-brcc0ExU_A3vm1Dlf56_Bu'

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
                    adapter=AsyncWebhookAdapter(webhook_client))
                await webhook.send(username='HCBP',
                                   avatar_url=
                                   'https://i.pinimg.com/originals/2f/08/ab/2f08ab311cb92ed2cfafc691b12a8ce2.jpg',
                                   embed=embed,
                                   )
            break
        except Exception:
            logger().exception('Webhook Failed')
            await sleep(2)


if __name__ == "__main__":
    import aiohttp

    async def run():
        client = aiohttp.ClientSession()
        try:
            # send webhook
            embed_dict = {
                'Email': f'||test||',
                'IP': f'||test.te.tes.tes||'
            }
            await send_webhook(embed_dict=embed_dict,
                               webhook_client=client,
                               title='Account Created',
                               color=Colour.teal())
        finally:
            await client.close()


    asyncio.run(run())

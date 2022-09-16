import asyncio

from discord import Colour

from utils.webhook import send_webhook


async def handle_error(err: Exception, state: str = "```null```", embed_dict: dict = None):
    if not embed_dict:
        embed_dict = {
            "State": state,
            "Exception Message": f"```{repr(err)[-800:]}```"
        }

    asyncio.create_task(
        send_webhook(
            embed_dict=embed_dict,
            color=Colour.dark_red(),
            title='Exception!',
            webhook_url='https://discord.com/api/webhooks/927893447808008273/'
                        'UlFfNapvHqzB2z4D_D_RPXgXRmRufwOcKTO3zZ6UaI8T-_mPQQx4UbaaIy6xTgIN_-eY'
        )
    )
    return embed_dict

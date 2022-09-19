import asyncio

from discord import Colour

from utils.webhook import send_webhook


class PingException(Exception):
    """
    This just pings the exception to discord for now.
    """

    def __init__(self, message: str ="Exception!"):
        super().__init__(message)

    async def raise_(self):
        await ping(exception=self)
        return self


async def ping(exception: Exception):

    await send_webhook(
        embed_dict={
            "message": f'```{repr(exception)}```'
        },
        color=Colour.purple(),
        title='Exception from aboutYouMonitor!'
    )


if __name__ == "__main__":

    asyncio.run(PingException("Testing!").raise_())
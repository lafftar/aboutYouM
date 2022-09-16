"""
This will somehow be called by triggers on the db, before inserts, comparing data and pinging if necessary.
For now, we do this in the db_fx


- New Product Monitor

@todo
- Restock Monitor
- Price Monitor
"""
from copy import copy

from discord import Colour

from utils.custom_logger import Log
from utils.structs import Product
from utils.webhook import send_webhook


BASE_DISCORD_WEBHOOKS = [
        'https://discord.com/api/webhooks/1020054473076375633/'
        'sec7Y3MuSicDZnwJicTTbvffmu1nLS6ywU4dkoop7_NXlts8IMJa8-d_egDNjpBEOFKF'
    ]
log: Log = Log('[PINGER]', do_update_title=False)


async def ping_new_product(product_json: dict):
    product = Product.from_json(product_json)

    webhook_urls = copy(BASE_DISCORD_WEBHOOKS)

    # @todo - this is only temporary!
    for text in ('sneaker', 'shoe', 'dunk'):
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
                           webhook_url=webhook_url)

    log.debug(f'Sent new product webhook for {product.title}.')


async def ping_updated_product(old_product_json: dict, new_product_json: dict):
    """
    This checks the previous old prod json, compares it to the new prod json, sends a ping depending on if it's a
    - restock, based on if any previous variants where stock 0 and are now stock >0
    - price drop/reduction, if price range or sm changed
    :return:
    """
    changes = ['**CHANGES**']
    old_product = Product.from_json(old_product_json)
    new_product = Product.from_json(new_product_json)

    # new_product.variants.pop(43816440)
    # old_product.variants.pop(43816441)
    # print(old_product)
    # print(new_product)

    # detect new and removed variants
    new_variants = new_product.variants.keys() - old_product.variants.keys()
    if new_variants:
        changes.append(f'Variants added: {list(new_variants)}')

    removed_variants = old_product.variants.keys() - new_product.variants.keys()
    if removed_variants:
        changes.append(f'Variants removed: {list(removed_variants)}')

    # detect stock change
    for variant in new_product.variants.values():
        old_variant = old_product.variants.get(variant.vid, None)
        if not old_variant:  # a new variant was added, this is already handled
            continue
        if variant.stock != old_variant.stock:
            emoji = '⬆️⬆️⬆️'
            if old_variant.stock > variant.stock:
                emoji = '⬇️⬇️⬇️'
            changes.append(f'Stock changed: '
                           f'{variant.title} had {old_variant.stock} stock and now has {variant.stock}. {emoji}')

    # return if no changes happened that we care about, or if no new variants where added (0 stock -> w/e)
    if changes == ['**CHANGES**'] or \
            ('Variants added:' not in changes[1]):
        return

    # make description of changes
    description = ''
    for index, line in enumerate(changes):
        if index != 0:
            line = f'{index}) {line}'

        description += f'{line}\n'

    # send embed
    webhook_urls = copy(BASE_DISCORD_WEBHOOKS)

    # @todo - this is only temporary! turn into fx that just takes embed
    for text in ('sneaker', 'shoe', 'dunk'):
        if text in new_product.title.lower():
            webhook_urls.append(
                'https://discord.com/api/webhooks/1019663978621837402/'
                'QsbnlzUJVDLT7VJgvvz7w-f_y88RVeWjbV4WbHfUk4L95RPiYdzLXicDcre37cSDugAe'
            )
            break

    embed = new_product.to_embed()

    embed.title = 'Restock!'

    embed.url = new_product.url
    embed.description = description
    embed.color = Colour.blurple()

    for webhook_url in webhook_urls:
        await send_webhook(embed=embed,
                           webhook_url=webhook_url)

    log.debug(f'Sent restock webhook for {new_product.title}.')
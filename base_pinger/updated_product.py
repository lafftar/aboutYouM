from base_pinger._base import pretty, log, _send_webhook
from utils.structs import Product


async def ping_updated_product(old_product_json: dict, new_product_json: dict):
    """
    This checks the previous old msg json, compares it to the new msg json, sends a ping depending on if it's a
    - restock, based on if any previous variants where stock 0 and are now stock >0
    - price drop/reduction, if price range or sm changed
    :return:
    """
    changes = ['**CHANGES**']
    old_product = Product.from_json(old_product_json)
    new_product = Product.from_json(new_product_json)

    # return if no variants have stock
    if not any((variant.stock for variant in new_product.variants.values())):
        # pretty('NO VARIANTS HAVE STOCK', new_product, log.error)
        return

    # detect new and removed variants
    new_variants = new_product.variants.keys() - old_product.variants.keys()
    if new_variants:
        msg = f'Variants added: {list(new_variants)}'
        changes.append(msg)
        log.debug(msg)

    removed_variants = old_product.variants.keys() - new_product.variants.keys()
    if removed_variants:
        msg = f'Variants removed: {list(removed_variants)}'
        changes.append(msg)
        log.debug(msg)

    # detect stock change

    # get keys in both
    for current_variant in new_product.variants.values():

        old_variant = old_product.variants.get(current_variant.vid, None)
        if not old_variant:  # a new variant was added, this is already handled
            continue

        if current_variant.stock != old_variant.stock:
            emoji = '⬆️⬆️⬆️'
            if current_variant.stock < old_variant.stock:
                emoji = '⬇️⬇️⬇️'
            changes.append(f'Stock changed: '
                           f'{current_variant.title} had {old_variant.stock} stock and now has {current_variant.stock}.'
                           f' {emoji}')

    # return if no changes happened that we care about, or if no new variants where added (0 stock -> w/e)
    if changes == ['**CHANGES**']:
        # pretty('NO CHANGES FOR', new_product, log.error)
        return

    # make description of changes
    description = ''
    for index, line in enumerate(changes):
        if index != 0:
            line = f'{index}) {line}'

        description += f'{line}\n'

    # send embed

    await _send_webhook(new_product, 'CHANGES DETECTED!', description)

    pretty(f'CHANGES DETECTED {new_product.pid}', description.replace('**CHANGES**', '') + repr(new_product), log.info)

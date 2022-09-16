import re
from dataclasses import dataclass

from discord import Embed


@dataclass
class TaskNetworkState:
    pass


@dataclass
class GlobalNetworkState:
    """"""
    pass


@dataclass
class Variant:
    vid: int
    title: str
    stock: int
    atc_link: str = ''

    @staticmethod
    def from_json(list_of_dicts: list[dict]):
        """
        From the `variants` key of the main product dict.
        """
        variants = {}
        for _dict in list_of_dicts:
            vid = _dict.get('id')
            variants[vid] = Variant(
                vid=vid,
                title='SIZE ' + _dict.get('attributes').get('vendorSize').get('values').get('label'),
                stock=_dict.get('stock').get('quantity')
            )
        return variants


@dataclass
class Product:
    """
    Not to be confused with the `Product` in `db.tables` 😭
    """
    pid: int
    title: str
    url: str
    is_active: bool
    is_sold_out: bool
    image: str
    variants: dict[int, Variant]
    price: float
    currency: str

    def __repr__(self) -> str:
        return '\n' + '\n'.join((f'{key:30s}:  {val}' for key, val in vars(self).items()
                                 if not key.startswith('_'))) + '\n'

    @staticmethod
    def from_json(_dict: dict):
        _attrs: dict = _dict.get('attributes')
        return Product(
            pid=_dict.get('id'),
            title=f"{_attrs.get('brand').get('values').get('label')} "
                  f"{_attrs.get('name').get('values').get('label')} "
                  f"{_attrs.get('colorDetail').get('values')[0].get('label')}".title(),
            url=f"https://www.aboutyou.com/p"
                f"/{_attrs.get('brand').get('values').get('value').replace('_', '-')}/" +
                re.sub('[^a-zA-Z0-9 \n\.]', '',
                       f"{_attrs.get('name').get('values').get('label').replace(' ', '-').lower()}{_dict.get('id')}"),
            is_active=_dict.get('isActive'),
            is_sold_out=_dict.get('isSoldOut'),
            image='https://cdn.aboutstatic.com/file/' + _dict.get('images')[0].get('hash'),
            variants=Variant.from_json(list_of_dicts=_dict.get('variants')),
            price=_dict.get('priceRange').get('max').get('withTax') / 100,
            currency=_dict.get('priceRange').get('max').get('currencyCode')
        )

    def to_embed(self) -> Embed:
        embed = Embed()
        embed.set_thumbnail(url=self.image)

        # static embed fields
        embed.add_field(name='Name', inline=False, value=self.title)
        embed.add_field(name='PID', inline=True, value=self.pid)
        embed.add_field(name='Price', inline=True, value=f'{self.price} {self.currency}')
        embed.add_field(name='URL', inline=True, value=f'[**PRODUCT PAGE**]({self.url})')

        # spacer
        embed.add_field(name='\u200B', value='\u200B', inline=False)

        # dynamic embed fields
        # embed.add_field(name='[TITLE] [STOCK]', inline=False, value='[ATC LINK]')
        for variant in self.variants.values():
            if variant.stock == 0:
                continue
            embed.add_field(name=f'[{variant.title}] [{variant.stock}]', inline=True,
                            value=f'[ATC](https://google.com)')
        return embed

import re
from dataclasses import dataclass
from typing import ClassVar

from discord import Embed

from utils.custom_logger import Log


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
    variants: ClassVar

    def __repr__(self) -> str:
        return '[' + ''.join((f'[{key}:  {val}]' for key, val in vars(self).items()
                                 if not key.startswith('_'))) + ']'

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

    @property
    def stock(self) -> int:
        return sum(
            [variant.stock for variant in self.variants.values()]
        )

    @property
    def num_variants(self) -> int:
        return len(self.variants)

    def __repr__(self) -> str:
        prod = '\n'.join((f'{key:30s}:  {val}' for key, val in vars(self).items()
                                 if not key.startswith('_')))
        stock = '\n' + f'{"stock":30s}:  {self.stock}'
        num_variants = '\n' + f'{"num_variants":30s}:  {self.num_variants}'
        return '\n' + prod + stock + num_variants + '\n'

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

        out = ''
        for variant in self.variants.values():
            if variant.stock == 0:
                continue
            out += f'\n[{variant.title.strip()}]:  [{variant.stock}]'

        out += f'\n\nTotal Stock:  [{self.stock}]'
        embed.add_field(name='Variants', inline=False,
                        value=out)
        return embed


class Proxy:
    log: Log = Log('[PROXY]', do_update_title=False)

    def __init__(
            self,
            from_: str,
            host: str = "",
            port: str = "",
            username: str = '',
            password: str = '',
            protocol: str = 'http'
    ):
        if not from_.strip(): self.panic()
        if not any([from_, port, host]): self.panic()

        if not from_:
            self.host: str = host
            self.port: str = port
            self.username: str = username
            self.password: str = password
        elif from_:
            from_ = from_.split(':')
            if len(from_) == 2:
                self.host = from_[0]
                self.port = from_[1]
            elif len(from_) == 4:
                self.host = from_[0]
                self.port = from_[1]
                self.username = from_[2]
                self.password = from_[3]
        else:
            self.panic()
        self.protocol: str = protocol

    def __str__(self) -> str:
        if self.password:
            return f'{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}'
        return f'{self.protocol}://{self.host}:{self.port}'

    @staticmethod
    def panic():
        msg = f"Instantiation Data Not Valid."
        raise Exception(msg)


if __name__ == "__main__":
    print(Proxy(from_="46.37.115.52:11689:004769739:wifp3shx"))

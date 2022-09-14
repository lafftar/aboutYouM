from json import load, dumps

from db.tables import Product

with open('/home/lafftar/Documents/aboutYouM/src.json') as file:
    src = load(file)

ent = src.get('entities')[:3]

"""
dict[int: dumps(dict, separators=(',', ':'))]
    {
        pid: {dump},
        pid: {dump},
        ...
        pid: {dump}
    }
"""


for item in ent:
    item: dict

    pid: int = item.get('id')
    _dump: dict = item
    product: Product = Product(pid=pid, dump=_dump)
    print(product)
import re
from json import load, dumps
from os import listdir

from utils.root import get_project_root


def b():
    cmds = {
        "strin"
    }

    # we now have the file names, we're going to read through the files and load the json from the files.

    _keys_dict = {}

    addr = f'{get_project_root()}/recon/external/gf/examples'
    for key in listdir(addr):
        with open(f'{addr}/{key}') as file:
            _keys_dict[key] = load(file)

    print(dumps(_keys_dict, indent=4))


with open(
        r'C:\Users\lafft\Downloads\DiscordChatExporter\The Rental Exchange - checkout-log - flare-success [874033503346524160].json',
        encoding='utf-8') as f:
    js: dict = load(f)

print(js.keys())
msgs = js['messages']
# print(dumps(msgs[0], indent=4))

pids = []
for msg in msgs:
    try:
        store = msg['embeds'][0]['fields'][0]['value']
    except IndexError:
        continue
    if 'about' not in store.lower():
        continue

    for field in msg['embeds'][0]['fields']:
        if field['name'] == "Quick Task":
            val = field['value']
            if 'WAIT' in val.upper(): continue
            pids.append(int(re.search(r'[\d]{7}', val).group()))

had = [8600400,
       8676702,
       7176677,
       4785204,
       8502674,
       8680517,
       8308678,
       8659147,
       8641772,
       7117354,
       7444383,
       8610480,
       7130191,
       8610865,
       7780083]
print('\n'.join(list(set([str(pid) for pid in pids]))))

_had = []
for item in had:
    if item in pids:
        print(item)
        continue
    _had.append(item)

print('\n'.join(list(set([str(pid) for pid in _had]))))
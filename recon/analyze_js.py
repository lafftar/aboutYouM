from json import load, dumps
from os import listdir

from utils.root import get_project_root

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

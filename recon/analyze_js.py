from json import load, dumps

cmds = {
    "strin"
}


with open('/home/lafftar/Documents/aboutYouM/recon/external/gf/examples/_keys') as _keys:
    _keys = [key.strip() for key in _keys.readlines()]

if '_keys' in _keys:
    _keys.remove('_keys')  # 🤮

# we now have the file names, we're going to read through the files and load the json from the files.

_keys_dict = {}
for key in _keys:
    with open(f'/home/lafftar/Documents/aboutYouM/recon/external/gf/examples/{key}') as file:
        _keys_dict[key] = load(file)

print(dumps(_keys_dict, indent=4))

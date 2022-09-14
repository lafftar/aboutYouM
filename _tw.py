from json import load, dumps

with open('/home/lafftar/Documents/aboutYouM/src.json') as file:
    src = load(file)


print(dumps(src.get('entities'), indent=4))
print(len(src.get('entities')))
import json
import os

def main():
    assets = readJsonFiles()
    difference = generateDiff(assets[0], assets[1])
    with open("./GeneratedDiffs/2020_2021.json", "w") as f:
        json.dump(difference, f, indent=4)

def readJsonFile(path):
    with open(path, 'r') as f:
        return json.load(f)

def readJsonFiles():
    AssetsList = []
    jsonDirectory = '.\StockAssetsFD'
    for entry in os.listdir(jsonDirectory):
        full_path = os.path.join(jsonDirectory, entry)
        if os.path.isfile(full_path):
            if entry != '.gitignore':
                AssetsList.append(readJsonFile(full_path))
    return AssetsList

def generateDiff(previous, current):
    added_keys = set(current.keys()) - set(previous.keys())
    removed_keys = set(previous.keys()) - set(current.keys())
    modified_values = {}
    diff = []

    for key in set(previous.keys()) & set(current.keys()):
        if previous[key] != current[key]:
            modified_values[key] = (previous[key], current[key])

    # print(f"Added keys: {added_keys}")
    # print(f"Removed keys: {removed_keys}")
    # print(f"Modified values: {modified_values}")

    if len(added_keys) > 0:
        for key in added_keys:
            diff.append({'Stock': key, 'Transaction': 'Purchase', 'Amount': current[key]})
    if len(removed_keys) > 0:
        for key in removed_keys:
            diff.append({'Stock': key, 'Transaction': 'Sale', 'Amount': previous[key]})
    if len(modified_values) > 0:
        # write parser function and calculation function to operate on ranges of values
        for key in modified_values.keys():
            sale_or_purchase = ''
            if previous[key][0] < current[key][0]:
                sale_or_purchase = 'Purchase'
            else:
                sale_or_purchase = 'Sale'
            amount = (current[key][0] - previous[key][1], current[key][1] - previous[key][0])
            diff.append({'Stock': key, 'Transaction': sale_or_purchase, 'Amount': amount})
    return diff


main()
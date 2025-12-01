import json
import os

def main():
    assets = readJsonFiles()
    generateDiffs(assets)

# read a json file at path, output as a dictionary
def readJsonFile(path):
    with open(path, 'r') as f:
        return json.load(f)

# read all json files in StockAssetsFD, output combined results as a dictionary
def readJsonFiles():
    AssetsList = []
    jsonDirectory = '.\StockAssetsFD'
    for entry in os.listdir(jsonDirectory):
        full_path = os.path.join(jsonDirectory, entry)
        if os.path.isfile(full_path):
            if entry != '.gitignore':
                AssetsList.append(readJsonFile(full_path))
    return AssetsList

# find the difference between financial disclosures between two years of filing, resulting
# in a dictionary containing all transactions
def generateDiff(previous, current):
    added_keys = set(current.keys()) - set(previous.keys())
    removed_keys = set(previous.keys()) - set(current.keys())
    diff = {}
    if len(added_keys) > 0:
        for key in added_keys:
            diff[key] = {'Transaction': 'Purchase', 'Amount': current[key]}
    if len(removed_keys) > 0:
        for key in removed_keys:
            diff[key] = {'Transaction': 'Sale', 'Amount': previous[key]}
    return diff

# find the differences in FDs throughout the rep's term, outputting each difference as a json
# file in the GeneratedDiffs folder
def generateDiffs(allAssets):
    startingYear = int(os.listdir('.\StockAssetsFD')[1][:4])
    for year in range(len(allAssets) - 1):
        difference = generateDiff(allAssets[year], allAssets[year + 1])
        with open("./GeneratedDiffs/" + str(startingYear + year) + "_" + str(startingYear + year + 1) + ".json", "w") as f:
            json.dump(difference, f, indent=4)
        

import json
import os
import requests

USD_to_Range_Map = {
    "1001.0" : (1001, 15000),
    "15001.0" : (15001, 50000)
}

def readJsonFile(path):
    with open(path, 'r') as f:
        return json.load(f)
    
def filterAssetsToYear(year, assets):
    transactions = {}
    for trade in assets:
        if year in trade['Traded']:
            transactions[trade['Ticker']] = {'Transaction': trade['Transaction'],
                                             'Amount': USD_to_Range_Map[trade['Trade_Size_USD']]
                                            }
    return transactions

def compare(parsePrev, parseCurr, parseResults, apiResults):
    discrepancies = {}
    # keys in FD that are not in Quiver Data
    parseDiscrepancies = set(parseResults.keys()) - set(apiResults.keys())
    # keys in Quiver Data that are not in FD
    apiDiscrepancies = set(apiResults.keys()) - set(parseResults.keys())

    if len(parseDiscrepancies) > 0:
        for key in parseDiscrepancies:
            discrepancies[key] = {'Transaction': parseResults[key]['Transaction'],
                                  'Amount': parseResults[key]['Amount'],
                                  'Present_In': 'Financial Disclosure',
                                  'Missing_In': 'Stock Act Filings'}
    if len(apiDiscrepancies) > 0:   
        for key in apiDiscrepancies:
            if key in parsePrev.keys() and key in parseCurr.keys():
                pass
            else:
                discrepancies[key] = {'Transaction': apiResults[key]['Transaction'],
                                    'Amount': apiResults[key]['Amount'],
                                    'Present_In': 'Stock Act Filings',
                                    'Missing_In': 'Financial Disclosure'}
    return discrepancies

def pullTransactions(BGID):
    headers = {
        'Accept': 'application/json',
        'Authorization': 'Bearer 2143a235f7c66c48bcc95166d61147310ac4fa7f',
    }

    params = {
        'normalized': 'true',
        'page': '1',
        'page_size': '700',
        'bioguide_id': BGID,
        'nonstock': 'false',
    }

    response = requests.get('https://api.quiverquant.com/beta/bulk/congresstrading', params=params, headers=headers)
    return response.json()

def main(bioGuideID):
    startingYear = int(os.listdir('.\StockAssetsFD')[1][:4])
    Quiver_Assets = pullTransactions(bioGuideID)
    allDiffs = os.listdir('./GeneratedDiffs')[1:]
    allAssets = os.listdir('./StockAssetsFD')[1:]
    for year in range(len(allDiffs)):
        AssetsPrev = readJsonFile('./StockAssetsFD/' + allAssets[year])
        AssetsCurr = readJsonFile('./StockAssetsFD/' + allAssets[year + 1])
        FD_Assets = readJsonFile('./GeneratedDiffs/' + allDiffs[year])
        currentTransactions = filterAssetsToYear(str(startingYear + year + 1), Quiver_Assets)
        results = compare(AssetsPrev, AssetsCurr, FD_Assets, currentTransactions)
        with open("./Results/" + str(startingYear + year) + "_" + str(startingYear + year + 1) + ".json", "w") as f:
            json.dump(results, f, indent=4)

main('G000596')
import json
import os
import requests

USD_to_Range_Map = {
    "1001.0" : (1001, 15000),
    "15001.0" : (15001, 50000),
    "50001.0" : (50001, 100000),
    "100001.0" : (100001, 250000),
    "250001.0" : (250001, 500000),
    "500001.0" : (500001, 1000000),
    "1000001.0" : (1000001, 5000000)
}

Relevant_Transaction_Types = [
    'ST'
]

def readJsonFile(path):
    with open(path, 'r') as f:
        return json.load(f)
    
def filterAssetsToYear(year, assets):
    transactions = {}
    for trade in assets:
        if year in trade['Traded'] and trade['TickerType'] in Relevant_Transaction_Types:
            try:
                transactions[trade['Ticker']] = {'Transaction': trade['Transaction'],
                                                'Amount': USD_to_Range_Map[trade['Trade_Size_USD']]
                                                }
            except KeyError:
                transactions[trade['Ticker']] = {'Transaction': trade['Transaction'],
                                                'Amount': trade['Trade_Size_USD']
                                                }
    return transactions

def compare(parsePrev, parseCurr, parseResults, apiResults, allQuiver, year):
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
                transactions = [d['Traded'] for d in allQuiver if d['Ticker'] == key and year in d['Traded']]
                discrepancies[key] = {'Transaction': apiResults[key]['Transaction'],
                                    'Amount': apiResults[key]['Amount'],
                                    'Present_In': 'Stock Act Filings',
                                    'Missing_In': 'Financial Disclosure',
                                    'Number_of_Transactions': len(transactions),
                                    'Transaction_Dates': transactions}
    return discrepancies

def pullTransactions(BGID, api_token):
    headers = {
        'Accept': 'application/json',
        'Authorization': api_token,
    }

    params = {
        'normalized': 'true',
        'page': '1',
        'page_size': '700',
        'bioguide_id': BGID,
        'nonstock': 'false',
    }

    response = requests.get('https://api.quiverquant.com/beta/bulk/congresstrading', params=params, headers=headers)

    with open("./Results/" + BGID + '_trading.json', 'w') as json_file:
        json.dump(response.json(), json_file, indent=4)
    # print("Succesfully stored Quiver transaction history in " + "./Results/" + BGID + '_trading.json')

    return response.json()

def main(bioGuideID, APItoken):
    # print("Comparing Transactions")
    compiledResults = {}
    startingYear = int(os.listdir('.\StockAssetsFD')[1][:4])
    Quiver_Assets = pullTransactions(bioGuideID, APItoken)
    allDiffs = os.listdir('./GeneratedDiffs')[1:]
    allAssets = os.listdir('./StockAssetsFD')[1:]
    for year in range(len(allDiffs)):
        AssetsPrev = readJsonFile('./StockAssetsFD/' + allAssets[year])
        AssetsCurr = readJsonFile('./StockAssetsFD/' + allAssets[year + 1])
        FD_Assets = readJsonFile('./GeneratedDiffs/' + allDiffs[year])
        currentTransactions = filterAssetsToYear(str(startingYear + year + 1), Quiver_Assets)
        results = compare(AssetsPrev, AssetsCurr, FD_Assets, currentTransactions, Quiver_Assets, str(startingYear + year + 1))
        compiledResults[str(startingYear + year) + "-" + str(startingYear + year + 1)] = results
        # print("Succesfully Compared transactions in " + str(startingYear + year) + "-" + str(startingYear + year + 1))
    with open("./Results/" + bioGuideID + ".json", "w") as f:
        json.dump(compiledResults, f, indent=4)
    # print("Succesfully stored output in " + "./Results/" + bioGuideID + ".json")

import json
import os
import requests
import FetchDisclosures
import sys

# conversions for lower trade value bounds found in Quiver data
USD_to_Range_Map = {
    "1001.0" : (1001, 15000),
    "15001.0" : (15001, 50000),
    "50001.0" : (50001, 100000),
    "100001.0" : (100001, 250000),
    "250001.0" : (250001, 500000),
    "500001.0" : (500001, 1000000),
    "1000001.0" : (1000001, 5000000)
}

# list of transaction types to filter Quiver data with
Relevant_Transaction_Types = [
    'ST'
]

# read json file at path and output as dictionary
def readJsonFile(path):
    with open(path, 'r') as f:
        return json.load(f)
    
# filter and organize Quiver data to year we are currently comparing
def filterAssetsToYear(year, assets):
    transactions = {}
    for trade in assets:
        # if stock was traded in the current year and the type is in our list of relevant transaction types
        if year in trade['Traded'] and trade['TickerType'] in Relevant_Transaction_Types:
            # add transaction to dataset, key is the stock ticker, value is a dictionary with 2 items:
            # Transaction, whether the transaction was a purchase or a sale
            # Amount, the upper and lower bounds of the transaction amount
            try:
                transactions[trade['Ticker']] = {'Transaction': trade['Transaction'],
                                                'Amount': USD_to_Range_Map[trade['Trade_Size_USD']]
                                                }
            # If the amount is not one that is able to be converted by our USD_to_Range_Map dictionary, just save the 
            # raw lower bound found in Quiver
            except KeyError:
                transactions[trade['Ticker']] = {'Transaction': trade['Transaction'],
                                                'Amount': trade['Trade_Size_USD']
                                                }
    return transactions

# compare transactions pulled in Quiver data to difference between FDs in a given year, return a dictionary of discrepancies
def compare(parsePrev, parseCurr, parseResults, apiResults, allQuiver, year, fds, rep_info):
    FD_URL = 'https://disclosures-clerk.house.gov/public_disc/financial-pdfs/'
    discrepancies = {}
    # we need to parse FD keys to find links to PTRS in certain discrepancies
    xmls = FetchDisclosures.parseXMLs()
    # keys in FD that are not in Quiver Data
    parseDiscrepancies = set(parseResults.keys()) - set(apiResults.keys())
    # keys in Quiver Data that are not in FD
    apiDiscrepancies = set(apiResults.keys()) - set(parseResults.keys())

    # Missing in PTRs
    if len(parseDiscrepancies) > 0:
        for key in parseDiscrepancies:
            # save link to FD in year prior to when the discrepancy was found
            FD_PREV = FD_URL + str(int(year) - 1) + '/' + fds[str(int(year) - 1)][0] + '.pdf'
            # save link to FD in year when the discrepancy was found
            FD_CURR = FD_URL + year + '/' + fds[year][0] + '.pdf'
            # add stock to dictionary of discrepancies
            discrepancies[key] = {'Transaction': parseResults[key]['Transaction'],
                                  'Amount': parseResults[key]['Amount'],
                                  'Present_In': 'Financial Disclosure',
                                  'Missing_In': 'Stock Act Filings',
                                  'Number_of_Transactions': None,
                                  'Transaction_Dates': None,
                                  'Previous_FD': FD_PREV,
                                  'Current_FD': FD_CURR,
                                  'PTR': None}
    # Missing in FDs
    if len(apiDiscrepancies) > 0:   
        for key in apiDiscrepancies:
            # ignore cases where a purchase or partial sale was made in a stock that was already owned in the previous year
            # and is still owned in the current year according to FDs
            if key in parsePrev.keys() and key in parseCurr.keys():
                pass
            else:
                FD_PREV = FD_URL + str(int(year) - 1) + '/' + fds[str(int(year) - 1)][0] + '.pdf'
                FD_CURR = FD_URL + year + '/' + fds[year][0] + '.pdf'
                # find dates of all transactions of specific stock traded in current year
                transactions = [d['Traded'] for d in allQuiver if d['Ticker'] == key and year in d['Traded']]
                # find dates of all filings of specific stock traded in current year
                filings = [d['Filed'] for d in allQuiver if d['Ticker'] == key and year in d['Traded']]
                # find list of links to PTRs containing discrepant transactions in specific stock
                PTRs = find_PTRs(filings, rep_info, xmls, year)
                # add stock to dictionary of discrepancies
                discrepancies[key] = {'Transaction': apiResults[key]['Transaction'],
                                    'Amount': apiResults[key]['Amount'],
                                    'Present_In': 'Stock Act Filings',
                                    'Missing_In': 'Financial Disclosure',
                                    'Number_of_Transactions': len(transactions),
                                    'Transaction_Dates': transactions,
                                    'Previous_FD': FD_PREV,
                                    'Current_FD': FD_CURR,
                                    'PTR': PTRs}
    return discrepancies

# given a list of dates of discrepant Quiver transactions, associate them with PTRs and return them as a list 
def find_PTRs(dates, rep, XMLs, year):
    PTR_URL = 'https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/'
    IDs = []
    key = XMLs[int(year) - 2008]
    lastName = ''
    district = ''
    first_year = rep['ClerkOffice'][0]['YearRange'][0]
    transition_year = False
    tName = ''
    tDistrict = ''
    # In years when a representative changes their name or district, PTRs may be filed under either name or district
    # For example, when Dwights Evans changed his district from PA02 to PA03 in 2018, his 2018 PTRs were still filed
    # under the PA02 district. To accomodate this, we have to check both names and districts in transition years.
    for i in rep['ClerkOffice']:
        if int(year) >= i['YearRange'][0] and int(year) <= i['YearRange'][1]:
            lastName = i['LastName']
            district = i['District']
            if int(year) == i['YearRange'][0] and year != first_year:
                transition_year = True
            break
        tName = i['LastName']
        tDistrict = i['District']

    # associate each date with a PTR
    for date in dates:
        # convert date format in Quiver to match format in FDKeys
        xml_date = api_to_xml_date(date)
        link_found = False
        for child in key:
            filingDate = child.find('FilingDate')
            if filingDate.text == xml_date:
                if transition_year:
                    if ((lastName in child.find('Last').text or tName in child.find('Last').text) and (child.find('StateDst').text == district or child.find('StateDst').text == tDistrict)):
                        IDs.append(PTR_URL + year + '/' + child.find('DocID').text + '.pdf')
                        link_found = True
                else:
                    if lastName in child.find('Last').text and child.find('StateDst').text == district:
                        IDs.append(PTR_URL + year + '/' + child.find('DocID').text + '.pdf')
                        link_found = True

        # reps oftentimes do not file their PTRs in the same year that the actual transaction was made. In these cases, the 
        # links to these PTRs may be found in the FDKey that they were filed in rather than the year they were traded in.
        filing_year = xml_date[-4:]
        if not link_found and filing_year != year:
            backup_key = XMLs[int(filing_year) - 2008]
            for child in backup_key:
                filingDate = child.find('FilingDate')
                if filingDate.text == xml_date:
                    if transition_year:
                        if ((lastName in child.find('Last').text or tName in child.find('Last').text) and (child.find('StateDst').text == district or child.find('StateDst').text == tDistrict)):
                            IDs.append(PTR_URL + filing_year + '/' + child.find('DocID').text + '.pdf')
                            link_found = True
                    else:
                        if lastName in child.find('Last').text and child.find('StateDst').text == district:
                            IDs.append(PTR_URL + filing_year + '/' + child.find('DocID').text + '.pdf')
                            link_found = True

        if not link_found:
            IDs.append('Link Not Found')
    return list(dict.fromkeys(IDs))

# convert the date format in Quiver data entries to date format in FDKeys document entries
def api_to_xml_date(api_date):
    list_date = api_date.split('-')
    return str(int(list_date[1])) + '/' + str(int(list_date[2])) + '/' + list_date[0]

# pull all transactions made by inputted representative with Quiver API, save as a dictionary and output as a json file
def pullTransactions(BGID, api_token, _lastName, _district, _refresh_api):
    prior_results = os.listdir('.\Results')
    filepath = "./Results/" + _lastName + _district + '_trading.json'
    filename = _lastName + _district + '_trading.json'
    # Quiver API throttling is the main reason for slowdowns, if we aren't explicitly told to refresh the Quiver data and we already have
    # a json file with Quiver data from a previous instance of the program, simply use the data in that json file.
    if not _refresh_api and filename in prior_results:
        return readJsonFile(filepath)
    else:
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
        if 'details' in response.keys():
            print('Error: API throttle')
            sys.exit(6)
        else:
            with open(filepath, 'w') as json_file:
                json.dump(response.json(), json_file, indent=4)
            # print("Succesfully stored Quiver transaction history in " + "./Results/" + BGID + '_trading.json')

            return response.json()

def main(rep, APItoken, FD_IDs, refresh_api):
    bioGuideID = rep['BioguideID']
    lastName = rep['ClerkOffice'][-1]['LastName']
    district = rep['ClerkOffice'][-1]['District']
    compiledResults = {}
    startingYear = int(os.listdir('.\StockAssetsFD')[1][:4])
    Quiver_Assets = pullTransactions(bioGuideID, APItoken, lastName, district, refresh_api)
    allDiffs = os.listdir('./GeneratedDiffs')[1:]
    allAssets = os.listdir('./StockAssetsFD')[1:]
    for year in range(len(allDiffs)):
        AssetsPrev = readJsonFile('./StockAssetsFD/' + allAssets[year])
        AssetsCurr = readJsonFile('./StockAssetsFD/' + allAssets[year + 1])
        FD_Assets = readJsonFile('./GeneratedDiffs/' + allDiffs[year])
        currentTransactions = filterAssetsToYear(str(startingYear + year + 1), Quiver_Assets)
        results = compare(AssetsPrev,
                          AssetsCurr,
                          FD_Assets,
                          currentTransactions,
                          Quiver_Assets,
                          str(startingYear + year + 1),
                          FD_IDs,
                          rep)
        compiledResults[str(startingYear + year) + "-" + str(startingYear + year + 1)] = results
    with open("./Results/" + lastName + district + ".json", "w") as f:
        json.dump(compiledResults, f, indent=4)

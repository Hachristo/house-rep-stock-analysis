import CompareTransactions
import DifferentialTransactions
import FetchDisclosures
import ParseDisclosures
import os
import time
import json
import argparse

argParser = argparse.ArgumentParser()
argParser.add_argument("-p", "--path", help="path to JSON file containing representatives")
argParser.add_argument('--safe_mode', action='store_true', help='enables error handling for cleaner operation')
argParser.add_argument("-a", "--API_token", help="Quiver API token, required for Quiver API calls")
args = argParser.parse_args()

def clearFolder(path):
    for entry in os.listdir(path):
        if entry != '.gitignore':
            fullpath = os.path.join(path, entry)
            os.remove(fullpath)
    # print("Cleared " + path)

def clearDataFolders():
    clearFolder('./FinancialDisclosures')
    clearFolder('./GeneratedDiffs')
    clearFolder('./StockAssetsFD')
    clearFolder('./tmp')

def singleRun(bioGuideID, district, lastName):
    clearDataFolders()
    FetchDisclosures.main(lastName, district)
    ParseDisclosures.main()
    DifferentialTransactions.main()
    CompareTransactions.main(bioGuideID)

def singleRunDict(representative, token):
    clearDataFolders()
    for term in representative['ClerkOffice']:
        FetchDisclosures.main(term['LastName'], term['District'])
    ParseDisclosures.main()
    DifferentialTransactions.main()
    CompareTransactions.main(representative['BioguideID'], token)

def readJsonFile(path):
    with open(path, 'r') as f:
        return json.load(f)

def LIST_RUN(path, QuiverToken, safeMode):
    representatives = readJsonFile(path)
    for rep in representatives:
        if rep['Completed'] == False:
            print("Running " + rep['BioguideID'])
            if safeMode:
                try:
                    singleRunDict(rep, QuiverToken)
                except:
                    print("API throttled")
                    with open(path, "w") as f:
                        json.dump(representatives, f, indent=4)
                    break
                rep['Completed'] = True
                print(rep['BioguideID'] + " Completed, waiting 5 seconds for API throttle")
                time.sleep(5)
            else:
                singleRunDict(rep, QuiverToken)
                rep['Completed'] = True
                print(rep['BioguideID'] + " Completed, waiting 5 seconds for API throttle")
                time.sleep(5)
    print('All representatives have been processed')
    with open(path, "w") as f:
        json.dump(representatives, f, indent=4)

# def main():
#     LIST_RUN(args.path, 'Bearer ' + args.API_token, args.safe_mode)
def main():
    arguments = readJsonFile('./Project_Arguments.json')
    LIST_RUN(arguments['RepFilePath'], arguments['QuiverAPIToken'], arguments['UseSafeMode'])

main()

# LIST_RUN('./Representatives.json', 'Bearer 2143a235f7c66c48bcc95166d61147310ac4fa7f', True)

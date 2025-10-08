import CompareTransactions
import DifferentialTransactions
import FetchDisclosures
import ParseDisclosures
import os

representatives = {
    'G000596' : {'District' : 'GA14', 'LastName' : 'Greene'},
    'M001213' : {'District' : 'UT01', 'LastName' : 'Moore'}
}

def clearFolder(path):
    for entry in os.listdir(path):
        if entry != '.gitignore':
            fullpath = os.path.join(path, entry)
            os.remove(fullpath)
    print("Cleared " + path)

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

singleRun('M001213', 'UT01', 'Moore')

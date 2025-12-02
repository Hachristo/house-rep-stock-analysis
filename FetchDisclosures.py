import requests
import xml.etree.ElementTree as ET
import os
import sys

path = './FinancialDisclosures/'

def main(rep, _fdids):
    xmls = parseXMLs(rep['ClerkOffice'][0]['YearRange'][0], rep['ClerkOffice'][-1]['YearRange'][1])
    docIDs = get_DocIDs(xmls, rep)
    download_All(docIDs)
    _fdids.update(docIDs)

# Parse the XML files in FDKeys
def parseXMLs(start, end):
    parsedXMLs = []
    xmlDirectory = '.\FDKeys'
    XMLs = os.listdir(xmlDirectory)
    for i in range(start - 2008, end - 2008 + 1):
        entry = XMLs[i]
        full_path = os.path.join(xmlDirectory, entry)
        if os.path.isfile(full_path):
            if entry != '.gitignore':
                # Perform operations on the file
                try:
                    tree = ET.parse(full_path)
                    root = tree.getroot()
                    parsedXMLs.append(root)
                except FileNotFoundError:
                    print("Fetch Error: '" + full_path + "' not found.")
                    sys.exit(1)
                except ET.ParseError as e:
                    print(f"Fetch Error parsing XML: {e}")
                    sys.exit(2)
    return parsedXMLs
    
# find FDs for representative in FDKeys
def get_DocIDs(_xmls, rep):
    DocDict = {}
    for root in _xmls:
        DocIDs = []
        year = root[0].find('Year').text
        _name = ''
        _district = ''
        for term in rep['ClerkOffice']:
            if int(year) >= term['YearRange'][0] and int(year) <= term['YearRange'][1]:
                _name = term['LastName']
                _district = term['District']
                break
        if _name == '' or _district == '':
            print('Fetch Error: missing Clerk Office data in ' + year)
            sys.exit(6)
        for child in root:
            filingType = child.find('FilingType')
            if filingType.text == 'O' or filingType.text == 'H':
                if _name in child.find('Last').text and child.find('StateDst').text == _district:
                    DocIDs.append(child.find('DocID').text)
        DocDict[year] = DocIDs
    return DocDict

# request FD from clerk office and download into FinancialDisclosures folder
def download_pdf_from_url(pdf_url, local_filename):
    """
    Downloads a PDF file from a given URL and saves it locally.

    Args:
        pdf_url (str): The URL of the PDF file.
        local_filename (str): The name to save the PDF file as locally.
    """
    try:
        response = requests.get(pdf_url, stream=True)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        with open(local_filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        # print(f"PDF downloaded successfully to {local_filename}")

    except requests.exceptions.RequestException as e:
        print(f"Fetch Error: failed to download PDF: {e}")
        sys.exit(3)

# request all FDs for rep
def download_All(dict):
    baseURL = 'https://disclosures-clerk.house.gov/public_disc/financial-pdfs/'
    prev_year = list(dict.keys())[0]
    for year in dict.keys():
        # ensure that FDs found are all consecutive, if we are missing a year then the program won't work
        if prev_year == year or int(year) - int(prev_year) == 1:
            prev_year = year
            fullBase = baseURL + year + '/'
            for id in dict[year]:
                download_pdf_from_url(fullBase + id + '.pdf', path + year + '.pdf')
        else:
            print("Fetch Error: missing FD(s) between " + prev_year + " and " + year)
            sys.exit(4)


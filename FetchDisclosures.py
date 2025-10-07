import requests
import xml.etree.ElementTree as ET
import os

DocDict = {}
path = './FinancialDisclosures/'

def main(name, district):
    print("Fetching Financial Disclosures")
    xmls = parseXMLs()
    get_DocIDs(xmls, name, district)
    download_All(path)

# Parse the XML fileS
def parseXMLs():
    parsedXMLs = []
    xmlDirectory = '.\FDKeys'
    for entry in os.listdir(xmlDirectory):
        full_path = os.path.join(xmlDirectory, entry)
        if os.path.isfile(full_path):
            if entry != '.gitignore':
                # Perform operations on the file
                try:
                    tree = ET.parse(full_path)
                    root = tree.getroot()
                    parsedXMLs.append(root)
                except FileNotFoundError:
                    print("Error: '" + full_path + "' not found.")
                    exit()
                except ET.ParseError as e:
                    print(f"Error parsing XML: {e}")
                    exit()
    return parsedXMLs
    
    

def get_DocIDs(_xmls, _name, _district):
    for root in _xmls:
        DocIDs = []
        year = root[0].find('Year').text
        for child in root:
            filingType = child.find('FilingType')
            if filingType.text == 'O' or filingType.text == 'H':
                if child.find('Last').text == _name and child.find('StateDst').text == _district:
                    DocIDs.append(child.find('DocID').text)
        if len(DocIDs) > 0:
            DocDict[year] = DocIDs

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
        print(f"PDF downloaded successfully to {local_filename}")

    except requests.exceptions.RequestException as e:
        print(f"Error downloading PDF: {e}")

def download_All(outputPath):
    baseURL = 'https://disclosures-clerk.house.gov/public_disc/financial-pdfs/'
    for year in DocDict.keys():
        fullBase = baseURL + year + '/'
        for id in DocDict[year]:
            download_pdf_from_url(fullBase + id + '.pdf', path + year + '.pdf')


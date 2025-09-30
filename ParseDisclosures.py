import json
import pymupdf
import os

def convertToText(pdf):
    doc = pymupdf.open(pdf) # open a document
    out = open("./tmp/" + pdf[23:-4] + ".txt", "wb") # create a text output
    for page in doc: # iterate the document pages
        text = page.get_text().encode("utf8") # get plain text (is in UTF-8)
        out.write(text) # write text of page
        out.write(bytes((12,))) # write page delimiter (form feed 0x0C)
    out.close()

def parseDisclosure(txtFile):
    assets = {}             # dictionary to contain list of assets
    reading = False         # only perform parsing checks when we are in a table
    keyReading = False      # reading mode for names of assets
    valueReading = False    # reading mode for values of assets
    keyComplete = False     # tracks whether the name of current asset has been fully parsed
    valueComplete = False   # tracks whether the value of current asset has been fully parsed
    spanOverride = False    # tracks when line contains a page break, necessitating special reading mode
    key = ""
    value = ""
    headerEnd = ""
    yearReading = False
    with open(txtFile, 'r', encoding="utf8") as file:
        # each line of the text file is parsed sequentially
        for line in file:
            # every table is followed by a line starting with an asterisk, letting us know
            # we've reached the end of a table
            if '*' in line:
                reading = False
                break
            # we are currently parsing through a table
            if line.casefold() == "Filing Type:\n".casefold():
                yearReading = True
                continue
            if yearReading:
                if line.casefold() == 'New Filer Report\n'.casefold():
                    headerEnd = "Year\n"
                else:
                    headerEnd = "$1,000?\n"
                yearReading = False
            if reading:
                # first page contains a line that starts with "Filing ID #[0-9]*", we don't want to parse this line
                if 'Filing ID' in line:
                    continue
                # \xoc is a page break. When this is encountered, we need to enter a special reading mode to account
                # for entries broken over two pages
                if '\x0c' in line:
                    if line == "\x0cAsset\n":
                        spanOverride = True
                        continue
                    else:
                        continue
                # page breaks interrupt the otherwise predictable pattern of data contained within the text file, so
                # we must ensure that we account for every edge case.
                if spanOverride:
                    if line.casefold() == headerEnd.casefold():
                        # we have fully recorded a name, but the value is split across two 
                        # pages and has yet to be fully recorded. In this case, we wait for the end of the table header,
                        # '$1,000?\n', and enter value reading mode on the next line to read the rest of the value
                        if keyComplete:
                            valueReading = True
                        spanOverride = False
                    else:
                        continue
                # we're looking for a line containing a stock abbreviation, something like JNJ (Johnson and Johsnon) or 
                # TSLA (Tesla). These will form the keys to our dataset
                elif keyReading:
                    # stock abbreviations are always found between parentheses, so we only continue with lines that open
                    # a parentheses
                    if '(' in line:
                        start_index = line.find('(')                # index of first parentheses
                        end_index = line.find(')', start_index + 1) # index of second parentheses
                        keyString = line[start_index + 1 : end_index]     # key is the substring between the two indexes
                        # parentheses are occassionally used in other places, but stock abbreviations are always a 
                        # series of uppercase characters. As long as we check to make sure our string matches that
                        # condition, we can save it as a key and start looking for it's associated value
                        if keyString.isupper():
                            key = keyString
                            valueReading = True
                            keyComplete = True
                            keyReading = False
                        else:
                            key = ""
                            continue
                # now we're looking for the value of the stock, always found after the key
                elif valueReading:
                    # certain stocks are owned at least in part by someone other than the filer, in which case we 
                    # include that information in the key
                    if line == 'SP\n' or line == 'JT\n' or line == 'DC\n':
                        key += ' (' + line.replace('\n', '') + ')'
                    # the value of certain stocks is marked as None or Undetermined in some cases
                    elif (line == 'None\n' or line == 'Undetermined\n') and value == "":
                        value += line.replace('\n', '')
                        valueComplete = True
                        valueReading = False
                    # otherwise, we are looking for the first instance of a '$' to indicate the presence of a value range
                    elif "$" in line:
                        value += line.replace('\n', '')
                        # oftentimes value ranges are split across two lines. If so, we continue value reading into the next line
                        # and save both lines as part of the value range
                        if '-' not in line or line.count('$') == 2:
                            valueComplete = True
                            valueReading = False
                        else:
                            value += ' '
                    elif "(" in line:
                        start_index = line.find('(')
                        end_index = line.find(')', start_index + 1)
                        keyString = line[start_index + 1 : end_index]
                        if keyString.isupper():
                            if key != "":
                                if key in assets.keys():
                                    assets[key].append("ERROR")
                                else:
                                    assets[key] = ["ERROR"]
                            key = keyString
                            valueReading = True
                            keyComplete = True
                            keyReading = False
                        else:
                            key = ""
                            continue     
                # if we have a complete key and value after reading a line, we save that key/value to our assets dictionary
                if keyComplete and valueComplete:
                    last_index = value.rfind('0')
                    if last_index != -1:
                        value = value[:last_index + 1]
                    # there are occasionally multiple entries for the same stock in these disclosures, so we make a list of 
                    # values associated with each key for each distinct entry
                    if key in assets.keys():
                        assets[key].append(value)
                    else:
                        assets[key] = [value]
                    key = ""
                    value = ""
                    keyComplete = False
                    valueComplete = False
                    keyReading = True
            # starts reading when the end of table header is encountered for the first time
            elif line.casefold() == headerEnd.casefold():
                reading = True
                keyReading = True
    file.close()
    for key in assets.keys():
        valueString = ""
        for v in assets[key]:
            valueString += v + ", "
    with open("./StockAssetsFD/" + txtFile[6:-4] + ".json", "w") as f:
        json.dump(assets, f, indent=4)

def main():
    pdfDirectory = '.\FinancialDisclosures'
    for entry in os.listdir(pdfDirectory):
        full_path = os.path.join(pdfDirectory, entry)
        if os.path.isfile(full_path):
            print(f"File: {full_path}")
            convertToText(full_path)
    txtDirectory = './tmp'
    for entry in os.listdir(txtDirectory):
        full_path = os.path.join(txtDirectory, entry)
        if os.path.isfile(full_path):
            print(f"File: {full_path}")
            parseDisclosure(full_path)
            


# fileName = "MTG2023FD"
# convertToText(fileName + ".pdf")
# parseDisclosure(fileName + ".txt")

main()





            

            
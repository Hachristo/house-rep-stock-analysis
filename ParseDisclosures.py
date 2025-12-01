import json
import pymupdf
import os

# convert a pdf to a text file
def convertToText(pdf):
    doc = pymupdf.open(pdf) # open a document
    out = open("./tmp/" + pdf[23:-4] + ".txt", "wb") # create a text output
    for page in doc: # iterate the document pages
        text = page.get_text().encode("utf8") # get plain text (is in UTF-8)
        out.write(text) # write text of page
        out.write(bytes((12,))) # write page delimiter (form feed 0x0C)
    out.close()

# parse text file of FD into a dictionary containing all stock assets and values
def parseDisclosure(txtFile):
    asset_type_codes = ['ST', 'CS', 'CT', 'FU', 'OP', 'RS', 'EF']   # types of relevant assets
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
            # new filers have slightly altered formatting, using 'Year\n' as the header for the rightmost column
            # rather than '$1,000?\n'. This is checked before we parse the table in the following blocks
            if line.casefold() == "Filing Type:\n".casefold():
                yearReading = True
                continue
            if yearReading:
                if line.casefold() == 'New Filer Report\n'.casefold():
                    headerEnd = "Year\n"
                else:
                    headerEnd = "$1,000?\n"
                yearReading = False
            # we are currently parsing through a table
            if reading:
                # first page contains a line that starts with "Filing ID #[0-9]*", we don't want to parse this line
                if 'Filing ID' in line:
                    continue
                # \xoc is a page break. When this is encountered, we need to enter a special reading mode to account
                # for entries broken over two pages
                if '\x0c' in line:
                    if line == "\x0cAsset\n":
                        spanOverride = True
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
                        # filers use this character to add notes to entries, we don't want anything from these notes
                        if '⇒' in line:
                            continue
                        else:
                            start_index = line.find('(')                    # index of first parentheses
                            end_index = line.find(')', start_index + 1)     # index of second parentheses
                            if end_index == -1:
                                end_index = line.find(' ', start_index + 1) # index of space after first paren, in case they forgot to close
                            keyString = line[start_index + 1 : end_index]   # key is the substring between the two indexes
                            # parentheses are occassionally used in other places, but stock abbreviations are always a 
                            # series of uppercase characters. As long as we check to make sure our string matches that
                            # condition, we can save it as a key and start looking for it's associated value
                            if keyString.isupper() and keyString.find(' ') == -1:
                                key = keyString
                                valueReading = True
                                keyComplete = True
                                keyReading = False
                            else:
                                key = ""
                                continue
                            # we perform an additional check to filter out assets that are not in our list of relevant types.
                            # not all filers include these type abbreviations, so it's not perfect, but this works for most filers.
                            if '[' in line:
                                start_index = line.find('[')
                                asset_type = line[start_index + 1 : start_index + 3]
                                if asset_type not in asset_type_codes:
                                    key = ""
                                    valueReading = False
                                    keyComplete = False
                                    keyReading = True
                                    continue
                # now we're looking for the value of the stock, always found after the key
                elif valueReading:
                    if '[' in line:
                        start_index = line.find('[')
                        asset_type = line[start_index + 1 : start_index + 3]
                        if asset_type not in asset_type_codes:
                            key = ""
                            valueReading = False
                            keyComplete = False
                            keyReading = True
                            continue
                    # the value of certain stocks is marked as None or Undetermined in some cases
                    elif (line == 'None\n' or line == 'Undetermined\n') and value == "":
                        value += line.replace('\n', '')
                        valueComplete = True
                        valueReading = False
                    # otherwise, we are looking for the first instance of a '$' to indicate the presence of a value range
                    elif "$" in line:
                        if value == '':
                            value += line.replace('\n', '')
                            if line.count('$') == 2:
                                valueComplete = True
                                valueReading = False
                            else:
                                value += ' '
                        # oftentimes value ranges are split across two lines. If so, we continue value reading into the next line
                        # and save both lines as part of the value range
                        else:
                            if '-' not in line:
                                value += line.replace('\n', '')
                                valueComplete = True
                                valueReading = False
                    # if we find another stock abbreviation while looking for a value, we know we've missed a value. We don't 
                    # know what that value is, and we indicate that by filling the value as 'ERROR', and moving on with the next.
                    elif "(" in line:
                        if '⇒' in line:
                            continue
                        start_index = line.find('(')
                        end_index = line.find(')', start_index + 1)
                        keyString = line[start_index + 1 : end_index]
                        if keyString.isupper():
                            if key != "":
                                assets[key] = "ERROR"
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
                        assets[key] = addRange(assets[key], rangeToInt(value))
                    else:
                        assets[key] = rangeToInt(value)
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
    with open("./StockAssetsFD/" + txtFile[6:-4] + ".json", "w") as f:
        json.dump(assets, f, indent=4)
    # print('Succesfully parsed ' + txtFile[6:10])

# add two value ranges (tuples containing upper and lower bound) together
def addRange(range1, range2):
    if range1 == "ERROR":
        return "ERROR"
    else:
        return (range1[0] + range2[0], range1[1] + range2[1]) 

# convert a string representing a range of value into a tuple containing the lower and upper bounds as ints
def rangeToInt(range):
    if range == "None" or range == "Undetermined":
        return (0, 0)
    else:
        characters_to_remove = '$, '
        translation_table = range.maketrans("", "", characters_to_remove)
        range = range.translate(translation_table)
        minValue = range[0:range.find('-')]
        maxValue = range[range.find('-') + 1:]
        try:
            return (int(minValue), int(maxValue))
        except:
            return (0, 0)

def main():
    pdfDirectory = '.\FinancialDisclosures'
    for entry in os.listdir(pdfDirectory):
        full_path = os.path.join(pdfDirectory, entry)
        if os.path.isfile(full_path):
            if entry != '.gitignore':
                convertToText(full_path)
    txtDirectory = './tmp'
    for entry in os.listdir(txtDirectory):
        full_path = os.path.join(txtDirectory, entry)
        if os.path.isfile(full_path):
            if entry != '.gitignore':
                parseDisclosure(full_path)







            

            
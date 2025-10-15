# VR Research: House of Representatives Stock Transaction/Financial Disclosure Analysis
---
## About
The purpose of this project is to assist in analysis of annual financial disclosures (FDs) and periodic transaction reports (PTRs), searching specifically for discrepancies in stock assets. Data is provided by the [Office of the Clerk](https://disclosures-clerk.house.gov/), where FDs and PTRS of all house representatives going back to 2007 can be accessed freely. The analysis is performed by parsing all submitted FDs from a single representative into an associated array, which is then compared to the stock transaction history available from [Quiver API](https://api.quiverquant.com/docs/). Stocks present in FDs that are not accounted for in PTRs, and vice versa, are saved in a JSON file to be reveiwed.

## Usage
Clone this repo and download [python](https://www.python.org/downloads/).

Use of this project is restricted to members of VR Research and approved clients. Upon being granted authorization, you'll be provided with two JSON files, 'Project_Arguments.json' and 'Representatives.json'. 

**Project_Arguments.json**

This file contains three values, 'RepFilePath', 'UseSafeMode', and 'QuiverAPIToken'.

RepFilePath: Replace the value in quotes with the path to 'Representatives.json'.

UseSafeMode: Leave this value as true unless you are a developer and want to see error messages, then replace it with false.

QuiverAPIToken: Enter your Quiver API token, preceded by 'Bearer '.

**Representatives.json**

This file contains a list of the representatives you'd like the program to run on. Each representative is entered as a JSON object with the following schema:
`{
        "BioguideID": string,
        "Completed": boolean,
        "ClerkOffice": [
            {
                "YearRange": [
                    int,
                    int
                ],
                "LastName": string,
                "District": string
            }
        ]
}`

BioguideID: Unique identifier for House members, used to pull data from Quiver. BioguideIDs can be found [here](https://www.congress.gov/help/field-values/member-bioguide-ids).

Completed: Flag for tracking whether member has already been analysed by the program, automatically updated after program completion.

ClerkOffice: List of terms served by the House member. Occasionally house members change their last name or district when filing, which can be accommodated for here by entering multiple terms in this list.

YearRange: List containing the first and last year the member filed with the last name and district included below.

LastName: Last name of the member as filed in the [Office of the Clerk](https://disclosures-clerk.house.gov/).

District: State and district number of the member as filed in the [Office of the Clerk](https://disclosures-clerk.house.gov/). State is written as the two letter state abbreviation followed by the two digit district number, with no spaces. For example, California district 07 would be written as 'CA07'.

**Running the program**

Once you've included these files, run the program from Command Prompt (Windows) or Terminal (Mac) by typing "python FindDiscrepancies.py" and pressing enter. Progress will be displaying in the command line, and output will be saved in the 'Results' folder as a JSON file named after the representative's BioguideID. The transactions pulled from Quiver will also be saved as a JSON file named as the BioguideID followed by '_trading'.

**API Throttling**

Quiver API monitors and limits the number of API calls made within a certain time frame, meaning that program flow will be halted occasionally by API throttling if the program makes too many API calls too quickly. A time buffer has been built in to reduce this, but in case throttling does occur, an exception has been written which will halt program execution. When this happens, simply wait for a few minutes and run the program again. Progress in analysing the list of representatives included in the 'Representatives.json' will be saved, and will continue with members whose "Completed" value is false.

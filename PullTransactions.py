# import quiverquant
# import pandas
# quiver = quiverquant.quiver("2143a235f7c66c48bcc95166d61147310ac4fa7f")

# df = quiver.congress_trading("Marjorie Taylor Greene", politician=True)
# json_columns = df.to_json()

# df.to_json('trading.json', orient='records', indent=4)

import requests
import json

headers = {
    'Accept': 'application/json',
    'Authorization': 'Bearer 2143a235f7c66c48bcc95166d61147310ac4fa7f',
}

params = {
    'normalized': 'true',
    'page': '1',
    'page_size': '700',
    'bioguide_id': 'M001213',
    'nonstock': 'true',
}

response = requests.get('https://api.quiverquant.com/beta/bulk/congresstrading', params=params, headers=headers)

json_response = response.json()

with open('trading.json', 'w') as json_file:
    json.dump(json_response, json_file, indent=4)


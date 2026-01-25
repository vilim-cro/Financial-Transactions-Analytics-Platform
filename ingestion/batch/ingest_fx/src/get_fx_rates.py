import os
import freecurrencyapi

client = freecurrencyapi.Client(os.getenv('FREECURRENCYAPI_API_KEY'))

result = client.latest(currencies=['EUR', 'DKK', 'NOK', 'SEK'])["data"]
print(result)

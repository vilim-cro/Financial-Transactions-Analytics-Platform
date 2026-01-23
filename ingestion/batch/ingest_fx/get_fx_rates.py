import freecurrencyapi
client = freecurrencyapi.Client('fca_live_ELNmWqgUPubg76NaexnWUpXv6Cmn2P55Piqo7Ukt')

result = client.currencies(currencies=['EUR', 'CAD'])
print(result)


result = client.latest(currencies=['EUR', 'DKK', 'NOK', 'SEK'])
print(result)


print(client.status())

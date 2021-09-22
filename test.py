from settings import Settings


print(Settings().broker.price("BTC/USDT")['bid'])


print("BTC" in "BTC/USDT")
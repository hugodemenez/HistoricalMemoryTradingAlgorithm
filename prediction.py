r"""
On regarde le prix actuel et on voit s'il touche un support qui est enregistré dans un fichier supports.csv        
"""
__autor__= "Hugo Demenez"

from settings import Settings
from csv_generator import csv_reader


class Prediction:
    def __init__(self):
        pass
    

    def buy_signal(self,symbol):
        """
        Donne le signal d'achat
        """
        symbol = symbol.replace(Settings().base_asset,"")
        error = ''
        
        current_price = Settings().broker.price(symbol)['bid']
            
        try:
            for support in csv_reader().file_to_dict_list():
                #Look if current price is almost on the support (tolerence %)
                    if current_price < support['price']*(1+Settings().tolerence) and current_price > support['price']*(1-Settings().tolerence) and support['paire']==symbol:
                        return {
                            'signal':"buy",
                            'recovery': support['potential_yield'],
                            'symbol' : symbol,
                        }

        except Exception as e:
            error = e
            
        return {
                'signal':"neutral",
                'symbol' : symbol,
                'error' : error,
            }



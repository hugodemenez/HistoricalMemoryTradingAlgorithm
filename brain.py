r"""
Ce programme sert à ouvrir, gérer et fermer les positions. 
Enregistre les positions dans la base de données et dans un fichier excel,
les affiches dans le terminal puis envoie une notification au groupe telegram

"""
import time,datetime,os,sys,requests
from brokerconnection import realcommands
from prediction import Prediction
from settings import Settings
from database import Database
from position import Position
from csv_generator import csv_generator



#Definition of variables
Position=Position()
Settings=Settings()
Database=Database()

def current_second() :
    return datetime.datetime.now().second

def cls():
    """
    This function clear the terminal in order to get the clear view of the prints.c
    """
    os.system('cls' if os.name=='nt' else 'clear')

def open_position(symbol):
    """
    This function send an open order to the broker, with the opening price,
    and then save the data inside the class Position.
    """
    
    if Position.backtesting == False:
        order = realcommands().limit_open(symbol=symbol,backtesting=Position.backtesting)
        if order['error']==True:
            return False
        Position.open_price=float(order['order']['price'])
        current_price = Settings.broker.price(symbol)['ask']
    else:
        time.sleep(2)
        current_price = Settings.broker.price(symbol)['ask']
        Position.open_price = current_price

    
    Position.symbol=symbol
    Position.current_price =current_price
    #Setting highest price and lowest price to the opening price
    Position.highest_price=Position.open_price
    Position.lowest_price=Position.open_price
    Position.status='open'    
    Position.number+=1
    Position.time=time.time()
    return True

def close_position():
    """
    This function send a close order to the broker, at market, 
    and then save the data inside an excel spreadsheet.
    """
    Position.status='close'  
    Position.stoploss = False
    Position.effective_yield = effective_yield_calculation(Position.close_price,Position.open_price,Settings.fee)
    Position.total_yield = round(Position.total_yield*Position.effective_yield,5)
    if Position.total_yield > Position.highest_yield:
        Position.highest_yield = Position.total_yield
    save_position()
    return


def save_position():
    """
    This function sends notification and add position information to database.
    """
    try:
        date = time.time()

        text=''
        text+="\nRendement : "+str(round((Position.total_yield-1)*100,2))+' %'
        program_notification(message=text)
        
        #Saving position into database
        Database.database_request(
            sql=("""REPLACE INTO positions (paire,opening_date,closing_date,duration,opening_price,closing_price,exit_way,highest_price,lowest_price,position_yield,total_yield) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""),
            params=(
                Position.symbol,
                datetime.datetime.fromtimestamp(Position.time),
                datetime.datetime.fromtimestamp(date),
                str(datetime.timedelta(seconds=round(date,0)-round(Position.time,0))),
                Position.open_price,
                Position.close_price,
                Position.close_mode,
                Position.highest_price,
                Position.lowest_price,
                Position.effective_yield,
                Position.total_yield,
            ),
            commit=True
        )
        return
    except Exception as error:
        program_notification(message=error)

def program_notification(message):
    try:
        token = "1813447727:AAHDPI54DetjXDDNFCMqtN-7phGvwNy9rqY"
        chat_id = "-431364858"
        url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}"
        requests.post(url)
    except Exception as error:
        print(error)
        
def effective_yield_calculation(current_price,opening_price,fee):
    R = float(current_price)/float(opening_price)
    F = float(fee)
    return (R-(F+(1-F)*R*F))

def check_position():
    """ 
    Function to update the current_price, the highest_price and the lowest price
    Then checks if it has to close the position
    """
    Position.current_price = Settings.broker.price(Position.symbol)['bid']

    #Updating highest_price
    if Position.current_price >Position.highest_price:
        Position.highest_price=Position.current_price 

    #Updating lowest_price
    if Position.current_price <Position.lowest_price:
        Position.lowest_price=Position.current_price 

    #Calculating current effective_yield
    current_effective_yield = effective_yield_calculation(
        current_price=Position.current_price,
        opening_price=Position.open_price,
        fee=Settings.fee
        )

    #Stop loss 
    #Close position :
    if current_effective_yield < Settings.risk:
        if Position.backtesting:
            Position.close_price = Position.open_price*(Settings.risk)
        else:
            order = realcommands().limit_close(Position.symbol,backtesting=Position.backtesting)
            Position.close_price = float(order['price'])
            
        Position.close_mode = 'stoploss'
        Position.number_lost+=1
        close_position()
        return

    #Take profit on expected yield 
    #Closing on takeprofit : Check if the yield  is stronger  than the minimal yield considering fees and slippage
    if current_effective_yield > Settings.expected_yield:
        if Position.backtesting:
            Position.close_price = Position.current_price
        else:
            order = realcommands().limit_close(symbol=Position.symbol,backtesting=Position.backtesting)
            Position.close_price = float(order['price'])

        Position.close_mode = 'takeprofit'
        close_position()
        return




def find_entry_point():
    #Analyse market every second
    #We use the watchlist defined in settings.py
    for symbol in Settings.watchlist:
        time.sleep(1)
        try:
            #We analyze the market with the signals defined inside prediction.py
            predict = Prediction().buy_signal(symbol+'/'+Settings.base_asset)
            #We clear the console
            cls()
            for values in predict:
                print(values,':',predict[values],'\n')
            #Give information about the program
            statistics = {
                '':'------------------------------ :',
                'running_time':str(datetime.timedelta(seconds=round(time.time(),0)-round(Position.start_time,0))),
                'current_status':Position.status,
                'total_yield':str(round((Position.total_yield-1)*100,2))+' %',
                'position_number':Position.number,
                'position_lost':Position.number_lost,
            }

            for data, value in statistics.items():
                print(data, ':', value, '\n')

                #If we get a buy signal then :
            if predict['signal'] == 'buy' and open_position(
                symbol+'/'+Settings.base_asset
            ):

                Settings.expected_yield = predict['recovery']
                return predict


        except Exception as error:
            print('error while predicting : %s' % error)
                            
def manage_position(predict):
    #We clear the console
    cls()
    for values in predict:
        print(values,':',predict[values],'\n')
    current_effective_yield=effective_yield_calculation(Position.current_price,Position.open_price,Settings.fee)
    #Give information about the program
    statistics = {
        '':'------------------------------ :',
        'running_time':str(datetime.timedelta(seconds=round(time.time(),0)-round(Position.start_time,0))),
        'current_status':Position.status,
        'current_price':Position.current_price,
        'open_price':Position.open_price,
        'highest_price':Position.highest_price,
        'lowest_price':Position.lowest_price,
        'position_number':Position.number,
        'position_yield':str(round((current_effective_yield-1)*100,2))+' %',
        'total_yield':str(round((Position.total_yield*current_effective_yield-1)*100,2))+' %',
        'number_lost':Position.number_lost,
        'stoploss':Position.stoploss,
        'current_position_time':str(datetime.timedelta(seconds=round(time.time(),0)-round(Position.time,0))),
    }

    for data, value__ in statistics.items():
        print(data, ':', value__, '\n')

    try:
        #We check if we have to do something with the current position, update current price highest price and lowest price
        check_position()
    except:
        print(Exception)
    #We slow down the requests
    time.sleep(0.2)


def main():
    '''Brain'''
    #Check the correct version of python
    if sys.version_info[0] < 3:
        raise Exception("Python 3 or a more recent version is required.")
    #test des commandes et de la connection au broker
    if realcommands().test_connection():
        print("Connected to market")

    elif input("Unable to connect to market, run in backtesting mode? Y/N : ").upper()=='N':
        return
    else:
        Position.backtesting = True
    
    #Generates file with known supports
    csv_generator()    
        
    #On change la description du telegram pour les settings
    parameters = vars(Settings)
    about = ''.join(
        '\n' + str(param) + ' : ' + str(value_)
        for param, value_ in parameters.items()
    )
    program_notification(about)
    
    
    #On initialise le temps de fonctionnement du programme
    Position.start_time = time.time()
    print('---Starting Trading---')
    if Position.backtesting == True:
        program_notification("Démarrage du programme : "+Settings.program_name + " en mode démo \n"+Settings.commentaire)
    else:
        program_notification("Démarrage du programme : "+Settings.program_name + " en mode réél \n"+Settings.commentaire)

    while True:
        try:
            
            if Position.highest_yield-Position.total_yield > Settings.program_risk:
                print("Program stopped : check strategy")
                break
            
            if Position.status == 'close':
                predict = find_entry_point()
                
                           
            elif Position.status == 'open':
                manage_position(predict)
                

            
            
            
        except KeyboardInterrupt:
            cls()
            if Position.status == 'open':
                if Position.backtesting:
                    Position.close_price = Position.current_price
                else:
                    order = realcommands().limit_close(symbol=Position.symbol,backtesting=Position.backtesting)
                    Position.close_price = float(order['price'])

                Position.close_mode = 'stopping program'
                close_position()
            print("---Ending Trading--")
            break

    program_notification("Arrêt du programme : "+Settings.program_name)






if __name__=='__main__':
    main()

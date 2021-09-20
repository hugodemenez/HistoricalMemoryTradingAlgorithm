import csv


class csv_generator:    
    
    def __init__(self,):
        # csv header
        fieldnames = ['crypto', 'price','potential_yield']
        self.dictionnary_list = []
        
        while(True):
            self.generate_dictionnary()
            
            if input("Do you have more (Y)es or (N)o :") in ['N','n']:
                break
        

        with open('supports.csv', 'w', encoding='UTF8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.dictionnary_list)    
        
    def generate_dictionnary(self) -> None:
        crypto = input("crypto :")
        price = input("price :")
        potential_yield = input("potential_yield in % :")
        try:
            self.dictionnary_list.append({'crypto': str(crypto),'price': float(price),'potential_yield': 1+float(potential_yield)/100})
        except Exception as error:
            print(f"Wrong input format  {error}")
            
        
class csv_reader:
    def __init__(self):
        pass
    
    def file_to_dict_list(self) -> list[dict]:
        supports=[]
        with open('supports.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                supports.append(row)
                
        return supports
        
        
            
if __name__=="__main__":
    print(csv_reader().file_to_dict_list())
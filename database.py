import mysql.connector

class Database:
    def __init__(self):
        pass
    
    def database_request(self,sql,params=None,commit=False):
        self.database = mysql.connector.connect(
                host="localhost",
                user="hugodemenez",
                password="Manonhugo147",
                database="trading",
                auth_plugin='mysql_native_password',
                )
        self.cursor = self.database.cursor(buffered=True)
        self.cursor.execute(sql,params)
        if commit:
            self.database.commit()

        return self.cursor
from mysql.connector import MySQLConnection, OperationalError

class sql(MySQLConnection):

    def cursor(self, **kwargs):
        try:
            c = super().cursor(**kwargs)
        except OperationalError:
            try:
                super().reconnect()
                c = super().cursor(**kwargs)
            except Exception as e: 
                raise e
        except Exception as e: 
            raise e
        return c


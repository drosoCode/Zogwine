from mysql.connector import MySQLConnection, OperationalError

class sql(MySQLConnection):

    def cursor(self, **kwargs):
        kwargs.update({'dictionary': True, 'buffered': True})
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


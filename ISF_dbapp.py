import pymysql

def connectDB(db_name: str) -> pymysql.connections.Connection:
    # prompt user for the MySQL username and password
    username = input("Enter username: ")
    pword = input("Enter password: ")

    # Use the user provided username and password values to connect to the database
    try:
        connection = pymysql.connect(
            host= "localhost",
            user=username,
            password= pword,
            database = db_name,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit = True)
        
        print("--------------------------")
        print("Connected to", db_name)
        print("--------------------------")
        return connection

    except RuntimeError as e:
        print("Error: ", e.args[0]) 
        # print("Wrong auth or cryptography package not installed")
        return connectDB(db_name)

    except pymysql.Error as e:
        code, msg = e.args
        print ("Cannot connect to the database.", code, msg)
        print("Please try again")
        return connectDB(db_name)
    
    
def some_func(my_db: pymysql.connections.Connection):
    pass


def main():
    my_db = connectDB('music_chens') 

    try:
        some_func(my_db) 
    except pymysql.Error as e:
        print("Error: %d: %s" % (e.args[0], e.args[1]))
    finally:
        if my_db:
            my_db.close()
            print("--------------------------")
            print("Connection closed")
            print("--------------------------")

if __name__ == '__main__':
    main()

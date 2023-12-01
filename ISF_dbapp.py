import pymysql
import streamlit as st
import pandas as pd

def connectDB(db_name: str) -> pymysql.connections.Connection:
    # prompt user for the MySQL username and password
    # username = input("Enter username: ")
    username = "root"
    # pword = input("Enter password: ")
    pword = "Qwe^44983"

    # Use the user provided username and password values to connect to the database
    try:
        connection = pymysql.connect(
            host= "localhost",
            user=username,
            password= pword,
            database = db_name,
            cursorclass=pymysql.cursors.Cursor,
            # cursorclass=pymysql.cursors.DictCursor,
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
    

def get_table_names(my_db: pymysql.connections.Connection):
    cursor = my_db.cursor()
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    cursor.close()

    table_names = []
    for row in tables:
        print(row[0])
        table_names.append(row[0])
        # tables.append(list(row_dict.values())[0])
    return table_names

def get_column_names(my_db: pymysql.connections.Connection, table_name: str):
    cursor = my_db.cursor()
    cursor.execute("SHOW COLUMNS FROM " + table_name)
    cols = cursor.fetchall()
    cursor.close()

    col_names = []
    for row in cols:
        # columns.append(list(row_dict.values())[0])    # for dictionary cursor
        col_names.append(row[0])

    return col_names

def run_st_tab_view(my_db, table_names, table_keys):
    st.title("ISF Database App")
    
    # make a tab for each table
    tabs = st.tabs(table_names)

    for i, tab in enumerate(tabs):
        with tab:
            st.write("current table: ", table_names[i])
            editor, edits_key = make_df_editor(my_db, table_names[i], table_keys[i])
            # show what the user has modified
            show_edits(edits_key)
            # make a button, on click, update the database
            if st.button("Update database", key=table_names[i] + "_update_btn"):
                update_db(my_db, edits_key, table_names[i], table_keys[i])
                # refresh page, flush session state
                st.experimental_rerun()


def make_df_editor(my_db: pymysql.connections.Connection, table_name: str, table_key: str):
    data_df = st.session_state[table_key]
    edits_key = table_key + "_edits"

    # static table, won't update unless the DB is updated
    st.write("static table below")
    st.dataframe(st.session_state[table_key])
    
    # generate session key name for editable table
    st.write("Editable table below")
    
    # make a container for data editor
    df_container = st.empty()
    df_container.data_editor(st.session_state[table_key], key=edits_key, num_rows="dynamic")

    return df_container, edits_key

def update_db(my_db, edits_key: str, table_name: str, table_key: str):
    '''
    update the database with the session state

    params:
        my_db: pymysql.connections.Connection
        key: str, the key name of the session state
        st.session_state[key]:    {"edited_rows":{}, "added_rows":[], "deleted_rows":[]}
                                    edited_rows: {row_i: {"col_name": new_value}, ...}
                                    added_rows: [{col_name: new_value, ...}, ...]
                                    deleted_rows: [row_i, ...]
    '''
    if edits_key not in st.session_state:
        return
    
    edited_rows = st.session_state[edits_key]["edited_rows"]
    added_rows = st.session_state[edits_key]["added_rows"]
    deleted_rows = st.session_state[edits_key]["deleted_rows"]

    # update the database
    for row_i, edit in edited_rows.items():
        row_i = int(row_i)
        # st.write(f"row_i: {row_i}, edit: {edit}")
        # enumerate through the columns
        for col_name, new_value in edit.items():
            # st.write(f"edited field: {col_name}, new_value: {new_value}")
            try:
                new_value = int(new_value)
                # update the database
                mycursor = my_db.cursor()
                update_procedure = 'update_table_int'
                params = (table_name, col_name, new_value, row_i+1)
                mycursor.callproc(update_procedure, params)
                mycursor.close()
                st.session_state[table_key] = fetch_data(my_db, table_name)
            except ValueError:
                pass


def show_edits(edits_key):
    # print what the usert has modified
    st.write("Modifications:") 

    if edits_key in st.session_state:
        st.write(st.session_state[edits_key]) 
        # the above automatically refresh with each edit on page, not persistant


def fetch_data(my_db, table_name: str):
    col_names = get_column_names(my_db, table_name)

    # get data from the table
    mycursor = my_db.cursor()
    mycursor.execute(f"SELECT * FROM {table_name}")
    result = mycursor.fetchall()
    mycursor.close()

    # store data in a dataframe and display in table view
    data_df = pd.DataFrame(result, columns=col_names)

    return data_df

def set_table_sessions(my_db, table_names: list):
    table_keys = [table_name + "_df" for table_name in table_names]

    for ith, table_name in enumerate(table_names):
        if table_keys[ith] not in st.session_state:
            # store a dataframe in the session state
            st.session_state[table_keys[ith]] = fetch_data(my_db, table_name)

    return table_keys
    

def main():
    disconnect = False
    my_db = connectDB('playground') 
    try:
        table_names = get_table_names(my_db) 
        table_keys = set_table_sessions(my_db, table_names)
        # print(table_names)
        run_st_tab_view(my_db, table_names, table_keys)
        # tryout()

    except pymysql.Error as e:
        print("Error: %d: %s" % (e.args[0], e.args[1]))

    finally:
        if (my_db is not None) & (disconnect == True):
            my_db.close()
            print("--------------------------")
            print("Connection closed")
            print("--------------------------")

if __name__ == '__main__':
    main()

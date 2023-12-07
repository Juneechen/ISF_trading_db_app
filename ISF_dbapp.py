import pymysql
import pandas as pd
import streamlit as st

import isf_config as config 

def get_table_names(my_db: pymysql.connections.Connection):
    cursor = my_db.cursor()
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    cursor.close()

    table_names = []
    for row in tables:
        # print(row[0])
        table_names.append(row[0])
        # tables.append(list(row_dict.values())[0])
    return table_names

def get_field_names(my_db: pymysql.connections.Connection, table_name: str):
    cursor = my_db.cursor()
    cursor.execute("SHOW COLUMNS FROM " + table_name)
    cols = cursor.fetchall()
    cursor.close()

    col_names = []
    for row in cols:
        # columns.append(list(row_dict.values())[0])    # for dictionary cursor
        col_names.append(row[0])

    return col_names


def show_edits(edits_key):
    # print what the usert has modified
    st.write("Modifications:") 

    if edits_key in st.session_state:
        st.write(st.session_state[edits_key]) 
        # the above automatically refresh with each edit on page, not persistant


def fetch_data(my_db, table_name: str):
    col_names = get_field_names(my_db, table_name)

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


def commit_delete(my_db, table_name: str, table_key: str, deleted_rows: list):
    '''
    params:
        table_name: str, name of the table to be deleted from
        table_key: str, the key name of the session state, for retrieving the pk value from dataframe before deletion
        deleted_rows: [row_i, ...]
    
    '''
    did_not_delete = []
    error_msg = []
    mycursor = my_db.cursor()

    # retrieve the pk field name of this table
    pk_col = config.TABLE_PK[table_name]

    for row_i in deleted_rows:
        pk_val = st.session_state[table_key].iloc[row_i][pk_col]
        try:
            procedure_name = config.PROCEDURES['delete']
            params = (table_name, pk_col, pk_val)
            mycursor.callproc(procedure_name, params)
            print(f"deleted from {table_name} where {pk_col} = {pk_val}")
        except pymysql.Error as e:
            code, msg = e.args
            did_not_delete.append(f"{pk_col} = {pk_val}")
            error_msg.append(f"Error: {msg}")
    
    mycursor.close()
    return did_not_delete, error_msg


def commit_update(my_db, table_name: str, table_key: str, edited_rows: dict):
    '''
    params:
        table_name: name of the table to be updated
        table_key: str, the key for retrieving the pk field name and value of the edited row
        edited_rows: {row_i: {col_name: new_value, ...}, ...}
    '''
    did_not_update = []
    error_msg = []
    mycursor = my_db.cursor()

    # retrieve the pk field name of this table
    pk_field_name = config.TABLE_PK[table_name]
    procedure_name = config.PROCEDURES['update']

    # update the database for each modified tuple (row)
    for row_i, edit in edited_rows.items():
        row_i = int(row_i)
        # enumerate through the modified fields
        for field, new_value in edit.items():
            pk_val = st.session_state[table_key].iloc[row_i][pk_field_name]

            try:
                print(f"updating {table_name} set {field} = {new_value} where {pk_field_name} = {pk_val}")
                params = (table_name, field, new_value, pk_field_name, pk_val)
                mycursor.callproc(procedure_name, params)

            except pymysql.Error as e:
                print(f"failed to update {table_name} set {field} = {new_value} where {pk_field_name} = {pk_val}")
                code, msg = e.args
                did_not_update.append(f"{field} = {new_value} where {pk_field_name} = {pk_val}")
                error_msg.append(f"Error: {msg}")
                    
    mycursor.close()
    return did_not_update, error_msg

def commit_insert(my_db, table_name: str, table_key: str, added_rows: list):
    '''
    params:
        added_rows: a list of dictionaries, each dictionary is a row to be inserted; 
                    field where value is not specified will not be present in the dictionary. 
                    format:
                    "added_rows":[
                        0:{
                            "p_name":"sweet shrimp 150 g"
                            "category":"Frozen"
                            "sell_price":10
                        }, ...
                    ]
    '''
    did_not_insert = []
    error_msg = []
    mycursor = my_db.cursor()

    # retrieve all column names (or editable column names) of the table
    table_fields = get_field_names(my_db, table_name)

    # for each added row, retrieve the new value for each column if specified, otherwise use None
    for row in added_rows:
        params = []
        for field_name in table_fields:
            if field_name in row:
                params.append(row[field_name])
            else:
                params.append(None)
        # call the procedure to insert the row
        params = tuple(params)
        try:
            procedure_name = config.PROCEDURES['create'] + table_name
            mycursor.callproc(procedure_name, params)
        except pymysql.Error as e:
            code, msg = e.args
            did_not_insert.append(params)
            error_msg.append(f"Error: {msg}")
    
    # update the static df stored in session state with the latest data from the DB using key = table_key
    # st.session_state[table_key] = fetch_data(my_db, table_name)

    mycursor.close()
    return did_not_insert, error_msg

def update_db(my_db, edits_key: str, table_name: str, table_key: str):
    '''
    commit front-end eidts to DB with edits stored in session state

    params:
        my_db: pymysql.connections.Connection
        edits_key: the key for retrieving edits from session state
        table_name: name of the table to be updated
        table_key: the key for retrieving the static before-change dataframe from session state
    '''
    if edits_key not in st.session_state:
        return
    
    all_sussess = True # for indicating whether all changes were successful

    edited_rows = st.session_state[edits_key]["edited_rows"]
    added_rows = st.session_state[edits_key]["added_rows"]
    deleted_rows = st.session_state[edits_key]["deleted_rows"]

    failed_updates, update_error = commit_update(my_db, table_name, table_key, edited_rows)
    failed_inserts, insert_errors = commit_insert(my_db, table_name, table_key, added_rows)
    failed_deletes, delete_errors = commit_delete(my_db, table_name, table_key, deleted_rows)

    if len(failed_updates) > 0:
        all_sussess = False
        for i, row in enumerate(failed_updates):
            st.error(f"Failed to set {row}. {update_error[i]}")

    if len(failed_inserts) > 0:
        all_sussess = False
        for i, row in enumerate(failed_inserts):
            st.error(f"Failed to insert {row}. {insert_errors[i]}")
    
    if len(failed_deletes) > 0:
        all_sussess = False
        for i, row in enumerate(failed_deletes):
            st.error(f"Failed to delete {failed_deletes[i]}. {delete_errors[i]}")


    # mycursor.callproc(update_procedure, params)
    # mycursor.close()
    st.session_state[table_key] = fetch_data(my_db, table_name)

    # return True to automatically refresh the tab
    # return False to let failure messages stay on page and warn user to manually refresh
    return all_sussess

# make a button, on click, update the database        
def show_update_btn(my_db, table_name, edits_key, table_key):
    if st.button(f"Commit Changes", key=table_name + "_update_btn"):
        all_sussess = update_db(my_db, edits_key, table_name, table_key)
        if all_sussess:
            # refresh tab, flush session state, 
            # other tabs need to be refreshed manually to see cascading changes
            st.rerun()
        else:
            st.warning("Some changes were not successful. Please refresh page to see the latest data.")

def run_st_tab_view(my_db, table_names, table_keys):
    st.title("ISF Seafood Trading - Admin Portal")
    tabs = st.tabs(table_names) # make a tab for each table

    for i, tab in enumerate(tabs):
        with tab:
            # manual tab refresh button
            if st.button(f"click to see cascading changes if you have modified any other tab", 
                         key=table_names[i] + "_refresh_btn"):
                # update static df
                st.session_state[table_keys[i]] = fetch_data(my_db, table_names[i])
                st.rerun()
            
            if table_names[i] in config.VIEW_ONLY_TABLES: 
                st.dataframe(st.session_state[table_keys[i]])

            else:
                edits_key = make_editable_table(my_db, table_names[i], table_keys[i])
                # show_edits(edits_key)
                show_update_btn(my_db, table_names[i], edits_key, table_keys[i])

# connect to a remote database with stored credentials on the cloud and return the connection object
def connectRemoteHost() -> pymysql.connections.Connection:
    try:
        connection = pymysql.connect(
            host = st.secrets["DB_HOST"],
            port = st.secrets["DB_PORT"],
            user = st.secrets["DB_USER"],
            password = st.secrets["DB_PASSWORD"],
            database = st.secrets["DB_NAME"],
            cursorclass =pymysql.cursors.Cursor,
            # cursorclass=pymysql.cursors.DictCursor,
            autocommit = True)

        print(">>> Connected to remote DB <<<")
        print("-----------------------------------------")
        return connection
    
    except pymysql.Error as e:
        code, msg = e.args

        # print(f"Connection to {config.DB_NAME} failed. Please try again.")
        print(f"Connection to {config.DB_NAME} failed. Please contact the host for credentials.")
        print(f"Error code: {code}, Error message: {msg}")
        print("-----------------------------------------")
        
        return None
    

def make_editable_table(my_db, table_name, table_key):
    edits_key = table_name + "_edits"
    mycursor = my_db.cursor()
    config_dict = {}
    
    if table_name in config.TABLE_WITH_DROPDOWN:
        fk_cols = []
        options = []
        for fk_col, referenced_pk, referenced_table in config.TABLE_WITH_DROPDOWN[table_name]:
            fk_cols.append(fk_col)
            mycursor.callproc(config.PROCEDURES['get_col'], (referenced_pk, referenced_table))
            result = mycursor.fetchall()
            options.append([row[0] for row in result])

        for i, fk_col in enumerate(fk_cols):
            config_dict[fk_col] = st.column_config.SelectboxColumn(width="medium", 
                                                                            options=options[i],required=True,)
    
    # make a data_editor with selectbox column, make each fk_col a key in column_config
    st.data_editor(st.session_state[table_key], key=edits_key, num_rows="dynamic", 
                    disabled=config.VIEW_ONLY_COLS[table_name], 
                    column_config=config_dict)
    
    return edits_key

def manual_tab_refresh_btn(my_db, table_name):
    table_key = table_name + "_df"
    if st.button(f"click to see cascading changes if you have modified any other tab", 
                         key=table_name + "_refresh_btn"):
        # update static df
        st.session_state[table_key] = fetch_data(my_db, table_name)
        st.rerun()

def tab_plus_selectbox_view(my_db, table_names, table_keys):
    st.title("ISF Seafood Trading - Admin Portal")
    # make 3 tabs, one for VIEW_ONLY_TABLES, one for EDITABLE_TABLES, one for 'Visual Analytics'
    view_only_tab, editable_tab, analytics_tab = st.tabs(["View Only Tales", "Editable Tables", "Visual Analytics"]) 
    
    with view_only_tab:
        # make a dropdown sidebar for each table, select one to view
        table_name = st.selectbox("Select a table to view", config.VIEW_ONLY_TABLES)
        st.dataframe(st.session_state[table_name + "_df"]) # key for static df
    
    with editable_tab:
        # make a radio button for each table, select one to edit
        table_name = st.selectbox("Select a table to edit", config.EDITABLE_TABLES)
        edits_key = make_editable_table(my_db, table_name, table_name + "_df")
        show_update_btn(my_db, table_name, edits_key, table_name + "_df")
        manual_tab_refresh_btn(my_db, table_name)

    with analytics_tab:
        st.write("Coming soon...")


def main():
    disconnect = False

    # # check for command line arguments, if 'local' is passed, connect to local db, otherwise connect to remote db
    # if len(sys.argv) > 1 & (sys.argv[1] == 'local'):
    #     my_db = auth.connectLocalDB(config.DB_NAME)
    # else:
    #     my_db = connectRemoteHost()

    # connect to remote hosted database using credentials stored in secrets.toml on the cloud
    my_db = connectRemoteHost()

    try:
        table_names = get_table_names(my_db) 
        table_keys = set_table_sessions(my_db, table_names)
        # st.sidebar.title("ISF Seafood Trading - Admin Portal")
        # run_st_tab_view(my_db, table_names, table_keys)
        tab_plus_selectbox_view(my_db, table_names, table_keys)
        


    except pymysql.Error as e:
        print("Error: %d: %s" % (e.args[0], e.args[1]))

    finally:
        if (my_db is not None) & (disconnect == True):
            my_db.close()
            print("--------------------------")
            print("Connection closed")
            print("--------------------------")

if __name__ == '__main__':
    print("rerun main():")
    main()

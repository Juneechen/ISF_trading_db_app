import pymysql
import pandas as pd
import streamlit as st
import time

import isf_config as config 

# cache database connection
@st.cache_resource
# connect to the remote hosted MySQL database using streamlit.secrets
def connectDB(db_name) -> pymysql.connections.Connection:
    try: 
        connection = pymysql.connect(
            host = st.secrets["DB_HOST"],
            port = st.secrets["DB_PORT"],
            user = st.secrets["DB_USER"],
            password = st.secrets["DB_PASSWORD"],
            database = st.secrets["DB_NAME"],
            # database = db_name,
            cursorclass =pymysql.cursors.Cursor,
            # cursorclass=pymysql.cursors.DictCursor,
            autocommit = True)

        print(">>> Connected to local", db_name, "<<<")
        print("-----------------------------------------")
        return connection
    except pymysql.Error as e:
        code, msg = e.args
        print(f"Connection to {db_name} failed. Please try again.")
        print(f"Error code: {code}, Error message: {msg}")
        print("-----------------------------------------")
        return None
    

# display sidebar for selecting role and entering password
def verifyRole(role):
    if role in st.session_state: # already verified for this session
        if st.session_state[role] == True: # can be False if logged out
            return True
    
    role_verified = False
    with st.sidebar.container():
        input_container = st.empty()
        btn_container = st.empty()
    role_password = input_container.text_input(f"Enter password: ", type="password", help=f'enter: "{role}pwd"')
    if btn_container.button("Verify"):
        role_verified = (role_password == st.secrets[role]) 
    if role_verified:
        input_container.empty()
        btn_container.empty()
        st.session_state[role] = True
    return role_verified

# render content for a verified role
def renderContentFor(role, my_db, table_names, table_keys):
    renderMsgFor(role)
    if role == 'admin':
        admin_content(my_db, table_names, table_keys)
    elif role == 'delivery':
        table_name = 'delivery'
        edits_key = delivery_management(my_db, table_name, table_name + "_df")
        update_btn(my_db, table_name, edits_key, table_name + "_df")
        manual_rerender_btn(my_db, table_name)
    elif role == 'analytics':
        analytics_content(my_db)
    else:
        devopsContent(my_db)

def renderMsgFor(role):
    '''render a message for the verified role in the sidebar'''
    with st.sidebar.container():
        st.success(f"Verified! Logged in as {role} staff.")
        if role == 'admin':
            st.write("View only tables:")
            st.write("- customer related tables")
            st.write("- managed by the customer site")
            # st.write("", config.VIEW_ONLY_TABLES)
            st.write("Editable tables:")
            st.write("- editable fields: marked with a pen icon")
            st.write("- view-only fields: auto-incremented ids")
            # st.write("", config.EDITABLE_TABLES)
        elif role == 'delivery':
            pass # add as needed
        elif role == 'analytics':
            pass # add as needed
        else:
            st.write("For testing features 🛠️")


def fetch_data(my_db, table_name: str):
    '''fetch a table from the database and return a dataframe'''
    col_names = get_fields(my_db, table_name)
    mycursor = my_db.cursor()
    mycursor.execute(f"SELECT * FROM {table_name}")
    result = mycursor.fetchall()
    mycursor.close()
    return pd.DataFrame(result, columns=col_names)

def set_table_sessions(my_db, table_names: list):
    '''define a key for each table to retrieve the dataframe from session state'''
    table_keys = [table_name + "_df" for table_name in table_names] # 

    for ith, table_name in enumerate(table_names):
        if table_keys[ith] not in st.session_state:
            # store a dataframe in the session state
            st.session_state[table_keys[ith]] = fetch_data(my_db, table_name)

    return table_keys

def get_table_names(my_db: pymysql.connections.Connection):
    '''get a list of table names from the database'''
    cursor = my_db.cursor()
    cursor.execute("SHOW TABLES")
    res = cursor.fetchall()
    cursor.close()
    table_names = [each[0] for each in res]
    return table_names


def get_fields(my_db: pymysql.connections.Connection, table_name: str):
    '''get a list of field names from the database for a given table'''
    cursor = my_db.cursor()
    cursor.execute("SHOW COLUMNS FROM " + table_name)
    res = cursor.fetchall() 
    cursor.close()
    return [each[0] for each in res] # a list of field names


def commit_delete(my_db, table_name: str, table_key: str, deleted_rows: list):
    '''
    params:
        table_key: the key for retrieving the data before deletion from session state
        deleted_rows: [row_i, ...]
    
    '''
    did_not_delete = []
    error_msg = []
    mycursor = my_db.cursor()
    pk_col = config.TABLE_PK[table_name] #  pk field name of this table

    for row_i in deleted_rows:
        pk_val = st.session_state[table_key].iloc[row_i][pk_col]
        try:
            procedure_name = config.PROCEDURES['delete']
            params = (table_name, pk_col, pk_val)
            mycursor.callproc(procedure_name, params)
            print(f"deleted from {table_name} where {pk_col} = {pk_val}") # for debugging
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

    pk_field_name = config.TABLE_PK[table_name]
    procedure_name = config.PROCEDURES['update']

    # update the database for each modified tuple (row)
    for row_i, edit in edited_rows.items():
        row_i = int(row_i)
        pk_val = st.session_state[table_key].iloc[row_i][pk_field_name]
        # enumerate through the modified fields for this tup;e
        for field, new_value in edit.items():
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
    added_rows: a list of dictionaries, each dictionary is a row to be inserted; 
                fields that are not filled-in will not be in the dictionary. 

                "added_rows":[
                    0:{field1: value1, ...},
                    1:{field1: value1, field3: value3, ...}, 
                    ...
                ]
    '''
    # retrieve all column names (or editable column names) of the table
    table_fields = get_fields(my_db, table_name)
    did_not_insert = []
    error_msgs = []

    mycursor = my_db.cursor()
    for row in added_rows: # retrive new values for each tuple, 
        params = [row.get(field, None) for field in table_fields] # None for fields that are not filled-in (not in the dictionary)
        params = tuple(params) # for calling the procedure
        try:
            procedure_name = config.PROCEDURES['create'] + table_name
            mycursor.callproc(procedure_name, params)
        except pymysql.Error as e:
            code, msg = e.args
            did_not_insert.append(params)
            error_msgs.append(f"Error: {msg}")
    
    # update the static df stored in session state with the latest data from the DB using key = table_key
    # st.session_state[table_key] = fetch_data(my_db, table_name)
    mycursor.close()
    return did_not_insert, error_msgs

def update_db(my_db, edits_key: str, table_name: str, table_key: str):
    '''
    commit front-end eidts to DB with edits stored in session state.

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

    st.session_state[table_key] = fetch_data(my_db, table_name) # update the static df stored in session state with the latest data from DB
    return all_sussess

# make a button, on click, update the database        
def update_btn(my_db, table_name, edits_key, table_key):
    '''make a button, on click, try update DB with edits stored in session state'''
    if st.button(f"Commit Changes", key=table_name + "_update_btn"):
        all_sussess = update_db(my_db, edits_key, table_name, table_key)
        if all_sussess: # refresh tab
            st.success("All changes were successful.")
            time.sleep(3)
            st.rerun()
        else: # not to refresh so failure messages stay on page, user will have a button for manual refresh
            st.warning("Some changes were not successful. Please refresh page to see the latest data.")


def delivery_management(my_db, table_name: str, table_key: str):
    '''Render a data_editor for delivery management'''
    st.header("Delivery Management")
    st.info("Edit the expected data and delivery status for orders you're delivering")
    edits_key = "delivery_status_edits"
    mycursor = my_db.cursor()
    config_dict = {"expected_delivery_date": st.column_config.DatetimeColumn(required=True),
                    "delivery_status": st.column_config.SelectboxColumn(width="medium", 
                                                                        options=config.DELIVERY_STATUS,required=True,)}
    st.data_editor(st.session_state[table_key], key=edits_key, 
                        disabled=config.VIEW_ONLY_COLS["delivery_status"], 
                        column_config=config_dict)
        
        # retrieve count from session state with key for data in this table
    st.write("Total Records:", len(st.session_state[table_key]))
    mycursor.close()
    return edits_key

def make_editable_table(my_db, table_name, table_key):
    '''Render a data_editor for an editable table, apply pre-defined column_config'''
    edits_key = table_name + "_edits"
    mycursor = my_db.cursor()
    config_dict = {} # a dict of specs for cols with special formatting
    
    if table_name in config.TABLE_WITH_DROPDOWN:
        fk_cols = []
        options = []
        # for each fk_col, get the list of valid values from the referenced table
        for fk_col, referenced_pk, referenced_table in config.TABLE_WITH_DROPDOWN[table_name]:
            fk_cols.append(fk_col)
            # call the procedure to get the list of valid valuee given a referenced table and pk_field_name being referenced
            mycursor.callproc(config.PROCEDURES['get_col'], (referenced_pk, referenced_table))
            result = mycursor.fetchall()
            options.append([row[0] for row in result])

        for i, fk_col in enumerate(fk_cols):
            config_dict[fk_col] = st.column_config.SelectboxColumn(width="medium", 
                                                                            options=options[i],required=True,)
    
    # make a data_editor with selectbox column, each fk_col has a column_config for dropdown options
    st.data_editor(st.session_state[table_key], key=edits_key, num_rows="dynamic", 
                    disabled=config.VIEW_ONLY_COLS[table_name], 
                    column_config=config_dict)
    
    # retrieve count from session state with key for data in this table
    st.write("Total Records:", len(st.session_state[table_key]))
    mycursor.close()
    return edits_key

def manual_rerender_btn(my_db, table_name):
    '''make a button, on click, fetch latest data from DB, then re-render the component'''
    table_key = table_name + "_df"
    if st.button(f"Click to see cascading changes if you have modified any other table", 
                         key=table_name + "_refresh_btn"):
        # fetch latest data from DB into session state
        st.session_state[table_key] = fetch_data(my_db, table_name)
        st.rerun()

def analytics_content(my_db):
    '''render analytics content'''
    queries = ["Best Selling Products by Year", "Number of Orders per Customer"]
    sales_by_year, order_per_customer = st.tabs(queries)
    with sales_by_year:
        sales_analytics(my_db)
    with order_per_customer:
        order_analytics(my_db)

def admin_content(my_db, table_names, table_keys):
    '''render admin content'''
    st.title(config.SITE_NAME + " - Admin Portal")
    editable_tab, view_only_tab = st.tabs(["Editable Tables", "View Only Tables"]) # make tab components
    
    with editable_tab:
        # table_name dynamically changes with the selectbox
        table_name = st.selectbox("Select a table to edit", config.EDITABLE_TABLES)
        edits_key = make_editable_table(my_db, table_name, table_name + "_df")
        update_btn(my_db, table_name, edits_key, table_name + "_df")
        manual_rerender_btn(my_db, table_name)
    
    with view_only_tab:
        table_name = st.selectbox("Select a table to view", config.VIEW_ONLY_TABLES)
        st.dataframe(st.session_state[table_name + "_df"]) # key for static df
        st.write("Total Records:", len(st.session_state[table_name + "_df"]))
        manual_rerender_btn(my_db, table_name)

def order_analytics(my_db):
    '''render order analytics content generated by stored procedure'''
    mycursor = my_db.cursor()
    st.subheader("Number of Orders per Customer")
    mycursor.callproc(config.ANALYTICS["Number of Orders per Customer"], ())
    result = mycursor.fetchall() # a list of tuples (cid, email, num_orders)
    mycursor.close()
    # make the result a dataframe and display with chart view
    df = pd.DataFrame(result, columns=["cid", "email", "num_orders"])
    st.dataframe(df)
    st.bar_chart(df["num_orders"])

def sales_analytics(my_db):
    '''render sales analytics content generated by stored procedure'''
    title = "Best Selling Products by Year"
    st.subheader(title)
    in_year = st.text_input("Enter a year", value="2023")
    mycursor = my_db.cursor()
    mycursor.callproc(config.ANALYTICS[title], (in_year,))
    result = mycursor.fetchall()
    mycursor.close()
    # make the result a dataframe and display with chart view
    df = pd.DataFrame(result, columns=["Product", "Sold"])
    df["Sold"] = df["Sold"].apply(int)
    st.dataframe(df)
    st.bar_chart(df, x="Product", y="Sold")
    
def devopsContent(my_db):
    st.header("Features under development")
    st.info("Contact chen.shuju@northeastern.edu for any technical issues")
    # res = get_fields(my_db, 'customer')
    # st.write(res)

def log_out_btn(role):
    '''log the user out from a specific role'''
    with st.sidebar.container():
        if st.button("Log out"):
            st.session_state[role] = False
            verifyRole(role)
            st.rerun()

def main():
    disconnect = False
    # connect to remote hosted database using credentials stored in secrets.toml on the cloud
    my_db = connectDB(config.DB_NAME) # the connection will be cached for this specific db name so it will only connect once

    try:
        table_names = get_table_names(my_db) 
        table_keys = set_table_sessions(my_db, table_names)
        role = st.sidebar.selectbox("Select a role", ['admin', 'analytics', 'delivery', "devops"])
        verified = verifyRole(role) # if success, the role will be marked as verified for this session
        if verified:
            st.header("🍣 🦑 🐟 🐙 🦐")
            renderContentFor(role, my_db, table_names, table_keys)
            log_out_btn(role)
        else:
            st.info(f"Password: {st.secrets[role]} 🤫")
        
    except pymysql.Error as e:
        print("Error: %d: %s" % (e.args[0], e.args[1]))

    finally:
        if (my_db is not None) & (disconnect == True):
            my_db.close()
            print("--------------------------")
            print("Connection closed")
            print("--------------------------")

if __name__ == '__main__':
    print("rerun main()")
    main()

import pymysql
import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd

import auth as auth
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

# make procedure for this
def fetch_categories(my_db: pymysql.connections.Connection):
    st.write("fetching categories from server")
    cursor = my_db.cursor()
    cursor.execute("SELECT category_name FROM category")
    categories = cursor.fetchall()
    cursor.close()
    categories = [category[0] for category in categories]
    return categories

    # st.write("fetching categories from session state")
    # if "category_df" in st.session_state:
    #     return st.session_state["category_df"]["category_name"].tolist() #static

# make procedure for this
def fetch_partners(my_db: pymysql.connections.Connection):
    st.write("fetching partners from server")
    cursor = my_db.cursor()
    cursor.execute("SELECT partner_id FROM delivery_partner")
    partners = cursor.fetchall()
    cursor.close()
    partners = [partner[0] for partner in partners] 
    return partners


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



def make_editor(my_db: pymysql.connections.Connection, table_name: str, table_key: str):
    data_df = st.session_state[table_key]
    edits_key = table_name + "_edits"

    # static table, won't update unless the DB is updated
    st.write("static data in the current session:")
    st.dataframe(st.session_state[table_key])
    
    # generate session key name for editable table
    st.write("Editable view:")
    
    df_container = st.empty()
    if table_name == "product":
        df_container.data_editor(st.session_state[table_key], key=edits_key, num_rows="dynamic", 
                                 disabled=config.VIEW_ONLY_COLS[table_name], 
                                 column_config={"category": st.column_config.SelectboxColumn(
                                                        "Product Category",
                                                        width="medium",
                                                        options=fetch_categories(my_db),
                                                        required=True,
                                                    )
                                                }
                                )
    elif table_name == "delivery_zone":
        df_container.data_editor(st.session_state[table_key], key=edits_key, num_rows="dynamic",
                                 column_config={"category": st.column_config.SelectboxColumn(
                                                        "Assigned Delivery Partner (ID)",
                                                        disabled=config.VIEW_ONLY_COLS[table_name], 
                                                        width="medium",
                                                        options=fetch_partners(my_db),
                                                        required=True,
                                                    )
                                                }
                                )

    else:
        df_container.data_editor(st.session_state[table_key], 
                                 disabled=config.VIEW_ONLY_COLS[table_name], 
                                 key=edits_key, num_rows="dynamic")

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

    # update the database for each modified tuple
    for row_i, edit in edited_rows.items():
        row_i = int(row_i)
        # st.write(f"row_i: {row_i}, edit: {edit}")
        # enumerate through the columns
        for col_name, new_value in edit.items():
            # st.write(f"edited field: {col_name}, new_value: {new_value}")
            pk = st.session_state[table_key].iloc[row_i][config.TABLE_PK[table_name]]

            # update the database
            mycursor = my_db.cursor()

            # try update DB, catch Error
            try:
                # hardcoded for now, probably need some SQL procedures or functions here
                if table_name == "product":
                    if col_name == "sell_price":
                        new_value = int(new_value)
                        update_procedure = 'update_product_price'
                    else:
                        update_procedure = 'update_product'
                    params = (table_name, col_name, new_value, pk)
                    mycursor.callproc(update_procedure, params)
                else:
                    mycursor.execute(f"UPDATE {table_name} SET {col_name} = '{new_value}' WHERE {config.TABLE_PK[table_name]} = '{pk}'")

            except pymysql.Error as e:
                code, msg = e.args
                msg2 =f"Modification interupted by {col_name} = '{new_value}'. \nPlease refresh page to see the latest data."
                mycursor.close()
                return False, f"{msg2} Error: {code} {msg}"

            # mycursor.callproc(update_procedure, params)
            mycursor.close()
            st.session_state[table_key] = fetch_data(my_db, table_name)

    # if all successful, return True
    return True, 'success'
            


def run_st_tab_view(my_db, table_names, table_keys):
    st.title("ISF Database App")
    
    # make a tab for each table
    tabs = st.tabs(table_names)

    for i, tab in enumerate(tabs):
        with tab:
            st.write("current table: ", table_names[i])

            # manual refresh button
            if st.button(f"click to see cascading changes if you have modified any other tab", 
                         key=table_names[i] + "_refresh_btn"):
                # update static df
                st.session_state[table_keys[i]] = fetch_data(my_db, table_names[i])
                st.rerun()

            editor, edits_key = make_editor(my_db, table_names[i], table_keys[i])
            # show what the user has modified
            show_edits(edits_key)
            # make a button, on click, update the database
            if st.button(f"Update {table_names[i]}", key=table_names[i] + "_update_btn"):
                success, message = update_db(my_db, edits_key, table_names[i], table_keys[i])
                if success:
                    # refresh tab, flush session state, other tabs need to be refreshed manually to see cascading changes
                    st.rerun()
                else:
                    st.error(message)
                    

def main():
    disconnect = False
    my_db = auth.connectDB(config.DB_NAME)
    try:
        table_names = get_table_names(my_db) 
        table_keys = set_table_sessions(my_db, table_names)
        run_st_tab_view(my_db, table_names, table_keys)

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

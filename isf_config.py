# This file contains the configuration for the ISF application and information about the data schema.
DB_NAME = "seafood_service_v3"

SECRET_DIR = ".streamlit"
SECRET_FILE = ".streamlit/secrets.toml"

VIEW_ONLY_TABLES = ['customer', 'order_invoice', 'order_item']

TABLE_WITH_DROPDOWN = ['product', 'delivery_zone']

TABLE_PK = {'category': 'category_name', 
            'coupon': 'coupon_code', 
            'customer': 'cid', 
            'delivery_partner': 'partner_id',
            'delivery_zone': 'area_id',
            'order_id': 'invoice_id',
            'payment': 'payment_type',
            'product': 'pid'}

# True means all columns are view only, False means all columns are editable
VIEW_ONLY_COLS = {'product': ['pid', 'qty_in_stock'], 
                  'delivery_partner': ['partner_id'],
                  'delivery_zone': False,
                  'category': False,
                  'coupon': False,
                  'payment': False,
                  'customer': True,
                  'order_invoice': True,
                  'order_item': True}

# names of the procedures to call for CRUD operations
PROCEDURES = {'create': 'add_to_',  # I'll call add_to_<table_name> (params: all fields) for create operations
              'read': 'read_table', # read_table(table_name). This might need to be function as it will return things.
              'update': 'updata_table', # update_table(table_name, a_single_field, new_value, pk_value). 
              'delete': 'delete_from'} # delete_from(table_name, pk_field_name, pk_value)



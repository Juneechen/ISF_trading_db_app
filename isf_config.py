# This file contains the configuration for the ISF application and information about the data schema.

# All tables:
# `category`, `coupon`, `customer`, `delivery`, `delivery_partner`, `delivery_zone`, `order_invoice`, 
# `order_item`, `payment`, `product`, `vendor`, `vendor_supplies_seafood_product`

DB_NAME = "seafood_service_v4"

DB_HOST="db-mysql-nyc1-26951-do-user-14685697-0.c.db.ondigitalocean.com"
DB_PORT=25060
DB_USER="doadmin"
DB_PASSWORD="AVNS_ZxAXLPDXSco1qchGFKp"
DB_NAME="seafood_service_v4"

SECRET_DIR = ".streamlit"
SECRET_FILE = ".streamlit/secrets.toml"

VIEW_ONLY_TABLES = ['customer', 'order_invoice', 'order_item', 'delivery', 'vendor_supplies_seafood_product']

TABLE_WITH_DROPDOWN = ['product', 'delivery_zone']

TABLE_PK = {'category': 'category_name', 
            'coupon': 'coupon_code', 
            'customer': 'cid', 
            'delivery_partner': 'partner_id',
            'delivery_zone': 'area_id',
            'payment': 'payment_type',
            'product': 'pid',
            'vendor': 'vendor_id',
            'vendor_supplies_seafood_product': 'vendor_id'}

# True means all columns are view only, False means all columns are editable
VIEW_ONLY_COLS = {'product': ['pid', 'qty_in_stock'], 
                  'category': False,
                  'coupon': False,
                  'customer': True,
                  'delivery': True,
                  'delivery_zone': False,
                  'delivery_partner': ['partner_id'],
                  'payment': False,
                  'order_invoice': True,
                  'order_item': True,
                  'vendor': ['vendor_id'],
                  'vendor_supplies_seafood_product': True} # temporary set to uneditable


# names of the procedures to call for CRUD operations
PROCEDURES = {'create': 'insert_',  # call insert_<table_name> (params: all fields) for create operations
              'read': 'read_table', # read_table(table_name). This might need to be function as it will return things.
              'update': 'update_table', # update_table(tablename_p, field_p, new_val_p, pk_field_p, pk_val_p)
              'delete': 'delete_from'} # delete_from(table_name, pk_field_name, pk_value)



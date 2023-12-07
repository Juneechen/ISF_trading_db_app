# This file contains the configuration for the ISF application and information about the data schema.

# All tables:
# `category`, `coupon`, `customer`, `delivery`, `delivery_partner`, `delivery_zone`, `order_invoice`, 
# `order_item`, `payment`, `product`, `vendor`, `vendor_supplies_seafood_product`

# https://seafoodtradingco.streamlit.app/
DB_NAME = "seafood_service_v4"

# DB_HOST="db-mysql-nyc1-26951-do-user-14685697-0.c.db.ondigitalocean.com"
# DB_PORT=25060
# DB_NAME="seafood_service_v4"

SECRET_DIR = ".streamlit"
SECRET_FILE = ".streamlit/secrets.toml"

SITE_NAME = "Seafood Trading Co."

VIEW_ONLY_TABLES = ['customer', 'order_invoice', 'order_item', 'delivery', 'vendor_supplies_seafood_product']
EDITABLE_TABLES = ['category', 'coupon', 'delivery_partner', 'delivery_zone', 'payment', 'product', 'vendor']

# TABLE_WITH_DROPDOWN = ['product', 'delivery_zone', 'vendor_supplies_seafood_product']

# a dictionary of table_with_dropdown: [(fk_col, referenced_pk, referenced_table), ...]
TABLE_WITH_DROPDOWN = {'product': [('category', 'category_name', 'category')],
                       'delivery_zone': [('partner_id', 'partner_id', 'delivery_partner')]
                    #    'vendor_supplies_seafood_product': [('vendor_id', 'vendor_id', 'vendor'), 
                    #                                        ('pid', 'pid', 'product')]
                    }   


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


# names of the procedures to call for CRUD and other operations
PROCEDURES = {'create': 'insert_',  # call insert_<table_name> (params: all fields) for create operations
              'read': 'read_table', # read_table(table_name). This might need to be function as it will return things.
              'update': 'update_table', # update_table(tablename_p, field_p, new_val_p, pk_field_p, pk_val_p)
              'delete': 'delete_from',  # delete_from(table_name, pk_field_name, pk_value)
              'get_col': 'get_all',  # get_all(col_name, table_name)
              'Number of Orders per Customer': 'count_order_per_cid' # count_order_by_cid()
              } 

# names of the analytics procedures
ANALYTICS = {'Number of Orders per Customer': 'count_order_per_cid' # count_order_by_cid()
                        
                        }

# names of the procedures to call for CRUD and other operations
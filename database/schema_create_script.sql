drop database if exists seafood_service_v4;
create database seafood_service_v4;
use seafood_service_v4;

DROP TABLE IF EXISTS vendor;
CREATE TABLE vendor ( 
	vendor_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(64) NOT NULL,
	last_name VARCHAR(64) NOT NULL,
	phone_number CHAR(11) NOT NULL,
	steet_number VARCHAR(10) NOT NULL,
	street_name VARCHAR(64) NOT NULL,
	city VARCHAR(25) NOT NULL,
	state CHAR(2) NOT NULL,
	zip CHAR(5) NOT NULL
);
insert into vendor values 
	(1, 'Jane', 'Smith', '5551234567', '123', 'Main St', 'Boston', 'MA', '02115'),
	(2, 'Mark', 'Anderson', '1235557890', '14', 'Main St', 'Portland', 'ME', '04101'),
	(3, 'Lisa', 'Miller', '9876543210', '567', 'Elm St', 'Portland', 'ME', '04102'),
	(4, 'Christopher', 'Wilson', '1112223333', '890', 'Oak St', 'Portland', 'ME', '04103');

DROP TABLE IF EXISTS category;
CREATE TABLE category (
	category_name VARCHAR(64) NOT NULL PRIMARY KEY
);
insert into category values ('Frozen'), ('Fresh'), ('Non-Refrigerated'), ('Refrigerated');

DROP TABLE IF EXISTS product;
CREATE TABLE product (
	pid 	INT NOT NULL AUTO_INCREMENT,
	p_name	VARCHAR(64) NOT NULL UNIQUE,
    category VARCHAR(64) NOT NULL,
    sell_price	INT NOT NULL,
    p_description varchar(64) DEFAULT NULL,
    qty_in_stock INT NOT NULL DEFAULT 0,
    product_img varchar(64) NOT NULL,
    PRIMARY KEY (pid),
    FOREIGN KEY (category) REFERENCES category(category_name) 
		ON UPDATE CASCADE ON DELETE CASCADE
);
INSERT INTO product (p_name, category, sell_price, qty_in_stock, product_img) VALUES
    ('Sashimi Tuna 1 lb', 'Fresh', 30, 50, 'https://picsum.photos/200/300?random=550'),
    ('Frozen Salmon Filet 1 lb', 'Frozen', 25, 40, 'https://picsum.photos/200/300?random=554'),
    ('Sashimi Sweet Shrimp 150 g', 'Frozen', 15, 60, 'https://picsum.photos/200/300?random=170'),
    ('Sashimi Octopus', 'Frozen', 35, 30, 'https://picsum.photos/200/300?random=822'),
    ('Maine Uni 150 g', 'Fresh', 20, 45, 'https://picsum.photos/200/300?random=647');


DROP TABLE IF EXISTS vendor_supplies_seafood_product;
CREATE TABLE vendor_supplies_seafood_product ( 
	vendor_id INT NOT NULL,
    pid INT NOT NULL AUTO_INCREMENT,
    PRIMARY KEY (vendor_id, pid),
    price_per_qty FLOAT NOT NULL,
    FOREIGN KEY (vendor_id) REFERENCES vendor(vendor_id) 
		ON UPDATE CASCADE ON DELETE RESTRICT,
	FOREIGN KEY (pid) references product(pid) 
		ON UPDATE CASCADE ON DELETE RESTRICT
);
INSERT INTO vendor_supplies_seafood_product (vendor_id, pid, price_per_qty) VALUES
    (1, 5, 15.99),(1, 3, 12.50),(1, 2, 9.99),(1, 4, 18.75),(2, 5, 14.50);

-- individuals we contract, each is responsible for orders in some area (contains a group of 
drop table if exists delivery_partner;
create table delivery_partner(
	partner_id 	int primary key auto_increment not null,
    first_name 	varchar(15) not null,
    last_name 	varchar(15) not null,
    phone		CHAR(11) NOT NULL
);
INSERT INTO delivery_partner (first_name, last_name, phone) VALUES
    ('Alice', 'Johnson', '12345678901'),('Bob', 'Smith', '98765432109'),('Cathy', 'Williams', '87654321098');

-- collection of zip codes representing areas we can deliver to;
-- check order zipcode against this when order being placed
-- the assigned parner is responsible for all orders with a specific zipcode
drop table if exists delivery_zone;
create table delivery_zone(
	zipcode	CHAR(5) NOT NULL PRIMARY KEY,
    partner_id	int not null,
    FOREIGN KEY (partner_id) REFERENCES delivery_partner(partner_id)
		ON UPDATE CASCADE ON DELETE CASCADE
);
INSERT INTO delivery_zone (zipcode, partner_id) VALUES
    ('02114', 1),('02115', 1),('02116', 1),('04101', 2),('04102', 2),('04103', 2);

DROP TABLE IF EXISTS customer;
CREATE TABLE customer (
	cid 		INT NOT NULL AUTO_INCREMENT,
	c_fname		VARCHAR(64) NOT NULL,
    c_lname		VARCHAR(64) NOT NULL,
    email		VARCHAR(64) NOT NULL UNIQUE,
    pwd			VARCHAR(64) NOT NULL,	-- add mininum len requirement?
    phone		CHAR(11) NOT NULL,
    street		VARCHAR(64) NOT NULL,
    apt			VARCHAR(8),
    city 		VARCHAR(64) NOT NULL,
    state		VARCHAR(64) NOT NULL,
    zip			CHAR(5) NOT NULL,
    PRIMARY KEY (cid)
);

INSERT INTO customer (c_fname, c_lname, email, pwd, phone, street, apt, city, state, zip) VALUES
	('Daniel', 'Brown', 'daniel.brown@example.com', 'hashed_password', '87654321098', '789 Pine St', 'Apt 67', 'Boston', 'MA', '02102'),
    ('Jackson', 'Jones', 'jackson.jones@example.com', 'hashed_password', '65432109876', '567 Cedar St', 'Apt 34', 'Portland', 'ME', '04102'),
    ('John', 'Doe', 'john.doe@example.com', 'hashed_password', '12345678901', '123 Main St', 'Apt 45', 'Boston', 'MA', '02114');

drop table if exists coupon;
create table coupon(
	coupon_code varchar(10) primary key not null,
    coupon_discount_amt float not null default 0.10,
    coupon_expiration_date date default NULL,
    coupon_description varchar(64)
);

INSERT INTO coupon (coupon_code, coupon_discount_amt, coupon_expiration_date, coupon_description) VALUES
	('Happy25', 25, '2023-06-30', '25% off, enjoy your summer!'),
	('Summer10', 10, '2023-07-31', '10% off for early summer days'),
	('Spring20', 20, '2023-04-15', '20% off to welcome the spring'),
	('Winter15', 15, '2023-12-25', '15% off for winter holidays'),
	('Fall10', 10, '2023-09-30', '10% off for the autumn season'),
	('NewYear20', 20, '2024-01-01', '20% off to celebrate the New Year'),
	('Easter30', 30, '2023-04-09', '30% off for Easter'),
	('Thanks20', 20, '2023-11-24', '20% off for Thanksgiving'),
	('July4th15', 15, '2023-07-04', '15% off for Independence Day'),
	('LaborDay10', 10, '2023-09-04', '10% off for Labor Day'),
	('', 0, date('9999-01-01'), 'Default empty coupon.');


drop table if exists payment;
create table payment(
	payment_type varchar(16) primary key not null,
    img VARCHAR(64),
    payment_text VARCHAR(64),
    bg_color VARCHAR(64)
);

INSERT INTO payment(payment_type, img, payment_text, bg_color) VALUES 
	('Credit/Debit', '/credit.png', 'text-black', 'bg-green-200'),  
	('Venmo', '/venmo.png', 'text-white', 'bg-blue-600'),            
	('Zelle', '/zelle.png', 'text-white', 'bg-purple-600'),    
	('PayPal', '/paypal.png', 'text-black', 'bg-yellow-400');        

DROP TABLE IF EXISTS order_invoice;
CREATE TABLE order_invoice (
	order_id 	INT NOT NULL AUTO_INCREMENT,
    customer_id	INT NOT NULL,
    payment_type varchar(16) NOT NULL,
    coupon_code varchar(10) DEFAULT NULL,		-- limit 1 coupon per order for simpliciy
    order_date	DATETIME DEFAULT CURRENT_TIMESTAMP,		-- should be automatically generated, need to 
    PRIMARY KEY (order_id),
    FOREIGN KEY (customer_id) REFERENCES customer(cid) 
		ON UPDATE CASCADE ON DELETE CASCADE,
	FOREIGN KEY (payment_type) REFERENCES payment(payment_type) 
		ON UPDATE CASCADE ON DELETE RESTRICT,
	FOREIGN KEY (coupon_code) REFERENCES coupon(coupon_code) 
		ON UPDATE CASCADE ON DELETE RESTRICT
);

INSERT INTO order_invoice (customer_id, payment_type, coupon_code) VALUES
    (1, 'Venmo', 'Happy25'), (1, 'Venmo', 'NewYear20'), (2, 'Venmo', NULL), (3, 'Venmo', NULL);


DROP TABLE IF EXISTS delivery;
CREATE TABLE delivery ( 
    order_id INT UNIQUE NOT NULL,
    delivery_partner_id INT NOT NULL,
    expected_delivery_date DATE NOT NULL,
    delivery_status ENUM('placed', 'in-transit', 'delivered'),
    
    PRIMARY KEY(order_id),
    FOREIGN KEY(order_id) REFERENCES order_invoice(order_id)
		ON UPDATE CASCADE ON DELETE RESTRICT,
	FOREIGN KEY(delivery_partner_id) REFERENCES delivery_partner(partner_id)
		ON UPDATE CASCADE ON DELETE RESTRICT
);
INSERT INTO delivery (order_id, delivery_partner_id, expected_delivery_date, delivery_status) VALUES
    (1, 1, '2023-11-02', 'delivered'), (2, 1, '2023-11-02', 'delivered'),
    (4, 1, '2023-12-16', 'in-transit'), (3, 1, '2023-12-25', 'placed');


ALTER TABLE delivery 
ADD COLUMN status_update_trigger INT DEFAULT 0;

DROP TABLE IF EXISTS order_item;
CREATE TABLE order_item (
	order_id 	INT NOT NULL,
    p_name		VARCHAR(64) NOT NULL,	-- unique alternative key
    quantity	INT NOT NULL,
    PRIMARY KEY (order_id, p_name),
    FOREIGN KEY (order_id) REFERENCES order_invoice(order_id)
		ON UPDATE CASCADE ON DELETE CASCADE,
	FOREIGN KEY (p_name) REFERENCES product(p_name)
		ON UPDATE CASCADE ON DELETE CASCADE
);
INSERT INTO order_item (order_id, p_name, quantity) VALUES
    (1, 'Sashimi Tuna 1 lb', 5), (2, 'Sashimi Tuna 1 lb', 3), (1, 'Maine Uni 150 g', 3),
    (3, 'Sashimi Tuna 1 lb', 6), (4, 'Sashimi Tuna 1 lb', 3), (2, 'Maine Uni 150 g', 3);

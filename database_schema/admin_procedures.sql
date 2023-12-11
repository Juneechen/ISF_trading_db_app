use seafood_service_v4;

-- update tuple from any table given pk field, pk value, and target field, new value
drop procedure if exists update_table;
DELIMITER ^^
CREATE PROCEDURE update_table(IN tablename_p VARCHAR(64), IN field_p VARCHAR(64), IN new_val_p VARCHAR(64), 
                              IN pk_field_p VARCHAR(64), IN pk_val_p VARCHAR(64))
BEGIN
	-- tested and confirmed that type casting will be done for us by MySQL when using statement
    SET @new_val = new_val_p;
    SET @pk_val = pk_val_p;
	
    -- possible error will be catched by the caller (web app)
    SET @qry = CONCAT('UPDATE ', tablename_p, ' SET ', field_p, ' = ?', ' WHERE ', pk_field_p, ' = ?');    
	PREPARE stmt FROM @qry;
    EXECUTE stmt USING @new_val, @pk_val;
    DEALLOCATE PREPARE stmt;
END^^
DELIMITER ;

-- delete tuple from any table given pk field and pk value
drop procedure if exists delete_from;
DELIMITER ^^
CREATE PROCEDURE delete_from(IN tablename_p VARCHAR(64), IN pk_field_p VARCHAR(64), IN pk_val_p VARCHAR(64))
BEGIN
	-- tested and confirmed that type casting will be done for us by MySQL when using statement
    SET @pk_val = pk_val_p;
	SET @qry = CONCAT('DELETE FROM ', tablename_p, ' WHERE ', pk_field_p, ' = ?');

    PREPARE stmt FROM @qry;
    EXECUTE stmt USING @pk_val;
    DEALLOCATE PREPARE stmt;
END^^
DELIMITER ;

/*
-- delete tuple from any table given pk field and pk value
drop procedure if exists count_by_pk;
DELIMITER ^^
CREATE PROCEDURE count_by_pk(IN tablename_p VARCHAR(64), IN pk_field_p VARCHAR(64))
BEGIN    
    SET @qry = CONCAT('SELECT COUNT(', pk_field_p, ') AS num_rows FROM ', tablename_p);

    PREPARE stmt FROM @qry;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
END^^
DELIMITER ;
*/

/*
-- get all the partner_id from delivery_partner table
drop procedure if exists get_all_partner_id;
DELIMITER ^^
CREATE PROCEDURE get_all_partner_id()
BEGIN
	SELECT partner_id FROM delivery_partner;
END^^
DELIMITER ;

-- get all the category_name from category table
drop procedure if exists get_all_category_name;
DELIMITER ^^
CREATE PROCEDURE get_all_category_name()
BEGIN
	SELECT category_name FROM category;
END^^
DELIMITER ;
*/

-- get one field in a table
drop procedure if exists get_all;
DELIMITER ^^
CREATE PROCEDURE get_all(IN fieldname_p VARCHAR(64), IN tablename_p VARCHAR(64))
BEGIN
	SET @qry = CONCAT('SELECT ', fieldname_p, ' FROM ', tablename_p);
    PREPARE stmt FROM @qry;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
END^^
DELIMITER ;


-- insert into product table given values for all fields
drop procedure if exists add_product;
DELIMITER ^^
CREATE PROCEDURE add_product(IN pid_p VARCHAR(16), IN product_name_p VARCHAR(64), IN category_p VARCHAR(64), IN sell_price_p VARCHAR(4), 
								IN description_p VARCHAR(64), IN qty_in_stock_p VARCHAR(4), product_img varchar(64))
BEGIN
	DECLARE int_price INT; 
	DECLARE int_qty INT;
	
	-- cast param as needed, because everying passed in will be string to reduce the type check for every new value 
	SET int_price = CAST(sell_price_p AS SIGNED);
	SET int_qty = COALESCE(CAST(qty_in_stock_p AS SIGNED), 0); -- If qty_in_stock is NULL, use default value (0)
	
	-- pid is auto-increment, ignore. 
	-- Quantity I'm thinking, shall we make a trigger for that - increase when buy from vender, decrease when customer places order
	INSERT INTO product(p_name, category, sell_price, p_description, qty_in_stock, product_img) 
				values (product_name_p, category_p, int_price, description_p, int_qty, product_img);
	-- possible error will be catched by the caller (web app)
END^^
DELIMITER ;

-- 
drop procedure if exists add_vendor;
DELIMITER ^^
CREATE PROCEDURE add_vendor(IN vendor_id_p VARCHAR(16), IN first_name_p VARCHAR(64), IN last_name_p VARCHAR(64), IN phone_number_p CHAR(10), 
								IN steet_number_p VARCHAR(8), IN street_name_p VARCHAR(64), city_p varchar(25), state_p CHAR(2), zip_p CHAR(5))
BEGIN
	INSERT INTO vendor(first_name, last_name, phone_number, steet_number, street_name, city, state, zip) 
				values (first_name_p, last_name_p, phone_number_p, steet_number_p, street_name_p, city_p, state_p, zip_p);
	-- possible error will be catched by the caller (web app)
END^^
DELIMITER ;

-- insert into category 
drop procedure if exists add_category;
DELIMITER ^^
CREATE PROCEDURE add_category(IN category_name_p VARCHAR(64))
BEGIN
	INSERT INTO category(category_name) 
				values (category_name_p);
	-- possible error will be catched by the caller (web app)
END^^
DELIMITER ;

-- insert into vendor_supplies_seafood_product     
drop procedure if exists add_vendor_supplies_seafood_product;
DELIMITER ^^
CREATE PROCEDURE add_vendor_supplies_seafood_product(IN vendor_id_p VARCHAR(64), pid_p VARCHAR(64), price_per_qty_p VARCHAR(64))
BEGIN
	SET @vendor_id_val = vendor_id_p;
    SET @pid_val = pid_p;
    SET @price_per_qty_val = price_per_qty_p;
    
	SET @qry = 'INSERT INTO supplies_seafood_product VALUES (?, ?, ?)';
    PREPARE stmt FROM @qry;
    EXECUTE stmt USING @vendor_id_val, @pid_val, @price_per_qty_val;
    DEALLOCATE PREPARE stmt;
END^^
DELIMITER ;

-- insert into delivery_partner     
drop procedure if exists add_delivery_partner;
DELIMITER ^^
CREATE PROCEDURE add_delivery_partner(IN vendor_id_p VARCHAR(64), first_name_p VARCHAR(64), last_name_p VARCHAR(64), phone_p VARCHAR(64))
BEGIN
	INSERT INTO delivery_partner(first_name, last_name, phone) 
				values (first_name_p, last_name_p, phone_p);
END^^
DELIMITER ;

-- insert into delivery_zone     
drop procedure if exists add_delivery_zone;
DELIMITER ^^
CREATE PROCEDURE add_delivery_zone(IN zipcode_p VARCHAR(5), partner_id_p VARCHAR(64))
BEGIN
	SET @pzipcode_val = zipcode_p;
    SET @partner_id_val = partner_id_p;
    
	SET @qry = 'INSERT INTO delivery_zone VALUES (?, ?)';
    PREPARE stmt FROM @qry;
    EXECUTE stmt USING @pzipcode_val, @partner_id_val;
    DEALLOCATE PREPARE stmt;
END^^
DELIMITER ;


-- insert into coupon     
drop procedure if exists add_coupon;
DELIMITER ^^
CREATE PROCEDURE add_coupon(IN coupon_code_p VARCHAR(10), coupon_discount_amt_p VARCHAR(4), 
								IN coupon_expiration_date_p VARCHAR(64), IN coupon_description_p varchar(64))
BEGIN
	SET @coupon_code_val = coupon_code_p;
    SET @coupon_discount_amt_val = coupon_discount_amt_p;
    SET @coupon_expiration_date_val = coupon_expiration_date_p;
    SET @coupon_description_val = coupon_description_p;
    
	SET @qry = 'INSERT INTO coupon VALUES (?, ?, ?, ?)';
    PREPARE stmt FROM @qry;
    EXECUTE stmt USING @coupon_code_val, @coupon_discount_amt_val, @coupon_expiration_date_val, @coupon_description_val;
    DEALLOCATE PREPARE stmt;
END^^
DELIMITER ;


drop procedure if exists add_payment;
DELIMITER ^^
CREATE PROCEDURE add_payment(IN payment_type_p VARCHAR(64), img_p VARCHAR(64), payment_text_p VARCHAR(64), bg_color_p VARCHAR(64))
BEGIN
	INSERT INTO payment(payment_type, img, payment_text, bg_color) 
				values (payment_type_p, img_p, payment_text_p, bg_color_p);
END^^
DELIMITER ;

drop procedure if exists count_order_per_cid;
DELIMITER ^^
CREATE PROCEDURE count_order_per_cid()
BEGIN
    SELECT c.cid, c.email, COUNT(o.order_id) AS num_orders
		FROM customer c
		LEFT JOIN order_invoice o ON c.cid = o.customer_id
		GROUP BY c.cid, c.email ORDER BY num_orders DESC;
END ^^
DELIMITER ;
-- call count_order_per_cid();


-- find the best selling products in a given year
DELIMITER ^^
CREATE PROCEDURE get_product_sales(IN year_p INT)
BEGIN
	SET @year_val = year_p;
    SET @qry = 'SELECT p_name AS product, SUM(quantity) AS num_sold FROM order_invoice
							JOIN order_item USING (order_id)
							WHERE YEAR(order_date) = ?
							GROUP BY product ORDER BY num_sold DESC;';
    PREPARE stmt FROM @qry;
    EXECUTE stmt USING @year_val;
    DEALLOCATE PREPARE stmt;
END^^
DELIMITER ;


/*
DELETE FROM delivery_partner WHERE partner_id > 25;
DELETE FROM delivery_partner WHERE partner_id BETWEEN 10 AND 20;
DELETE FROM customer WHERE cid > 50;
DELETE FROM product WHERE pid < 6;
DELETE FROM delivery WHERE order_id BETWEEN 2 AND 4;

*/








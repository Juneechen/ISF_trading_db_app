use seafood_service_v4;

DROP PROCEDURE IF EXISTS register_user;
DELIMITER //

CREATE PROCEDURE register_user(
	IN c_fname VARCHAR(64), 
    IN c_lname VARCHAR(64), 
    IN c_email VARCHAR(64), 
    IN c_pwd VARCHAR(64), 
    IN c_phone CHAR(11), 
    IN c_street VARCHAR(64), 
    IN c_apt VARCHAR(8), 
    IN c_state VARCHAR(64), 
    IN c_zip CHAR(5)
    )
	BEGIN
		DECLARE email_already_exist VARCHAR(64);
        
		SELECT email INTO email_already_exist FROM customer 
        WHERE email = c_email 
        LIMIT 1;
        
        IF email_already_exist IS NOT NULL THEN
			SIGNAL SQLSTATE '45007' SET MESSAGE_TEXT = 'This email already exists';
		
		ELSE 
			INSERT INTO customer(c_fname, c_lname, email, pwd, phone, street, apt, state, zip)
			VALUES (c_fname, c_lname, c_email, c_pwd, c_phone, c_street, c_apt, c_state, c_zip);
		END IF;
		SELECT NULL;
    END // 
    DELIMITER ;


DROP PROCEDURE IF EXISTS user_login;
DELIMITER // 
CREATE PROCEDURE user_login(
	IN c_email VARCHAR(64),
    IN c_pwd VARCHAR(64)
)
	BEGIN
		DECLARE email_exist VARCHAR(64);
        DECLARE pwd_exists VARCHAR(64);
        DECLARE check_pwd_un INT;
        
        select count(*) into check_pwd_un from customer where email = c_email and pwd = c_pwd;
        
        SELECT email INTO email_exist FROM customer
        WHERE email = c_email
        LIMIT 1;

        IF email_exist IS NULL THEN
			SIGNAL SQLSTATE '45001' SET MESSAGE_TEXT = "email does not match";
		ELSEIF 
			check_pwd_un = 0 THEN
				SIGNAL SQLSTATE '45001' SET MESSAGE_TEXT = 'email or pw wrong';
        END IF;
	END //
    DELIMITER ;    


DROP PROCEDURE IF EXISTS get_all_inventory;
DELIMITER //
CREATE PROCEDURE get_all_inventory(
    IN c_pname VARCHAR(64) 
)
	BEGIN
        DECLARE product_name VARCHAR(64);
        DECLARE product_count INT;
        
        IF c_pname IS NULL or c_pname = '' THEN
			SELECT * FROM product;
		ELSE
			SELECT COUNT(*) INTO product_count FROM product WHERE p_name = c_pname;
		
        IF product_count = 0 THEN
			SIGNAL SQLSTATE '45008' SET MESSAGE_TEXT = 'product does not exist'; # 45008: product != exist
		ELSE
			SELECT * FROM product where p_name = c_pname;
		END IF;
	END IF;
END //
DELIMITER ;

DROP PROCEDURE IF EXISTS get_promo_codes;
DELIMITER //
CREATE PROCEDURE get_promo_codes(
    IN c_cid INT,
    IN c_coupon_code VARCHAR(10)
)
BEGIN
    DECLARE cid_exists INT;
	DECLARE coupon_available INT;
    SELECT COUNT(*) INTO cid_exists FROM customer
    WHERE cid = c_cid;

    IF cid_exists = 0 THEN
        SIGNAL SQLSTATE '45009' SET MESSAGE_TEXT = 'customer id not found';
    ELSE
        IF c_coupon_code = '' THEN
            SELECT *
            FROM coupon c
            WHERE NOT EXISTS (
                SELECT 1
                FROM order_invoice o
                WHERE o.customer_id = c_cid AND o.coupon_code = c.coupon_code
            );
        ELSE
            SELECT COUNT(*) INTO coupon_available
            FROM coupon c
            WHERE c.coupon_code = c_coupon_code
              AND NOT EXISTS (
                SELECT 1
                FROM order_invoice o
                WHERE o.customer_id = c_cid AND o.coupon_code = c.coupon_code
            );

            IF coupon_available = 0 THEN
                SIGNAL SQLSTATE '45006' SET MESSAGE_TEXT = 'coupon not available';
            ELSE
                SELECT c.coupon_code
                FROM coupon c
                WHERE c.coupon_code = c_coupon_code;
            END IF;
        END IF;
    END IF;
END //
DELIMITER ;

DROP PROCEDURE IF EXISTS get_payment_methods;
DELIMITER //
CREATE PROCEDURE get_payment_methods()
BEGIN
	SELECT * from payment;
END //
DELIMITER ;


DROP PROCEDURE IF EXISTS remove_item_from_inventory;
DELIMITER //
CREATE PROCEDURE remove_item_from_inventory(
	IN c_pid INT,
    IN c_qty INT
)
BEGIN
    DECLARE pid_exists INT;
    DECLARE c_qty_exists INT;
    
	SELECT COUNT(*) INTO pid_exists FROM product
    WHERE pid = c_pid;
    
    IF pid_exists = 0 THEN
		SIGNAL SQLSTATE '45002' SET MESSAGE_TEXT = 'product not found';
	ELSE
		SELECT qty_in_stock INTO c_qty_exists FROM product
		WHERE pid = c_pid;
	
		IF c_qty_exists < c_qty THEN
			SIGNAL SQLSTATE '45003' SET MESSAGE_TEXT = 'Not enough qty in stock';
		ELSE
			UPDATE product SET qty_in_stock = qty_in_stock - c_qty
            WHERE pid = c_pid;
		END IF;
	END IF;
END //
DELIMITER ;
    
DROP PROCEDURE IF EXISTS place_order;
DELIMITER //
CREATE PROCEDURE place_order(
	IN c_customer_id INT,
    IN c_payment_type VARCHAR(16),
    IN c_coupon_code VARCHAR(10)
)
BEGIN
	DECLARE customer_exists INT;
    DECLARE payment_type_exists VARCHAR(16);
    DECLARE coupon_code_exists VARCHAR(10);
	
    
    SELECT COUNT(*) INTO customer_exists FROM customer
    WHERE cid = c_customer_id;
    
    SELECT payment_type INTO payment_type_exists FROM payment
    WHERE payment_type = c_payment_type;
    
    SELECT coupon_code INTO coupon_code_exists FROM coupon
    WHERE coupon_code = c_coupon_code;
    
    IF customer_exists = 0 THEN
		SIGNAL SQLSTATE '45010' SET MESSAGE_TEXT = 'customer not found';
	ELSEIF payment_type_exists IS NULL THEN
		SIGNAL SQLSTATE '45011' SET MESSAGE_TEXT = 'payment doesnt exist';
	ELSEIF coupon_code_exists IS NULL AND c_coupon_code <> '' THEN
		SIGNAL SQLSTATE '45005' SET MESSAGE_TEXT = 'coupon not found';
	ELSE
		SET @set_order_date = CURRENT_TIMESTAMP;
        
        INSERT INTO order_invoice (customer_id, payment_type, coupon_code, order_date)
        VALUES (c_customer_id, c_payment_type, c_coupon_code, @set_order_date);
        
        -- Adding this line so that we can get the order_id that was just created	
        select last_insert_id() as order_id;
        END IF;
END //
DELIMITER ;

DROP PROCEDURE IF EXISTS add_item_to_order;
DELIMITER //
CREATE PROCEDURE add_item_to_order(
	IN c_order_id INT,
    IN c_pname VARCHAR(64),
    in c_quantity INT
)
BEGIN
	DECLARE order_exists INT;
    
    SELECT COUNT(*) into order_exists FROM order_invoice
    WHERE order_id = c_order_id;
    
    IF order_exists = 0 THEN
		SIGNAL SQLSTATE '45012' SET MESSAGE_TEXT = 'order id doesnt exist';
	ELSE
		INSERT INTO order_item(order_id, p_name, quantity)
        VALUES(c_order_id, c_pname, c_quantity);
	END IF;
END // 
DELIMITER ;

DROP PROCEDURE IF EXISTS begin_delivery;
DELIMITER //
CREATE PROCEDURE begin_delivery(
    IN c_order_id INT
)
BEGIN
	DECLARE order_id_exists INT;
    DECLARE cid_exists CHAR(5);
	DECLARE partner_ids INT;
    DECLARE count_items INT;
    DECLARE delivery_date DATE;

	SELECT customer_id INTO order_id_exists FROM order_invoice WHERE order_id = c_order_id;
    SELECT zip INTO cid_exists from customer WHERE cid = order_id_exists;
    select partner_id INTO partner_ids from delivery_zone where zipcode = (select zip from customer where cid = order_id_exists);
    SELECT COUNT(*) INTO count_items from order_item where order_id = c_order_id;
    select cid_exists;
    
	SET delivery_date = CASE
		WHEN count_items < 5 THEN DATE_ADD(NOW(), INTERVAL 1 DAY)
		WHEN count_items <= 10 THEN DATE_ADD(NOW(), INTERVAL 2 DAY)
		ELSE DATE_ADD(NOW(), INTERVAL 5 DAY)
	END;
    
    INSERT INTO delivery(order_id, delivery_partner_id, expected_delivery_date, delivery_status) 
    VALUES(c_order_id, partner_ids, delivery_date, 'placed');
END // 
DELIMITER ;



DROP PROCEDURE IF EXISTS convert_email_to_id;
DELIMITER //
CREATE PROCEDURE convert_email_to_id(
	IN c_email VARCHAR(64)
)
BEGIN
	select cid from customer where email = c_email;
END //
DELIMITER ;


DROP PROCEDURE IF EXISTS get_delivery;
DELIMITER //

CREATE PROCEDURE get_delivery(
    IN param_order_id INT
)
BEGIN
    DECLARE current_status VARCHAR(20);
    DECLARE new_status_index INT;

    -- Return the updated status
    SELECT * FROM delivery WHERE order_id = param_order_id;
    
    -- Get the current status
    SELECT delivery_status INTO current_status FROM delivery WHERE order_id = param_order_id;

    -- Calculate the new status index
    SET new_status_index = FIND_IN_SET(current_status, 'placed,in-transit,delivered') + 1;

    -- Update the status if it's within the valid range
    IF new_status_index <= 3 THEN
        UPDATE delivery 
        SET delivery_status = ELT(new_status_index, 'placed', 'in-transit', 'delivered')
        WHERE order_id = param_order_id;
    END IF;
END //

DELIMITER ;

DROP PROCEDURE IF EXISTS get_partner_info;
DELIMITER //

CREATE PROCEDURE get_partner_info(
    IN param_partner_id INT
)
BEGIN

   select * from delivery_partner where partner_id = param_partner_id;
END //

DELIMITER ;

DROP PROCEDURE IF EXISTS insert_vendor;

DELIMITER //
CREATE PROCEDURE insert_vendor(
    IN v_id INT, IN fname VARCHAR(64), IN lname VARCHAR(64), 
    IN phone INT, IN street_num INT, IN street_name VARCHAR(64), 
    IN city VARCHAR(25), IN state VARCHAR(2), IN zip INT)
BEGIN
    INSERT INTO vendor (vendor_id, first_name, last_name, phone_number, steet_number, street_name, city, state, zip)
    VALUES (v_id, fname, lname, phone, street_num, street_name, city, state, zip);
END //
DELIMITER ;


DROP PROCEDURE IF EXISTS insert_category;

DELIMITER //
CREATE PROCEDURE insert_category(IN cat_name VARCHAR(64))
BEGIN
    INSERT INTO category (category_name) VALUES (cat_name);
END //
DELIMITER ;


DROP PROCEDURE IF EXISTS insert_product;

DELIMITER //
CREATE PROCEDURE insert_product(
    IN pname VARCHAR(64), IN cat VARCHAR(64), IN price INT, 
    IN p_desc VARCHAR(64), IN qty INT, IN p_img VARCHAR(64))
BEGIN
    INSERT INTO product (p_name, category, sell_price, p_description, qty_in_stock, product_img)
    VALUES (pname, cat, price, p_desc, qty, p_img);
END //
DELIMITER ;


DROP PROCEDURE IF EXISTS insert_vendor_supply;

DELIMITER //
CREATE PROCEDURE insert_vendor_supply(IN v_id INT, IN p_id INT, IN price_per_qty FLOAT)
BEGIN
    INSERT INTO vendor_supplies_seafood_product (vendor_id, pid, price_per_qty)
    VALUES (v_id, p_id, price_per_qty);
END //
DELIMITER ;


DROP PROCEDURE IF EXISTS insert_delivery_partner;

DELIMITER //
CREATE PROCEDURE insert_delivery_partner(
    IN fname VARCHAR(15), IN lname VARCHAR(15), IN phone CHAR(11))
BEGIN
    INSERT INTO delivery_partner (first_name, last_name, phone)
    VALUES (fname, lname, phone);
END //
DELIMITER ;

DROP PROCEDURE IF EXISTS insert_delivery_zone;

DELIMITER //
CREATE PROCEDURE insert_delivery_zone(IN z_code CHAR(5), IN partner_id INT)
BEGIN
    INSERT INTO delivery_zone (zipcode, partner_id) VALUES (z_code, partner_id);
END //
DELIMITER ;



DROP PROCEDURE IF EXISTS insert_coupon;

DELIMITER //
CREATE PROCEDURE insert_coupon(
    IN p_coupon_code VARCHAR(10), IN p_coupon_discount_amt FLOAT, IN p_coupon_expiration_date DATE, IN p_coupon_description VARCHAR(64))
BEGIN
    INSERT INTO coupon (coupon_code, coupon_discount_amt, coupon_expiration_date, coupon_description)
    VALUES (p_coupon_code, p_coupon_discount_amt, p_coupon_expiration_date, p_coupon_description);
END //
DELIMITER ;

DROP PROCEDURE IF EXISTS insert_payment;

DELIMITER //
CREATE PROCEDURE insert_payment(
    IN p_type VARCHAR(16), IN img VARCHAR(64), 
    IN p_text VARCHAR(64), IN bg_color VARCHAR(64))
BEGIN
    INSERT INTO payment (payment_type, img, payment_text, bg_color)
    VALUES (p_type, img, p_text, bg_color);
END //
DELIMITER ;

DROP PROCEDURE IF EXISTS get_all_coupon_codes;
DELIMITER //
CREATE PROCEDURE get_all_coupon_codes()
BEGIN
    select * from coupon;
END //
DELIMITER ;



    








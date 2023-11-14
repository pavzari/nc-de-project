-- PostgreSQL production database sql schema

CREATE TABLE address (
    address_id INT PRIMARY KEY,
    address_line_1 VARCHAR(240),
    address_line_2 VARCHAR(240),
    district VARCHAR(240),
    city VARCHAR(240),
    postal_code VARCHAR(240),
    country VARCHAR(240),
    phone VARCHAR(240),
    created_at TIMESTAMP,
    last_updated TIMESTAMP
);
CREATE TABLE counterparty (
    counterparty_id INT PRIMARY KEY,
    counterparty_legal_name VARCHAR(240),
    legal_address_id INT REFERENCES address(address_id),
    commercial_contact VARCHAR(240),
    delivery_contact VARCHAR(240),
    created_at TIMESTAMP,
    last_updated TIMESTAMP
);
CREATE TABLE currency (
    currency_id INT PRIMARY KEY,
    currency_code VARCHAR(3),
    created_at TIMESTAMP,
    last_updated TIMESTAMP
);
CREATE TABLE department (
    department_id INT PRIMARY KEY,
    department_name VARCHAR(240),
    location VARCHAR(240),
    manager VARCHAR(240),
    created_at TIMESTAMP,
    last_updated TIMESTAMP
);
CREATE TABLE staff (
    staff_id INT PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    department_id INT REFERENCES department(department_id),
    email_address VARCHAR(240),
    created_at TIMESTAMP,
    last_updated TIMESTAMP
);
CREATE TABLE design (
    design_id INT PRIMARY KEY,
    created_at TIMESTAMP,
    design_name VARCHAR(240),
    file_location VARCHAR(240),
    file_name VARCHAR(240),
    last_updated TIMESTAMP
);
CREATE TABLE payment_type (
    payment_type_id INT PRIMARY KEY,
    payment_type_name VARCHAR(240),
    created_at TIMESTAMP,
    last_updated TIMESTAMP
);
CREATE TABLE purchase_order (
    purchase_order_id INT PRIMARY KEY,
    created_at TIMESTAMP,
    last_updated TIMESTAMP,
    staff_id INT REFERENCES staff(staff_id),
    counterparty_id INT REFERENCES counterparty(counterparty_id),
    item_code VARCHAR(20),
    item_quantity INT,
    item_unit_price NUMERIC(10,2),
    currency_id INT REFERENCES currency(currency_id),
    agreed_delivery_date VARCHAR(10),
    agreed_payment_date VARCHAR(10),
    agreed_delivery_location_id INT REFERENCES address(address_id)
);
CREATE TABLE sales_order (
    sales_order_id INT PRIMARY KEY,
    created_at TIMESTAMP,
    last_updated TIMESTAMP,
    design_id INT REFERENCES design(design_id),
    staff_id INT REFERENCES staff(staff_id),
    counterparty_id INT REFERENCES counterparty(counterparty_id),
    units_sold INT,
    unit_price NUMERIC(10,2),
    currency_id INT REFERENCES currency(currency_id),
    agreed_delivery_date VARCHAR(10),
    agreed_payment_date VARCHAR(10),
    agreed_delivery_location_id INT REFERENCES address(address_id)
);
CREATE TABLE transaction (
    transaction_id INT PRIMARY KEY,
    transaction_type VARCHAR(20),
    sales_order_id INT REFERENCES sales_order(sales_order_id),
    purchase_order_id INT REFERENCES purchase_order(purchase_order_id),
    created_at TIMESTAMP,
    last_updated TIMESTAMP
);
CREATE TABLE payment (
    payment_id INT PRIMARY KEY,
    created_at TIMESTAMP,
    last_updated TIMESTAMP,
    transaction_id INT REFERENCES transaction(transaction_id),
    counterparty_id INT REFERENCES counterparty(counterparty_id),
    payment_amount NUMERIC(10,2),
    currency_id INT REFERENCES currency(currency_id),
    payment_type_id INT REFERENCES payment_type(payment_type_id),
    paid BOOLEAN,
    payment_date VARCHAR(10),
    company_ac_number INT,
    counterparty_ac_number INT
);

CREATE TABLE _prisma_migrations ();
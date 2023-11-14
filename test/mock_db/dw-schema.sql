
-- PostgreSQL data warehouse sql schema

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
-- SELECT pg_catalog.set_config('search_path', '', false); 
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;
SET default_tablespace = '';
SET default_table_access_method = heap;

CREATE TABLE dim_counterparty (
    counterparty_id integer NOT NULL,
    counterparty_legal_name character varying NOT NULL,
    counterparty_legal_address_line_1 character varying NOT NULL,
    counterparty_legal_address_line_2 character varying,
    counterparty_legal_district character varying,
    counterparty_legal_city character varying NOT NULL,
    counterparty_legal_postal_code character varying NOT NULL,
    counterparty_legal_country character varying NOT NULL,
    counterparty_legal_phone_number character varying NOT NULL
);


CREATE TABLE dim_currency (
    currency_id integer NOT NULL,
    currency_code character varying NOT NULL,
    currency_name character varying NOT NULL
);


CREATE TABLE dim_date (
    date_id date NOT NULL,
    year integer NOT NULL,
    month integer NOT NULL,
    day integer NOT NULL,
    day_of_week integer NOT NULL,
    day_name character varying NOT NULL,
    month_name character varying NOT NULL,
    quarter integer NOT NULL
);



CREATE TABLE dim_design (
    design_id integer NOT NULL,
    design_name character varying NOT NULL,
    file_location character varying NOT NULL,
    file_name character varying NOT NULL
);



CREATE TABLE dim_location (
    location_id integer NOT NULL,
    address_line_1 character varying NOT NULL,
    address_line_2 character varying,
    district character varying,
    city character varying NOT NULL,
    postal_code character varying NOT NULL,
    country character varying NOT NULL,
    phone character varying NOT NULL
);



CREATE TABLE dim_payment_type (
    payment_type_id integer NOT NULL,
    payment_type_name character varying NOT NULL
);



CREATE TABLE dim_staff (
    staff_id integer NOT NULL,
    first_name character varying NOT NULL,
    last_name character varying NOT NULL,
    department_name character varying NOT NULL,
    location character varying NOT NULL,
    email_address character varying NOT NULL
);



CREATE TABLE dim_transaction (
    transaction_id integer NOT NULL,
    transaction_type character varying NOT NULL,
    sales_order_id integer,
    purchase_order_id integer
);



CREATE TABLE fact_payment (
    payment_record_id integer NOT NULL,
    payment_id integer NOT NULL,
    created_date date NOT NULL,
    created_time time without time zone NOT NULL,
    last_updated_date date NOT NULL,
    last_updated time without time zone NOT NULL,
    transaction_id integer NOT NULL,
    counterparty_id integer NOT NULL,
    payment_amount numeric NOT NULL,
    currency_id integer NOT NULL,
    payment_type_id integer NOT NULL,
    paid boolean NOT NULL,
    payment_date date NOT NULL
);


CREATE TABLE fact_purchase_order (
    purchase_record_id integer NOT NULL,
    puchase_order_id integer NOT NULL, --------TYPO IN COLUMN NAME !!!!!!
    created_date date NOT NULL,
    created_time time without time zone NOT NULL,
    last_updated_date date NOT NULL,
    last_updated_time time without time zone NOT NULL,
    staff_id integer NOT NULL,
    counterparty_id integer NOT NULL,
    item_code character varying NOT NULL,
    item_quantity integer NOT NULL,
    item_unit_price numeric NOT NULL,
    currency_id integer NOT NULL,
    agreed_delivery_date date NOT NULL,
    agreed_payment_date date NOT NULL,
    agreed_delivery_location_id integer NOT NULL
);



CREATE TABLE fact_sales_order (
    sales_record_id SERIAL,
    sales_order_id integer NOT NULL,
    created_date date NOT NULL,
    created_time time without time zone NOT NULL,
    last_updated_date date NOT NULL,
    last_updated_time time without time zone NOT NULL,
    sales_staff_id integer NOT NULL,
    counterparty_id integer NOT NULL,
    units_sold integer NOT NULL,
    unit_price numeric(10,2) NOT NULL,
    currency_id integer NOT NULL,
    design_id integer NOT NULL,
    agreed_payment_date date NOT NULL,
    agreed_delivery_date date NOT NULL,
    agreed_delivery_location_id integer NOT NULL
);



ALTER TABLE ONLY dim_counterparty
    ADD CONSTRAINT dim_counterparty_pkey PRIMARY KEY (counterparty_id);



ALTER TABLE ONLY dim_currency
    ADD CONSTRAINT dim_currency_pkey PRIMARY KEY (currency_id);



ALTER TABLE ONLY dim_date
    ADD CONSTRAINT dim_date_pkey PRIMARY KEY (date_id);



ALTER TABLE ONLY dim_design
    ADD CONSTRAINT dim_design_pkey PRIMARY KEY (design_id);




ALTER TABLE ONLY dim_location
    ADD CONSTRAINT dim_location_pkey PRIMARY KEY (location_id);



ALTER TABLE ONLY dim_payment_type
    ADD CONSTRAINT dim_payment_type_pkey PRIMARY KEY (payment_type_id);



ALTER TABLE ONLY dim_staff
    ADD CONSTRAINT dim_staff_pkey PRIMARY KEY (staff_id);



ALTER TABLE ONLY dim_transaction
    ADD CONSTRAINT dim_transaction_pkey PRIMARY KEY (transaction_id);



ALTER TABLE ONLY fact_payment
    ADD CONSTRAINT fact_payment_pkey PRIMARY KEY (payment_record_id);



ALTER TABLE ONLY fact_purchase_order
    ADD CONSTRAINT fact_purchase_order_pkey PRIMARY KEY (purchase_record_id);



ALTER TABLE ONLY fact_sales_order
    ADD CONSTRAINT fact_sales_order_pkey PRIMARY KEY (sales_record_id);



ALTER TABLE ONLY fact_payment
    ADD CONSTRAINT fact_payment_counterparty_id_fkey FOREIGN KEY (counterparty_id) REFERENCES dim_counterparty(counterparty_id);



ALTER TABLE ONLY fact_payment
    ADD CONSTRAINT fact_payment_created_date_fkey FOREIGN KEY (created_date) REFERENCES dim_date(date_id);



ALTER TABLE ONLY fact_payment
    ADD CONSTRAINT fact_payment_currency_id_fkey FOREIGN KEY (currency_id) REFERENCES dim_currency(currency_id);



ALTER TABLE ONLY fact_payment
    ADD CONSTRAINT fact_payment_last_updated_date_fkey FOREIGN KEY (last_updated_date) REFERENCES dim_date(date_id);



ALTER TABLE ONLY fact_payment
    ADD CONSTRAINT fact_payment_payment_date_fkey FOREIGN KEY (payment_date) REFERENCES dim_date(date_id);



ALTER TABLE ONLY fact_payment
    ADD CONSTRAINT fact_payment_payment_type_id_fkey FOREIGN KEY (payment_type_id) REFERENCES dim_payment_type(payment_type_id);



ALTER TABLE ONLY fact_payment
    ADD CONSTRAINT fact_payment_transaction_id_fkey FOREIGN KEY (transaction_id) REFERENCES dim_transaction(transaction_id);



ALTER TABLE ONLY fact_purchase_order
    ADD CONSTRAINT fact_purchase_order_agreed_delivery_date_fkey FOREIGN KEY (agreed_delivery_date) REFERENCES dim_date(date_id);


ALTER TABLE ONLY fact_purchase_order
    ADD CONSTRAINT fact_purchase_order_agreed_delivery_location_id_fkey FOREIGN KEY (agreed_delivery_location_id) REFERENCES dim_location(location_id);



ALTER TABLE ONLY fact_purchase_order
    ADD CONSTRAINT fact_purchase_order_agreed_payment_date_fkey FOREIGN KEY (agreed_payment_date) REFERENCES dim_date(date_id);




ALTER TABLE ONLY fact_purchase_order
    ADD CONSTRAINT fact_purchase_order_counterparty_id_fkey FOREIGN KEY (counterparty_id) REFERENCES dim_counterparty(counterparty_id);



ALTER TABLE ONLY fact_purchase_order
    ADD CONSTRAINT fact_purchase_order_created_date_fkey FOREIGN KEY (created_date) REFERENCES dim_date(date_id);



ALTER TABLE ONLY fact_purchase_order
    ADD CONSTRAINT fact_purchase_order_currency_id_fkey FOREIGN KEY (currency_id) REFERENCES dim_currency(currency_id);



ALTER TABLE ONLY fact_purchase_order
    ADD CONSTRAINT fact_purchase_order_last_updated_date_fkey FOREIGN KEY (last_updated_date) REFERENCES dim_date(date_id);



ALTER TABLE ONLY fact_purchase_order
    ADD CONSTRAINT fact_purchase_order_staff_id_fkey FOREIGN KEY (staff_id) REFERENCES dim_staff(staff_id);



ALTER TABLE ONLY fact_sales_order
    ADD CONSTRAINT fact_sales_order_agreed_delivery_date_fkey FOREIGN KEY (agreed_delivery_date) REFERENCES dim_date(date_id);



ALTER TABLE ONLY fact_sales_order
    ADD CONSTRAINT fact_sales_order_agreed_delivery_location_id_fkey FOREIGN KEY (agreed_delivery_location_id) REFERENCES dim_location(location_id);



ALTER TABLE ONLY fact_sales_order
    ADD CONSTRAINT fact_sales_order_agreed_payment_date_fkey FOREIGN KEY (agreed_payment_date) REFERENCES dim_date(date_id);



ALTER TABLE ONLY fact_sales_order
    ADD CONSTRAINT fact_sales_order_counterparty_id_fkey FOREIGN KEY (counterparty_id) REFERENCES dim_counterparty(counterparty_id);



ALTER TABLE ONLY fact_sales_order
    ADD CONSTRAINT fact_sales_order_created_date_fkey FOREIGN KEY (created_date) REFERENCES dim_date(date_id);



ALTER TABLE ONLY fact_sales_order
    ADD CONSTRAINT fact_sales_order_currency_id_fkey FOREIGN KEY (currency_id) REFERENCES dim_currency(currency_id);



ALTER TABLE ONLY fact_sales_order
    ADD CONSTRAINT fact_sales_order_design_id_fkey FOREIGN KEY (design_id) REFERENCES dim_design(design_id);



ALTER TABLE ONLY fact_sales_order
    ADD CONSTRAINT fact_sales_order_last_updated_date_fkey FOREIGN KEY (last_updated_date) REFERENCES dim_date(date_id);


ALTER TABLE ONLY fact_sales_order
    ADD CONSTRAINT fact_sales_order_sales_staff_id_fkey FOREIGN KEY (sales_staff_id) REFERENCES dim_staff(staff_id);

CREATE DATABASE people_data;
\connect people_data;
CREATE SCHEMA dit
    CREATE TABLE people_data__jml (
        id serial PRIMARY KEY,
        email_address varchar(255),
        person_id varchar(20),
        employee_numbers character varying[]
        person_type varchar(255),
        grade varchar(255),
        grade_level varchar(255),
    );

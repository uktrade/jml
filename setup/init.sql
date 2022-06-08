CREATE DATABASE people_data;
\connect people_data;
CREATE SCHEMA dit
    CREATE TABLE people_data__identities (
        id serial PRIMARY KEY,
        sso_user_id  uuid,
        employee_numbers character varying[]
    );

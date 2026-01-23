CREATE TABLE users (
    user_id UUID PRIMARY KEY,
    first_name TEXT,
    last_name TEXT,
    gender CHAR,
    street TEXT,
    city TEXT,
    zip INT,
    lat DECIMAL,
    long DECIMAL,
    job TEXT,
    dob DATE
);
CREATE TABLE merchants (
    merchant TEXT PRIMARY KEY,
    merch_lat DECIMAL,
    merch_long DECIMAL,
    merch_zipcode INTEGER
);

COPY users (user_id, first_name, last_name, gender, street, city, zip, lat, long, job, dob)
FROM '/docker-entrypoint-initdb.d/data/credit_card_transactions_users.csv'
DELIMITER ';'
CSV HEADER;

COPY merchants (merchant, merch_lat, merch_long, merch_zipcode)
FROM '/docker-entrypoint-initdb.d/data/credit_card_transactions_merchants.csv'
DELIMITER ';'
CSV HEADER;

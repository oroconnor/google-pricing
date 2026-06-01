CREATE TABLE pricing (
    sku_id                  VARCHAR(100)    NOT NULL,
    description             VARCHAR(200)    NOT NULL,
    valid_from              TIMESTAMP       NOT NULL,
    model                   VARCHAR(50),
    direction               VARCHAR(10),
    format                  VARCHAR(20),
    input_token_threshold   VARCHAR(20),
    price_per_mil_tokens    NUMERIC(7,3),
    PRIMARY KEY (sku_id, valid_from)
);

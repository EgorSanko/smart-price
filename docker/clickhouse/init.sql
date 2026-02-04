CREATE DATABASE IF NOT EXISTS smartprice;

CREATE TABLE IF NOT EXISTS smartprice.price_events
(
    product_id UInt64,
    marketplace LowCardinality(String),
    price Float64,
    original_price Nullable(Float64),
    is_available UInt8 DEFAULT 1,
    recorded_at DateTime DEFAULT now(),
    date Date DEFAULT toDate(recorded_at)
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (product_id, recorded_at);
# StockStream

[![Deploy](https://github.com/puneethkotha/StockStream/actions/workflows/pages.yml/badge.svg)](https://github.com/puneethkotha/StockStream/actions/workflows/pages.yml)  
[Product site](https://puneethkotha.github.io/StockStream/)

Distributed real-time analytics platform for streaming stock market data.

### Description

StockStream ingests live and historical OHLCV data from Yahoo Finance, streams it through Apache Kafka, and processes it with Spark Structured Streaming. Price time-series is written to InfluxDB for fast range queries and aggregations; stock metadata (symbol, sector, industry, 52-week high/low) is stored in PostgreSQL. A rule engine runs on each batch to fire alerts on price moves, volume spikes, and volatility. Grafana dashboards connect to InfluxDB for real-time charts. The stack runs in Docker: Zookeeper, Kafka, Spark master/worker, InfluxDB, PostgreSQL, Grafana, and a Python producer container. Designed for fault tolerance (consumer groups, checkpointing, backpressure) and horizontal scaling via Kafka partitions and Spark workers.

---

## Tech Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Message broker | Apache Kafka | 2.8 |
| Stream processing | Apache Spark Structured Streaming | 3.3.3 |
| Time-series DB | InfluxDB | 2.5.1 |
| Relational DB | PostgreSQL | latest |
| Visualization | Grafana OSS | 8.4.3 |
| Runtime | Python | 3.10+ |

**Python dependencies:** `confluent-kafka`, `findspark`, `psycopg2-binary`, `influxdb-client`, `yfinance`, `python-dotenv`, `schedule`, `pytz`

---

## Key Capabilities

### Event streaming pipeline

- Kafka topics: `real-time-stock-prices`, `stock-general-information` (4 partitions each)
- Consumer group: `stock-stream-consumer-group`
- Backpressure: `maxOffsetsPerTrigger` = 10,000
- Checkpoint recovery at `/tmp/spark-checkpoint`

### Hybrid storage

- **PostgreSQL:** Stock metadata. Indexes on `Symbol`, `Entry_Date`, `Sector`, `Industry`, composite `(Symbol, Entry_Date)`
- **InfluxDB:** OHLCV time-series. Symbols as tags, line protocol write

### Alert rules (configurable)

| Rule | Default | Severity |
|------|---------|----------|
| Price drop | 5% | HIGH |
| Price spike | 5% | MEDIUM |
| High volume | 1M shares | INFO |
| Volatility (high-low spread) | 3% | MEDIUM |

Logs: `logs/alerts.log`, `logs/producer.log`, `logs/consumer.log`

---

## Quick Start

**Prerequisites:** Python 3.10+, Docker, Docker Compose

```bash
# 1. Start infrastructure
docker-compose up -d

# 2. Install Python deps
pip install -r requirements.txt

# 3. Run producer
cd producer && python producer.py
```

Consumer (inside Spark container):

```bash
docker exec -it ktech_spark_submit bash -c "spark-submit --master spark://spark-master:7077 \
    --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.3 \
    --jars /opt/bitnami/spark/jars/postgresql-42.5.4.jar \
    /app/consumer/consumer.py"
```

---

## Project Layout

```
├── producer/
│   ├── producer.py
│   ├── producer_utils.py
│   └── stock_info_producer.py
├── consumer/
│   ├── consumer.py
│   ├── InfluxDBWriter.py
│   └── alert_rules.py
├── script/
│   ├── initdb.sql
│   └── utils.py
├── logs/
├── docs/                 # GitHub Pages landing site
├── docker-compose.yaml
├── requirements.txt
└── pyproject.toml
```

---

## Data Flow

1. **Ingestion:** yfinance → producer → Kafka (`real-time-stock-prices`, `stock-general-information`)
2. **Processing:** Spark Structured Streaming → parse, validate, transform
3. **Storage:** InfluxDB (OHLCV), PostgreSQL (metadata via `stock_info_producer`)
4. **Alerting:** `consumer/alert_rules.py` runs on each batch
5. **Viz:** Grafana → InfluxDB (port 3000)

---

## Configuration

### Environment (`.env`)

| Variable | Description |
|----------|-------------|
| `STOCKS` | Comma-separated symbols (e.g. `AAPL,MSFT,GOOGL`) |
| `INFLUXDB_BUCKET` | InfluxDB bucket |
| `INFLUXDB_MEASUREMENT` | Measurement name |
| `INFLUX_ORG`, `INFLUX_TOKEN` | InfluxDB auth |
| `POSTGRES_*` | PostgreSQL connection |

### Alert thresholds

Edit `consumer/alert_rules.py`:

```python
PriceDropAlert(threshold_percent=5.0)
PriceSpikeAlert(threshold_percent=5.0)
HighVolumeAlert(threshold_volume=1000000)
VolatilityAlert(threshold_percent=3.0)
```

### Performance

Spark options in `consumer/consumer.py`:
- `maxOffsetsPerTrigger`: 10000 (backpressure)
- `kafka.group.id`: stock-stream-consumer-group

---

## Architecture

![Architecture](images/architecture.jpg)

Yahoo Finance API → Producer → Kafka → Spark Streaming → InfluxDB / PostgreSQL → Grafana. All services run via Docker Compose.

---

## Dashboard

![Grafana dashboard](images/grafana.jpg)

Grafana at `localhost:3000`, wired to InfluxDB. Candlestick, gauge, and line charts for real-time and historical data.

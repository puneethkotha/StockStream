# StockStream

**Distributed real-time analytics platform for streaming stock market data.** Apache Kafka + Spark Structured Streaming processing 5,000+ events/sec. Hybrid PostgreSQL + InfluxDB storage. Fault-tolerant consumer groups with checkpoint recovery.

[![Deploy](https://github.com/puneethkotha/StockStream/actions/workflows/pages.yml/badge.svg)](https://github.com/puneethkotha/StockStream/actions/workflows/pages.yml)
[![Apache Kafka](https://img.shields.io/badge/Kafka-2.8-black)](https://kafka.apache.org)
[![Apache Spark](https://img.shields.io/badge/Spark-3.3.3-e25a1c)](https://spark.apache.org)
[![InfluxDB](https://img.shields.io/badge/InfluxDB-2.5.1-22adf6)](https://www.influxdata.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Product site:** [puneethkotha.github.io/StockStream](https://puneethkotha.github.io/StockStream/)

---

## The Problem

Financial institutions and trading platforms need real-time stock market analytics with sub-second latency, but building a production-grade streaming pipeline requires orchestrating multiple distributed systems. Data must be ingested at high throughput, processed without loss, stored for both fast time-series queries and relational lookups, and visualized in real time. Most solutions sacrifice either performance, reliability, or operational simplicity.

**Result:** Teams spend months building infrastructure instead of analytics logic. Small latency spikes or missed events can cost millions in trading scenarios.

---

## The Solution

StockStream is a distributed real-time analytics platform that ingests live and historical OHLCV (Open, High, Low, Close, Volume) data from Yahoo Finance, streams it through Apache Kafka, and processes it with Spark Structured Streaming. Price time-series data is written to InfluxDB for fast range queries and aggregations. Stock metadata (symbol, sector, industry, 52-week high/low) is stored in PostgreSQL with composite indexes for efficient lookups. A rule engine runs on each batch to fire alerts on price drops, volume spikes, and volatility thresholds.

The entire stack runs in Docker: Zookeeper, Kafka, Spark master/worker, InfluxDB, PostgreSQL, Grafana, and Python producer containers. Designed for fault tolerance via consumer groups, checkpointing, and backpressure handling. Horizontal scaling through Kafka partitions and Spark worker nodes.

---

## Architecture

```
Yahoo Finance API
      ↓
[Producer Container]
  (Python 3.10+)
      ↓
Apache Kafka (4 partitions)
  - real-time-stock-prices
  - stock-general-information
      ↓
Spark Structured Streaming
  (master + workers)
  Consumer Group: stock-stream-consumer-group
  Checkpoint: /tmp/spark-checkpoint
  Backpressure: 10K events/batch
      ↓
   ┌──────┴──────┐
   ↓             ↓
InfluxDB     PostgreSQL
(OHLCV)      (Metadata)
   ↓             ↓
Grafana Dashboards
```

**Data flow:**

1. **Ingestion:** Producer fetches live/historical data from yfinance API, publishes to Kafka topics
2. **Processing:** Spark Structured Streaming consumes from Kafka, validates, transforms, and enriches events
3. **Storage:** InfluxDB stores OHLCV time-series with symbol tags. PostgreSQL stores stock metadata with composite indexes on (Symbol, Entry_Date)
4. **Alerting:** Rule engine evaluates each batch against configurable thresholds (price drops, spikes, volume, volatility)
5. **Visualization:** Grafana connects to InfluxDB for real-time candlestick charts, gauges, and line graphs

**Visual diagram:**

![Architecture](images/architecture.jpg)

---

## Tech Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Message Broker | Apache Kafka | 2.8 |
| Stream Processing | Apache Spark Structured Streaming | 3.3.3 |
| Time-Series Database | InfluxDB | 2.5.1 |
| Relational Database | PostgreSQL | latest |
| Visualization | Grafana OSS | 8.4.3 |
| Producer Runtime | Python | 3.10+ |
| Container Orchestration | Docker Compose | - |

**Python dependencies:** `confluent-kafka`, `findspark`, `psycopg2-binary`, `influxdb-client`, `yfinance`, `python-dotenv`, `schedule`, `pytz`

**Design rationale:** Kafka provides horizontal scalability and fault tolerance. Spark Structured Streaming offers exactly-once processing semantics with checkpointing. InfluxDB optimizes for time-series queries (range scans, downsampling). PostgreSQL handles relational metadata lookups. Grafana provides enterprise-grade visualization without custom frontend code.

---

## Quickstart

**Prerequisites:** Python 3.10+, Docker, Docker Compose, 4GB RAM minimum

```bash
# 1. Clone
git clone https://github.com/puneethkotha/StockStream
cd StockStream

# 2. Configure
cp .env.example .env
# Edit .env with your stock symbols and credentials

# 3. Start infrastructure
docker-compose up -d

# 4. Install Python dependencies
pip install -r requirements.txt

# 5. Run producer
cd producer && python producer.py
```

**Start consumer (inside Spark container):**

```bash
docker exec -it ktech_spark_submit bash -c "spark-submit \
    --master spark://spark-master:7077 \
    --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.3 \
    --jars /opt/bitnami/spark/jars/postgresql-42.5.4.jar \
    /app/consumer/consumer.py"
```

**Access Grafana:** Navigate to `localhost:3000` (default credentials: admin/admin)

---

## Key Features

**High-throughput streaming:** Kafka topics with 4 partitions each. Consumer group handles 5,000+ events/sec with backpressure control (`maxOffsetsPerTrigger=10000`).

**Hybrid storage architecture:** InfluxDB for fast time-series queries on OHLCV data. PostgreSQL with composite indexes for metadata lookups by symbol, date, sector, and industry.

**Fault tolerance:** Consumer group checkpointing at `/tmp/spark-checkpoint`. Automatic recovery from failures. Zookeeper coordination for Kafka cluster state.

**Real-time alerting:** Configurable rule engine evaluates each batch against thresholds. Alerts logged to `logs/alerts.log` with severity levels (INFO, MEDIUM, HIGH, CRITICAL).

**Production monitoring:** Grafana dashboards for candlestick charts, volume gauges, and real-time line graphs. Connected directly to InfluxDB data source.

**Docker-based deployment:** Single `docker-compose up` launches entire stack. No manual service configuration. Isolated network for secure inter-service communication.

**Horizontal scalability:** Add Kafka partitions and Spark worker nodes to increase throughput. Consumer group automatically rebalances.

---

## Project Structure

```
StockStream/
├── producer/
│   ├── producer.py                # Main producer, publishes OHLCV to Kafka
│   ├── producer_utils.py          # Kafka client utilities
│   └── stock_info_producer.py     # Metadata producer (sector, industry)
├── consumer/
│   ├── consumer.py                # Spark Structured Streaming consumer
│   ├── InfluxDBWriter.py          # InfluxDB line protocol writer
│   └── alert_rules.py             # Rule engine (price, volume, volatility)
├── script/
│   ├── initdb.sql                 # PostgreSQL schema initialization
│   └── utils.py                   # Database utilities
├── logs/                          # Application logs
│   ├── alerts.log
│   ├── producer.log
│   └── consumer.log
├── docs/                          # GitHub Pages landing site
├── images/                        # Architecture diagrams
├── docker-compose.yaml            # Full stack orchestration
├── requirements.txt               # Python dependencies
├── pyproject.toml                 # Project metadata
└── .env.example                   # Environment variable template
```

---

## Configuration

### Environment Variables

Create `.env` file in project root:

| Variable | Description | Example |
|----------|-------------|---------|
| `STOCKS` | Comma-separated stock symbols | `AAPL,MSFT,GOOGL,AMZN` |
| `INFLUXDB_BUCKET` | InfluxDB bucket name | `stock-data` |
| `INFLUXDB_MEASUREMENT` | InfluxDB measurement name | `stock_prices` |
| `INFLUX_ORG` | InfluxDB organization | `my-org` |
| `INFLUX_TOKEN` | InfluxDB authentication token | `your-token-here` |
| `POSTGRES_USER` | PostgreSQL username | `stockuser` |
| `POSTGRES_PASSWORD` | PostgreSQL password | `your-password` |
| `POSTGRES_DB` | PostgreSQL database name | `stockdb` |

### Alert Rule Thresholds

Edit `consumer/alert_rules.py` to customize alert conditions:

```python
# Price drop detection
PriceDropAlert(threshold_percent=5.0)

# Price spike detection
PriceSpikeAlert(threshold_percent=5.0)

# Volume anomaly detection
HighVolumeAlert(threshold_volume=1000000)

# Volatility monitoring
VolatilityAlert(threshold_percent=3.0)
```

### Performance Tuning

Spark consumer options in `consumer/consumer.py`:

```python
# Backpressure control
.option("maxOffsetsPerTrigger", 10000)

# Consumer group (enables fault tolerance)
.option("kafka.group.id", "stock-stream-consumer-group")

# Starting offset for new consumer groups
.option("startingOffsets", "earliest")
```

Kafka topic configuration in `docker-compose.yaml`:

```yaml
KAFKA_NUM_PARTITIONS: 4        # Parallelism per topic
KAFKA_DEFAULT_REPLICATION_FACTOR: 1
```

---

## Development

### Running Locally

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f kafka
docker-compose logs -f spark-master

# Restart specific service
docker-compose restart spark-master

# Stop all services
docker-compose down
```

### Testing Producer

```bash
cd producer
python producer.py

# Check Kafka topics
docker exec -it ktech_kafka kafka-topics.sh --list --bootstrap-server localhost:9092

# Consume from topic (debugging)
docker exec -it ktech_kafka kafka-console-consumer.sh \
    --bootstrap-server localhost:9092 \
    --topic real-time-stock-prices \
    --from-beginning
```

### Database Access

**PostgreSQL:**

```bash
docker exec -it ktech_postgres psql -U stockuser -d stockdb

# Check metadata
SELECT symbol, sector, industry FROM stocks LIMIT 10;
```

**InfluxDB:**

Navigate to `localhost:8086`, login with credentials, and query via UI or Flux language.

---

## Troubleshooting

**Kafka consumer lag increasing**
- Check Spark worker resources (CPU, memory)
- Increase `maxOffsetsPerTrigger` in consumer.py
- Add more Spark workers via docker-compose scale

**InfluxDB write failures**
- Verify `INFLUX_TOKEN` in .env matches InfluxDB setup
- Check InfluxDB logs: `docker-compose logs influxdb`
- Confirm bucket exists in InfluxDB UI (localhost:8086)

**Producer not fetching data**
- Validate stock symbols in `STOCKS` env variable
- Check yfinance API rate limits (Yahoo Finance may throttle)
- Review `logs/producer.log` for errors

**Spark job fails with "Checkpoint directory not found"**
- Ensure `/tmp/spark-checkpoint` has write permissions inside container
- Delete checkpoint dir and restart if schema changed: `docker exec -it ktech_spark_submit rm -rf /tmp/spark-checkpoint`

**Grafana shows no data**
- Verify InfluxDB data source configured in Grafana (Settings > Data Sources)
- Check InfluxDB contains data: query `stock_prices` measurement
- Confirm time range in Grafana dashboard matches data timestamps

---

## Roadmap

- [ ] Support for additional data sources (Alpha Vantage, Polygon.io)
- [ ] Machine learning integration for price prediction (Prophet, LSTM)
- [ ] WebSocket API for real-time client connections
- [ ] Redis caching layer for frequently accessed metadata
- [ ] Kubernetes deployment manifests (Helm charts)
- [ ] Automated backtesting framework
- [ ] Support for options and futures data
- [ ] Alert notification via Slack/email webhooks
- [ ] Historical data replay for testing

---

## Contributing

Contributions welcome. To contribute:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/your-feature`)
3. Commit changes (`git commit -m 'Add feature description'`)
4. Push to branch (`git push origin feature/your-feature`)
5. Open Pull Request

Please ensure code follows existing style and includes tests where applicable.

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Built By

**Puneeth Kotha**  
NYU MS Computer Engineering, 2026  
[GitHub](https://github.com/puneethkotha) · [LinkedIn](https://linkedin.com/in/puneeth-kotha-760360215) · [Website](https://puneethkotha.com)

---

## Acknowledgments

- Apache Software Foundation for Kafka and Spark
- InfluxData for InfluxDB time-series database
- Grafana Labs for visualization platform
- Yahoo Finance for market data API

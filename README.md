# Dynasty Fantasy Football Analytics Platform

A full stack fantasy football analytics platform built to analyze dynasty leagues, identify cross-league trade opportunities, and automate interactions with the Sleeper platform.

This project was created to solve a problem I ran into while managing multiple dynasty leagues. Instead of manually searching through hundreds of rosters and thousands of transactions, the application collects league data, stores it in a relational database, and generates actionable trade insights in seconds.

The project started as a Google Sheet with Apps Script and has grown into a distributed web application with asynchronous data pipelines, background workers, REST APIs, authentication, and a React frontend.

---

## Features

- User authentication with linked Sleeper accounts
- Asynchronous data ingestion from the Sleeper API
- Background processing with distributed workers
- PostgreSQL database with normalized schemas
- Cross-league trade signal generation
- Player valuation engine based on historical production and aging curves
- League, roster, transaction, and player analytics
- Trade proposal and waiver claim automation
- React dashboard for browsing analytics
- Redis caching to reduce API calls and improve response times

---

## Tech Stack

### Backend

- Python
- FastAPI
- SQLModel
- SQLAlchemy
- PostgreSQL
- Alembic
- TaskIQ
- Redis
- HTTPX
- Pydantic

### Frontend

- React
- TypeScript
- Vite
- React Router

### Infrastructure

- Docker
- Docker Compose

---

## How It Works

1. Users connect their Sleeper account.
2. Background workers synchronize leagues, rosters, players, users, drafts, and transactions.
3. Data is normalized and stored in PostgreSQL.
4. Analytics services process the data to generate player values and trade signals.
5. The frontend displays results through the FastAPI API.

---

## Analytics

The platform currently includes:

- Cross-league trade signal detection
- Historical transaction analysis
- Dynasty player valuation
- Expected career value modeling
- Aging curve adjustments
- League activity tracking
- Player ownership analysis
- Draft pick valuation

Additional analytics are continuously being added.

---

## Performance

The application is designed around asynchronous processing and distributed workers.

Some optimizations include:

- Concurrent API requests with HTTPX
- Bulk database inserts and upserts
- Redis caching
- Background synchronization jobs
- Batched processing
- Connection pooling

These improvements reduced large synchronization jobs from over 30 minutes to under 30 seconds while allowing analytics across thousands of leagues.

---

## Goals

Some upcoming work includes:

- Additional dynasty valuation models
- More advanced trade recommendations
- Historical player trend visualization
- League comparison dashboards
- CI/CD deployment pipeline
- Cloud deployment

---

## Why I Built This

As a dynasty fantasy football player, I wanted better tools for evaluating trades across multiple leagues.

Most existing tools only analyze a single league at a time. I wanted something that could continuously collect data from thousands of leagues, analyze market trends, and surface opportunities that would be nearly impossible to find manually.

Building the platform also gave me an opportunity to learn and apply modern backend engineering practices including asynchronous programming, distributed task processing, REST API design, relational database modeling, Docker, and React.

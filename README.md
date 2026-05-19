# YouTube Analytics Dashboard 📊

**A Streamlit-powered application to harvest, store, and analyze YouTube channel data using the YouTube Data API v3, MongoDB, and PostgreSQL.**

<br />

## Table of Contents

1. [Key Technologies](#key-technologies)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Database Setup](#database-setup)
5. [Usage](#usage)
6. [Features](#features)
7. [Contact](#contact)

<br />

## Key Technologies

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| YouTube Data API v3 | Fetching channel, video & comment data |
| MongoDB | NoSQL data lake / staging storage |
| PostgreSQL | Structured SQL data warehouse |
| Pandas | Data cleaning and transformation |
| Plotly | Interactive dark-themed charts |
| Streamlit | Web application interface |

<br />

## Prerequisites

Before running the app, make sure the following are installed and running on your machine:

- **Python 3.8+**
- **MongoDB** running locally at `mongodb://localhost:27017/`
- **PostgreSQL** running locally with:
  - host: `localhost`
  - user: `postgres`
  - password: `root`
  - database: `youtube` *(create this manually before running)*
- A **YouTube Data API v3 key** — [How to get one ▶](https://youtu.be/SwSbnmqk3zY?t=79)

<br />

## Installation

Clone the repository:
```bash
git clone https://github.com/ibhavanaa/Youtube-Data-Harvesting-and-Warehousing.git
cd Youtube-Data-Harvesting-and-Warehousing
```

Install required packages:
```bash
pip install -r requirements.txt
```

Or install individually:
```bash
pip install google-api-python-client pymongo pandas psycopg2 streamlit plotly streamlit-option-menu
```

<br />

## Database Setup

### PostgreSQL
Create the database before running the app:
```sql
CREATE DATABASE youtube;
```
The app will automatically create the required tables (`channel`, `playlist`, `video`, `comment`) on first run.

### MongoDB
No manual setup needed — the app uses `mongodb://localhost:27017/` by default and creates collections automatically.

> If you use MongoDB Atlas or a custom URI, update the connection string in the `mongodb` class inside `app.py`.

<br />

## Usage

Run the Streamlit app:
```bash
streamlit run app.py
```

Access it in your browser at: `http://localhost:8501`

<br />

## Features

### 🔍 Data Collection
Retrieve comprehensive data from any YouTube channel using the YouTube Data API v3. Collects:
- Channel info (name, description, subscribers, views, country)
- Playlists
- Videos (title, views, likes, comments, duration, caption status)
- Top-level comments

### 🍃 Store to MongoDB
Harvested data is staged in a MongoDB collection. Supports overwrite if the channel already exists.

### 🗄️ Migrate to PostgreSQL
Migrate channel data from MongoDB into a structured PostgreSQL data warehouse with normalized tables for channels, playlists, videos, and comments.

### 📊 Data Analysis & Visualization
Interactive charts and tables powered by **Plotly Dark theme**:

**Channel Analysis:**
- Channel-wise playlist count (pie chart)
- Channel-wise video count (bar chart)
- Date-range filtered published videos
- Subscriptions, views, likes, comments, and duration breakdowns

**Video Analysis:**
- Top videos by views, likes, comments, and duration
- 🆕 **Engagement Rate** — `(likes + comments) / views × 100` for every video
- Filterable by individual channel or across all channels

### 🧮 SQL Queries (10 built-in)
Pre-built analytical queries including:
- Top 10 most viewed videos
- Videos with highest likes/comments
- Channel-wise total views and subscriber counts
- Average video durations per channel
- Videos published in a specific year

<br />

## Contact

📧 Email: [ibhavanachoudhary@gmail.com](mailto:ibhavanachoudhary@gmail.com)

🌐 LinkedIn: [Bhavana Choudhary](https://www.linkedin.com/in/bhavana-choudhary-a13290270/)

🐙 GitHub: [ibhavanaa](https://github.com/ibhavanaa)

Feel free to reach out for questions, suggestions, or collaboration!

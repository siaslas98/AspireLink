## Project Overview

**Internship Support Tool** is a web-based platform designed to help university students—especially those in technical fields—stay organized and motivated during the internship application process. The platform combines two key features:

- **Watchlist Notifications** – Students can track specific companies and receive alerts when new internship opportunities are posted.
- **Motivational Tools** – Check-ins, reminders, and gamified elements like streaks and badges encourage consistent progress.

This tool aims to reduce the stress of internship hunting by centralizing opportunity tracking, boosting accountability, and supporting students' long-term career growth.

## Basic Setup

### Clone the repository

```bash
git clone https://github.com/siaslas98/internship-support-tool.git
cd internship-support-tool
```

### Setup Environment Variables

- Create a `.env` file in the root of the repository and add the following line:
  `DATABASE_URL=postgresql://myuser:mypassword@db:5432/internship_db`
  **Note: this runs with docker, no need to install PostgreSQL separately**

### Run the app using Docker

- Make sure Docker is installed and running on your machine. Then run:
  ```bash
  docker compose up --build
  ```
  - This will:
    - Start the FastAPI app on http://localhost:8001
    - Start a PostgreSQL database
    - Mount code for live reloading

### Initialize the database

In another terminal:

```bash
docker exec -it internship-support-tool-web-1 python scripts/init_database.py
```

## Some Important Commands:

- Access the database
  ```bash
  docker exec -it internship-support-tool-db-1 psql -U myuser -d internship_db
  ```
- After accessing database, clear all entries in the users and watchlist table and reset id to 0
  ```
  TRUNCATE watchlist_items, users CASCADE;
  ```

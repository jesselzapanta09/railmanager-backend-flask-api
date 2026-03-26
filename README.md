# MSIT 114 - Activity 19 - Improved Flask API with Front-End

This project is the **backend API** for the RailManager system, built using Flask, flask-mysqldb, PyJWT, and flask-cors to handle data processing, authentication, email verification, and image management for users and train entities.

## Requirements

Before running the project, install:

- Python 3.10 or newer
- MySQL server
- `pip`

## Installation & Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/jesselzapanta09/railmanager-backend-flask-api.git
cd railmanager-backend-flask-api
```

### Step 2: Install Dependencies

```cmd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Step 3: Import the Database

1. Open your MySQL client (e.g., MySQL Workbench, phpMyAdmin, or CLI).
2. Create a new database:
```sql
   CREATE DATABASE trainappdb;
```
3. Import the provided SQL file(**trainappdb.sql**)


### Step 4: Run the Server

```bash
python run.py
```

The API should now be running at `http://localhost:5000`.

---

# System Feafure using Flask API

1. CRUD with image - assigned entity.
2. User profile — Can modify user information with picture.
3. User registration using email — Send verification link through email.
4. Verify user using email address — Cannot log in if account is not verified.
5. Forgot password using email — Send a reset password link through email.
6. Log in and log out using authorization.



## Author

**Jessel Zapanta** — MSIT 114
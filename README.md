# RailManager Flask API

Backend API built with Flask for authentication, users, and train management.

## Requirements

Before running the project, install:

- Python 3.10 or newer
- MySQL server
- `pip`

## Clone the project

```bash
git clone <your-repository-url>
cd train-flask-api-v5
```

## Install dependencies

It is recommended to use a virtual environment.

### Windows CMD

```cmd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Environment variables

Create a `.env` file in the project root and add the required values:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=your_database
JWT_SECRET=your_jwt_secret
PORT=5000
ALLOWED_ORIGINS=http://localhost:3000
```

## Run the server

```bash
python run.py
```

The API will start on:

```text
http://127.0.0.1:5000
```

## Health check

Open this URL in your browser after starting the server:

```text
http://127.0.0.1:5000/health
```

Expected response:

```json
{
  "success": true,
  "message": "API is running"
}
```

## Main routes

- `GET /` - API welcome route
- `GET /health` - health check
- `POST /api/...` - auth endpoints
- `GET /api/trains/...` - train endpoints
- `GET /api/users/...` - user endpoints

## Notes

- Uploaded files are stored in the `uploads/` directory.
- CORS origins are controlled by `ALLOWED_ORIGINS`.
- Database connection values are loaded from `.env`.

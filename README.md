# ds-vault

**ds-vault** is a secure, full-stack data vault application designed to safely store and encrypt sensitive information. It leverages a modern tech stack consisting of a Next.js frontend and a robust Django backend.

## 🚀 Features

- **Secure Data Storage**: Encrypts and securely stores user data safely.
- **Normal Encryption**: Utilizes AES-GCM with a random key for standard security.
- **Advanced Encryption**: Employs AES-GCM with a user-provided seed-phrase-derived key and stores a cryptographic record on a blockchain for enhanced security and immutability.
- **Robust Authentication**: Supports Two-Factor Authentication (2FA), Google OAuth, and secure JWT-based verification.
- **Modern UI/UX**: Built with Next.js 16, Tailwind CSS, and Framer Motion for smooth animations and a responsive design.

## 🏗️ Architecture

- **Frontend**: Next.js (React 19), Tailwind CSS, Framer Motion.
- **Backend**: Django (Python), SQLite (default, with robust persistent volume support in Docker).
- **Encryption Engine**: Custom AES-GCM encryption modules (`Encryption/` directory).
- **Blockchain Integration**: Custom blockchain components (`blockchain/` directory) for advanced encryption tracking.

## 🐳 Docker Setup (Recommended)

The easiest way to run the entire application (frontend, backend, database, and encryption services) is using Docker Compose. This ensures you have all the necessary dependencies isolated without needing to install them locally.

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) installed on your machine.
- [Docker Compose](https://docs.docker.com/compose/install/) installed.

### Run the Application

Navigate to the root directory of the project and execute the following command to build and start the containers:

```bash
docker compose up --build
```

This command will automatically:
1. Build the Django backend (`server/Dockerfile`) and start it on `http://localhost:8000`.
2. Build the Next.js frontend (`client/Dockerfile`) and start it on `http://localhost:3000`.
3. Set up and mount persistent volumes for the SQLite database and the encrypted vault data.
4. Establish an internal network (`ds-vault-network`) for seamless communication between the Next.js client and the Django server.

You can now access the application by heading over to **http://localhost:3000** in your web browser. 

To stop the application, press `Ctrl+C` in your terminal or run:
```bash
docker compose down
```

## 💻 Manual Local Setup (Without Docker)

If you prefer to run the application locally without Docker, you can set up the services independently.

### 1. Backend (Django) Setup
Navigate to the `server` directory and set up the Python environment.

```bash
cd server
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### 2. Frontend (Next.js) Setup
Open a new terminal window, navigate to the `client` directory, and start the frontend development server.

```bash
cd client
npm install
npm run dev
```

The application is now up and running across `http://localhost:3000` (frontend) and `http://localhost:8000` (backend).

## ☁️ Deploying the Backend to Render

The backend is production-ready and can be deployed to [Render](https://render.com) as a Docker-based web service.

### Prerequisites
- Your project pushed to a GitHub repository.
- A free [Render](https://render.com) account connected to your GitHub.

### Step-by-Step

**1. Create a New Web Service on Render**
- Go to [Render Dashboard](https://dashboard.render.com) → **New → Blueprint** (if using `render.yaml`) OR **New → Web Service**.
- Select your GitHub repo.
- If prompted for runtime, choose **Docker**.
- Set the **Dockerfile Path** to `server/Dockerfile` and the **Build Context** to `.` (repo root).

**2. Add a PostgreSQL Database**
- In Render Dashboard → **New → PostgreSQL**.
- Name it `ds-vault-db`, select the **Free** plan, and create it.
- Copy the **Internal Database URL** from its dashboard.

**3. Set Environment Variables**
In your web service's **Environment** tab, add the following:

| Variable | Value |
|---|---|
| `SECRET_KEY` | A long random string (Render can generate one) |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `your-service-name.onrender.com` |
| `DATABASE_URL` | Internal connection string from your Render Postgres DB |
| `CORS_ALLOWED_ORIGINS` | `https://your-frontend-url.com` |
| `EMAIL_HOST_USER` | Your Gmail address |
| `EMAIL_HOST_PASSWORD` | Your Gmail App Password |

> **Tip**: See `.env.render.example` in this repo for a full reference of all variables.

**4. Deploy**
Click **Save and Deploy**. Render will:
1. Build the Docker image (copies `server/`, `Encryption/`, `blockchain/` into the container).
2. Run `python manage.py migrate` and `collectstatic`.
3. Start the app with `gunicorn` on port `8000`.

Your API will be live at:
```
https://your-service-name.onrender.com/api/
```

**5. (Optional) Using `render.yaml` Blueprint**
A `render.yaml` file is included at the repo root. You can use **New → Blueprint** in Render to auto-provision both the web service and the PostgreSQL database in one click. After creating via Blueprint, manually set `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` in the environment tab since they are marked `sync: false` for security.

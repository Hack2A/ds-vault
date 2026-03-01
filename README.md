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

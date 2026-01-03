# Fashion Ecommerce

## Technology Stack and Features

- ⚡ [**FastAPI**](https://fastapi.tiangolo.com) for the Python backend API.
  - 🧰 [SQLModel](https://sqlmodel.tiangolo.com) for the Python SQL database interactions (ORM).
  - 🔍 [Pydantic](https://docs.pydantic.dev), used by FastAPI, for the data validation and settings management.
  - 💾 [PostgreSQL](https://www.postgresql.org) as the SQL database.
- 🚀 [React](https://react.dev) for the frontend.
  - 💃 Using hooks, [Vite](https://vitejs.dev), and other parts of a modern frontend stack.
- 🐋 [Docker Compose](https://www.docker.com) for development and production.
- 🔒 Secure password hashing by default.
- 🔑 JWT (JSON Web Token) authentication.
- 📫 Email based password recovery.
- 🚢 Deployment on AWS EC2 via Docker Compose, using Nginx to handle Let's Encrypt SSL certificates with Certbot.

## How To Use It
- Clone this repository manually, , set the name with the name of the project you want to use, for example `my-project`:
```bash
https://github.com/Matec76/fashion-ecommerce.git my-project
```
- Enter into the directory:
```bash
cd my-projcect
```

### Configure

You can then update configs in the `.env` files to customize your configurations.

### Generate Secret Keys

You have to change them with a secret key, to generate secret keys you can run the following command:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the content and use that as password / secret key.

### Requirements

* [Docker](https://www.docker.com/).
* [uv](https://docs.astral.sh/uv/) for Python package and environment management.

### General Workflow

- Build and start containers using Docker Compose.

```bash
docker compose up -d --build
```

Important: Ensure the container is fully up and running before continuing.

- Initialize Alembic and run migrations to create database tables.

```bash
docker exec backend alembic revision --autogenerate -m "baseline_initial"
```
- After creating the revision, run the migration in the database.

```bash
docker exec backend alembic upgrade head
```

- Restart Docker Compose services

```bash
docker compose down
docker compose up
```
- Once the services are running successfully and the following pages are accessible, the build process is complete.
  - Frontend: http://localhost:5173
  - Backend: http://localhost:8000/api/v1/docs
  - Database: http://localhost:8080

## License
This project is licensed under the MIT License.

# BookTracker Backend 

[SwaggerUI](https://book-registration.ddns.net/api/1.1.1/docs) 

[Redoc](https://book-registration.ddns.net/api/1.1.1/redoc)

<span style="font-size:16px; color:orange;">⚠️ Both URLs are deployed on AWS EC2. Due to cost-saving considerations, these services may not be continuously running.</span>


## Quick Start

1. **Config your own env variable**
- JWT_SECRET
```python
import secrets
>>> secrets.token_hex(16) # generates a heaxadecimal token and add this token in our .env file
```
- MAIL_PASSWORD

Follow this [guide](https://support.google.com/accounts/answer/185833) to create your own app passwords

- MAIL_USERNAME, MAIL_FROM, MAIL_FROM_NAME

Your **Gmail** Address

2. **Run the CLI**

```bash
git clone https://github.com/RobertChienShiba/BookTracker.git
```
```bash
cd BookTracker/
```
```bash
docker compose -f ./docker-compose.yml -f ./docker-compose-development.yml -p dev up -d
```


## API (REST)
- `/auth` : Include User Registration, login & logout, Account verification, Get User profile, Password reset & verification.
- `/books` : Book CRUD
- `/reviews` : Review CRUD
- `/tags` : Tag CRUD
> More API details can be found in the FastAPI-provided Swagger UI: `http://localhost:8000/api/1.1.1/docs`.

## Database
- ORM: SQLAlchemy
    - sqlite3
    - aiosqlite
    - alembic

    ![DB Arch.](https://imgur.com/MP8ncy8.png)

- Redis: aioredis

## Authentication & Authorization
- JWT: pyJWT 

    ![Auth](https://imgur.com/tjNbxhH.png)
- RBAC
    - USER
    - ADMIN


## Background Task + Message Queue
- Email Verification: FastAPI-Mail
- Redis
- Dramatiq
> Create 16 workers (based on CPU cores), each with its own event loop to handle tasks non-blocking. This setup efficiently utilizes multi-core CPUs and supports high-concurrency for I/O-bound tasks. Detailed operation logs can be found in `worker.log`

## CI/CD
- [Gitlab CI/CD](https://gitlab.com/RobertChienShiba/BookTracker)
- Pytest

## Deploy
- DNS: No-ip
- SSL: Let's Encrypt
- AWS EC2 & Elastic IP
- Nginx
- Docker


## Reference
- [Ssali Jonathan YT FastAPI Course](https://www.youtube.com/watch?v=TO4aQ3ghFOc)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Dramatiq](https://dramatiq.io/)
- [Docker Compose](https://docs.docker.com/compose/)
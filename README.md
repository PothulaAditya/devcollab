# DevCollab

A collaborative project-management backend where developers can create projects, recruit team members, assign tasks, chat in real time, and manage everything through a clean REST API. Think of it as the backend powering a mix of GitHub, Trello, and Slack.

**Live API Docs:** [devcollab.adityapothula.dev/docs](https://devcollab.adityapothula.dev/docs)

The live link opens an interactive Swagger UI where you can try every endpoint directly in the browser.

---

## Features

- **Authentication** — JWT-based auth with registration, login, email verification, password reset, and refresh tokens (with server-side revocation on logout).
- **Account management** — Account deactivation/reactivation with password re-authentication, and login-based auto-reactivation.
- **Projects** — Full CRUD with ownership, search, and status filtering. Project details are cached in Redis for fast reads.
- **Applications** — Developers apply to join projects; owners accept or reject. Acceptance triggers an automated email and auto-adds the applicant as a member.
- **Project members** — View, promote (member ↔ admin), and remove members with role-based permissions.
- **Tasks** — Task creation and assignment with a three-level permission system (owner, admin, and assigned user, where the assigned user can only update status).
- **Comments** — Task-scoped comments where only the author can delete their own.
- **Real-time chat** — WebSocket-based live chat, scoped per project, with token authentication, message persistence, and chat history. Multiple projects chat simultaneously and in isolation.
- **Background jobs** — Email sending handled asynchronously via Celery workers, so requests never block on email delivery.
- **Admin dashboard** — Role-gated admin routes for viewing all users and projects, banning/unbanning users, promoting users to admin, and platform statistics.

---

## Tech Stack

- **Framework:** FastAPI
- **Database:** PostgreSQL with SQLAlchemy ORM
- **Migrations:** Alembic
- **Caching & message broker:** Redis
- **Background tasks:** Celery
- **Real-time:** WebSockets
- **Auth:** JWT (access + refresh tokens), OAuth2 password flow
- **Email:** Resend API (with a verified sending domain)
- **Containerization:** Docker & Docker Compose
- **Deployment:** Railway (with managed PostgreSQL and Redis)

---

## Architecture Highlights

- **Cache-aside pattern with invalidation** — Project reads hit Redis first; writes invalidate the cache so data never goes stale. A TTL acts as a safety net.
- **Refresh token revocation** — Refresh tokens are stored in the database, so logout truly invalidates a session rather than relying on token expiry alone.
- **Layered permissions** — Permissions are enforced per resource (project ownership, membership roles, task assignment, comment authorship) and gated through reusable dependencies.
- **Asynchronous email** — Email is offloaded to a Celery worker, keeping API responses fast and resilient to email-provider latency.
- **Per-project WebSocket rooms** — A connection manager keys live connections by project, so messages broadcast only within their project and many projects can chat at once without interference.

---

## Running Locally

The entire system (API, PostgreSQL, Redis, and the Celery worker) runs with Docker Compose.

### Prerequisites
- Docker and Docker Compose installed
- A `.env` file with the required environment variables (see below)

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/PothulaAditya/devcollab.git
cd devcollab

# 2. Create a .env file (see Environment Variables below)

# 3. Build and start all services
docker-compose up --build

# 4. In a second terminal, run the database migrations
docker-compose exec web alembic upgrade head
```

The API will be available at `http://localhost:8000/docs`.

### Environment Variables

```
DATABASE_HOSTNAME=db
DATABASE_USERNAME=your_username
DATABASE_PASSWORD=your_password
DATABASE_PORT=5432
DATABASE_NAME=devcollab
REDIS_URL=redis://redis:6379
SECRET_KEY=your_jwt_secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
RESEND_API_KEY=your_resend_api_key
```

---

## API Overview

All endpoints are documented and testable via the interactive Swagger UI at `/docs`. Major route groups:

- `/user` — registration, verification, password reset, deactivation
- `/login`, `/refresh`, `/logout` — authentication and token management
- `/project` — project CRUD, search, and filtering
- `/application` — applying to and managing project applications
- `/project/{id}/members` — member management
- `/project/{id}/task` — task creation and management
- `/project/{id}/task/{id}/comment` — task comments
- `/ws/project/{id}` — real-time chat (WebSocket)
- `/admin` — admin dashboard routes

---

## Roadmap

DevCollab is an actively evolving project. Phase 1 (a complete, deployed backend) is done; the following are planned for future phases:

- **Automated testing** — a pytest suite covering the core flows and edge cases, to protect against regressions as new features are added.
- **Pagination** — cursor or offset pagination for projects, tasks, and chat history (currently full lists are returned).
- **Google / OAuth login** — social login alongside the existing email-password auth.
- **Formal role-permission system** — a centralized role → permission map to replace per-route permission checks as the role model grows.
- **Deeper admin tooling** — audit logs, analytics, and more granular moderation.
- **WebSocket scaling** — Redis Pub/Sub across multiple server instances to scale real-time chat horizontally.
- **Frontend** — a web client consuming this API.

## Known Limitations

A few intentional simplifications remain, scoped for later work:

- **Application lifecycle** — applications are not automatically cleaned up after being accepted or rejected; a tidy-up step is planned.
- **Email deliverability** — the sending domain is newly verified, so verification emails may initially land in spam until the domain builds sending reputation.
- **No pagination yet** — list endpoints currently return full result sets.

These are tracked deliberately rather than hidden — the project is open and continuing to improve.

## Project Status

DevCollab's first phase is fully built, tested, containerized, and deployed live. It was developed feature-by-feature with a focus on understanding each concept (authentication flows, caching, background jobs, real-time communication, and deployment) rather than just assembling code. Development is ongoing.

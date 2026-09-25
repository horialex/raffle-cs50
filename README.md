# Raffles
#### Video Demo: https://youtu.be/u1BL4U2cr0U
#### Description:

## The idea

Buying and selling products online usually happens at a fixed price or through an auction. Either way, someone who wants an item has to pay its full price to get it. This project explores a different approach: users join a raffle by buying tickets for a small price, and each ticket gives them a chance to win the product.

Raffles is a web platform where people create raffles for products they own and other people buy tickets to win them. The creator sets a ticket price, a minimum number of tickets that must be sold and a due date. When the due date passes, the platform draws a winner. The project also follows the prize after the draw: the winner and the creator exchange addresses, a courier delivers the prize, and the winner either accepts it or files a complaint that an administrator resolves.

The application is written in Python with Flask, uses MySQL through SQLAlchemy, renders its pages with Jinja2 and Bootstrap, and runs in Docker. It is my final project for CS50.

## What a user can do

- **Register, log in and manage a profile**, including a profile picture, password change and account deletion.
- **Create a raffle** with one to three products, each with up to three images. A new raffle is a *DRAFT* that can still be edited or deleted. Once *STARTED* it becomes *ACTIVE* and is locked.
- **Browse, filter and search active raffles** from other users, and **buy tickets** up to the per-user limit the creator chose.
- **Follow their tickets** on a "My tickets" dashboard and **receive in-app messages** about everything that affects them.
- **Deliver or receive a prize**, and accept or contest it after it arrives.
- **Administrators** can see every user, raffle, delivery and contestation, and decide the outcome of contested prizes.

## How a raffle is settled

Settlement runs as a command-line job, `flask process-raffles`, meant to be run daily (for example by cron). It finds every active raffle past its due date:

- **Failed raffles** (not enough tickets sold): the raffle and its tickets are *CANCELLED*, buyers are refunded and everyone is notified.
- **Successful raffles**: the raffle is *WON*, one ticket is drawn at random as *WINNER*, the rest become *LOST*, and a prize delivery is created.

The delivery then moves through `pending_delivery_address` → `pending_pickup_address` → `waiting_for_shipment` → `prize_sent` → `prize_delivered` → `prize_accepted`, and the raffle becomes *COMPLETED*. If the winner contests the prize instead, an admin either dismisses the complaint (the creator is paid) or accepts it (all tickets are refunded, the raffle ends as *REJECTED_PRIZE* and the prize is returned to the creator).

## Files

- **`api/app.py`** creates the Flask app. It sets up the database, sessions, CSRF protection, error pages, blueprints and the `process-raffles` command.
- **`api/config.py`** holds the configuration and business rules (product and image limits, ticket limits, upload sizes, payment and shipping simulation switches).
- **`api/auth.py`** and **`api/users.py`** handle login and logout, registration, profiles, account deletion, the message inbox and the admin user list.
- **`api/raffles.py`** covers creating, editing, deleting, starting, listing and viewing raffles.
- **`api/checkout.py`** is the ticket purchase flow, and **`api/tickets.py`** is the "My tickets" dashboard.
- **`api/prize_delivery.py`** lets the winner and creator enter addresses and the winner accept or contest the prize. **`api/contestation.py`** lets admins resolve contestations.
- **`api/jobs/raffles_processor.py`** is the settlement job.
- **`api/services/`** contains the delivery state machine (`prize_delivery_service.py`), the simulated courier (`courier_service.py`) and notifications (`notifications_service.py`).
- **`api/models/`**, **`api/constants/`** and **`api/forms/`** hold the SQLAlchemy models, the status enums and the WTForms classes.
- **`api/utils/`** has helpers for login, validation and file uploads. **`api/migrations/`** has the database migrations.
- **`templates/`** and **`static/`** hold the Jinja2 pages, the CSS, the images and `script.js`.
- **`scripts/`** has seed scripts that create a won or contested raffle for manual testing.
- **`Dockerfile`** and **`docker-compose.yml`** run MySQL and the web app in containers.

## Design choices

**Technologies** I kept the stack close to what CS50 teaches so I could focus on the rules of the platform instead of a separate API and front end. WTForms and Bootstrap-Flask handle form rendering, validation and CSRF protection.

**All-or-nothing settlement** Settling a raffle touches the raffle, its tickets, a delivery record and many messages. Each raffle is settled in one database transaction, so a failure rolls everything back. There is never, for example, a *WON* raffle with no winner.

**Messaging** In-app messages are saved in the same transaction as the change they describe. Email and SMS are sent only after the commit, so nobody is told about a change that was rolled back.

**Delivery state machine** The allowed status changes live in one table, `ALLOWED_TRANSITIONS`, and every change goes through `transition()`. That function refuses illegal moves and writes an audit log row.

**Winner draw** The winner is chosen with `secrets.choice`, which uses a cryptographically secure random generator, so the result cannot be predicted.

**Simulated payments and shipping.** Real payment and courier integrations were out of scope, so each is simulated behind a config switch where a real provider (e.g. Mangopay) could be added later.

**File uploads** Uploaded images get a UUID prefix plus `secure_filename`, so files never overwrite each other or escape the upload folder.

## Running the project and commands

```bash
cp .env.example .env                                            # fill in the MySQL credentials and APP_SECRET
docker compose up -d                                            # start the containers
docker compose exec web flask db upgrade -d ./api/migrations    # create the tables (first run only)
docker compose exec web flask process-raffles                   # settle raffles past their due date
```

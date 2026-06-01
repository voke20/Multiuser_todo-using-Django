# Note Taking API

## Description
A REST API for a multi-user note taking application built with Django and Django REST Framework. Users can create, read, update and delete notes, and share notes with other users.

## Tech Stack
- Python
- Django
- Django REST Framework
- djangorestframework-simplejwt
- PostgreSQL
- Docker

## Setup Instructions

### Prerequisites
- Docker
- Python 3.x

### Installation
1. Clone the repository
   git clone https://github.com/voke20/Multiuser_todo-using-Django.git

2. Create a .env file in the root directory and add:
   SECRET_KEY=your_secret_key
   POSTGRES_DB=your_db_name
   POSTGRES_USER=your_db_user
   POSTGRES_PASSWORD=your_db_password
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432

3. Start PostgreSQL container
   docker compose up -d

4. Install dependencies
   pip install -r requirements.txt

5. Run migrations
   python manage.py migrate

6. Start the server
   python manage.py runserver

## API Endpoints

### Authentication
- POST /api/auth/register/
- POST /api/auth/login/
- POST /api/auth/token/refresh/
- POST /api/auth/logout/

### Notes
- GET /api/notes/
- POST /api/notes/
- GET /api/notes/<id>/
- PUT /api/notes/<id>/
- PATCH /api/notes/<id>/
- DELETE /api/notes/<id>/

### Note Sharing
- POST /api/notes/<id>/share/
- DELETE /api/notes/<id>/share/<user_id>/
- GET /api/notes/shared/
- GET /api/notes/my-shared/

## Running Tests
python manage.py test authenticate
python manage.py test note

## API Documentation
Visit /api/docs/ for interactive Swagger documentation
# Note Taking API

## Description
A REST API for a multi-user note taking application built with Django and Django REST Framework. Users can create, read, update and delete notes, share notes with other users, upload file attachments and send notes via email.

## Tech Stack
- Python
- Django
- Django REST Framework
- djangorestframework-simplejwt
- PostgreSQL
- Docker
- CKEditor (RichTextField)
- python-magic (file type detection)

## Setup Instructions

### Prerequisites
- Docker
- Python 3.14

### Installation
1. Clone the repository
   git clone https://github.com/voke20/Multiuser_todo-using-Django.git

2. Create a .env file based on .env.example
   cp .env.example .env
   
3. Update .env with your own values

4. Build and run with Docker
   docker compose up --build

5. Visit http://localhost:8000/api/docs/ for API documentation

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

### Categories
- GET /api/notes/categories/
- POST /api/notes/categories/
- GET /api/notes/categories/<id>/
- PUT /api/notes/categories/<id>/
- DELETE /api/notes/categories/<id>/

### Note Sharing
- POST /api/notes/<id>/share/
- DELETE /api/notes/<id>/share/<user_id>/
- GET /api/notes/shared/
- GET /api/notes/myshared/

### File Uploads
- POST /api/notes/<id>/uploads/
- GET /api/notes/<id>/uploads/

### Email
- POST /api/notes/<id>/send-email/

## Features
- JWT Authentication
- Custom User Model (email + phone login)
- Note Categories
- Note Pinning
- File Uploads (PNG, JPEG, JPG, PDF, TXT)
- Auto file type detection
- Note Sharing
- Send notes via email (SMTP)
- Search/filter notes
- Swagger API documentation at /api/docs/

## Running Tests
python manage.py test authenticate
python manage.py test note

## Environment Variables
See .env.example for required variables
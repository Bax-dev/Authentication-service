# TSES Authentication Service

A comprehensive email-based authentication service built with Django, featuring OTP authentication, JWT tokens, Redis-backed rate limiting, asynchronous processing with Celery, and complete OpenAPI documentation.

## Features

- **Email-based OTP Authentication**: Secure one-time password authentication via email
- **JWT Token Management**: Access and refresh token implementation
- **Redis-backed Rate Limiting**: Sliding window rate limiting for API protection
- **Asynchronous Processing**: Celery-based background tasks for email sending
- **Comprehensive Audit Logging**: Complete audit trail for all authentication events
- **OpenAPI Documentation**: Full Swagger/ReDoc API documentation
- **PostgreSQL Database**: Production-ready database backend
- **Docker Ready**: Easy deployment with Docker and docker-compose

## Quick Start

### Option 1: Docker Compose (Recommended)

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd tses_app
   ```

2. **Run with Docker Compose:**
   ```bash
   docker compose up --build
   ```

   That's it! The application will be available at `http://localhost:8000`

   **Services included:**
   - **Web App**: Django application on port 8000
   - **PostgreSQL**: Database
   - **Redis**: Cache and message broker
   - **Celery Worker**: Background task processing

   **Django Management Commands in Docker:**
   ```bash
   # Run commands inside the web container
   docker compose exec web python manage.py [command]

   # Examples:
   docker compose exec web python manage.py makemigrations
   docker compose exec web python manage.py migrate
   docker compose exec web python manage.py createsuperuser
   ```

### Option 2: Local Development

#### Prerequisites

- Python 3.12+
- pip
- Git

#### Setup

1. **Clone and setup:**
   ```bash
   git clone https://github.com/Bax-dev/Authentication-service.git
   cd tses_app
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Local development uses SQLite** (automatically configured):
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py createsuperuser
   ```

3. **Start services:**
   ```bash
   # Terminal 1: Django development server
   python manage.py runserver

   # Terminal 2: Celery worker (requires Redis)
   # Install Redis locally or use Docker for Redis only:
   # docker run -d -p 6379:6379 redis:7-alpine
   celery -A tses_app worker --loglevel=info
   ```

4. **Access the application:**
   - **Web App**: http://localhost:8000
   - **API Docs**: http://localhost:8000/api/schema/swagger-ui/
- Redis

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd tses_app
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**

   Create a `.env` file or set environment variables:

   ```bash
   # Database
   DB_NAME=tses_app
   DB_USER=postgres
   DB_PASSWORD=your_password
   DB_HOST=localhost
   DB_PORT=5432

   # Redis
   REDIS_URL=redis://localhost:6379/0

   # Celery
   CELERY_BROKER_URL=redis://localhost:6379/0
   CELERY_RESULT_BACKEND=redis://localhost:6379/0

   # Email (configure for your SMTP provider)
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=your_email@gmail.com
   EMAIL_HOST_PASSWORD=your_app_password

   # Django
   SECRET_KEY=your_secret_key_here
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   ```

5. **Run database migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser:**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start Redis server** (in a separate terminal):
   ```bash
   redis-server
   ```

8. **Start Celery worker** (in a separate terminal):
   ```bash
   celery -A tses_app worker --loglevel=info
   ```

9. **Run the development server:**
   ```bash
   python manage.py runserver
   ```

## API Endpoints

### Authentication Endpoints

- `POST /api/v1/auth/otp/request` - Request OTP (rate limited: 3/email per 10min, 10/IP per hour)
- `POST /api/v1/auth/otp/verify` - Verify OTP and get JWT tokens (failed attempts: max 5 per 15min)

### Audit Endpoints

- `GET /api/v1/audit/logs` - List audit logs (JWT authentication required, paginated)
  - Query parameters: `email`, `event`, `from_datetime`, `to_datetime`

### Legacy Endpoints (for compatibility)

- `POST /api/accounts/register/` - User registration
- `POST /api/accounts/login/` - Password-based login
- `POST /api/accounts/token/` - Get JWT tokens
- `POST /api/accounts/token/refresh/` - Refresh JWT tokens
- `GET/PUT /api/accounts/profile/` - User profile management

### Documentation

- `GET /api/schema/` - OpenAPI schema
- `GET /api/schema/swagger-ui/` - Swagger UI documentation
- `GET /api/schema/redoc/` - ReDoc documentation

#### Swagger UI Navigation

The Swagger UI provides an interactive interface for exploring and testing the API:

1. **Access Swagger UI** at `http://localhost:8000/api/schema/swagger-ui/`

2. **Authentication**:
   - For endpoints requiring authentication, click the **"Authorize"** button
   - Enter your JWT access token in the format: `Bearer YOUR_ACCESS_TOKEN`
   - Click **"Authorize"** to apply the token

3. **Testing Endpoints**:
   - Expand any endpoint section to view its details
   - Click **"Try it out"** to interact with the endpoint
   - Fill in the request parameters or body
   - Click **"Execute"** to send the request
   - View the response below the request

4. **Key Sections**:
   - **Authentication**: OTP request/verify endpoints
   - **Audit**: Audit log retrieval
   - **Accounts**: Legacy user management endpoints

5. **Response Codes**: Each endpoint shows possible HTTP status codes and their meanings

## Rate Limiting

The service implements Redis-backed rate limiting with sliding window algorithm:

### OTP Request Limits
- **Per Email**: 3 requests per 10 minutes
- **Per IP Address**: 10 requests per hour

### OTP Verify Limits
- **Per Email**: 10 requests per 5 minutes
- **Failed Attempts Lockout**: 5 failed attempts per email per 15 minutes (returns 423 Locked)

### Other Limits
- **Login**: 10 requests per 5 minutes per user/IP
- **Registration**: 3 requests per hour per IP
- **Token Refresh**: 20 requests per 5 minutes per user

Rate limit responses include helpful error messages and retry-after seconds in headers.

## Usage Examples

### User Registration

```bash
curl -X POST http://localhost:8000/api/accounts/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "password": "securepassword123",
    "password_confirm": "securepassword123"
  }'
```

### OTP Authentication Flow

1. **Request OTP:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/otp/request \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com"}'
   ```

2. **Verify OTP:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/otp/verify \
     -H "Content-Type: application/json" \
     -d '{
       "email": "user@example.com",
       "otp": "123456"
     }'
   ```

   Response includes JWT tokens:
   ```json
   {
     "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
     "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
     "user": {
       "id": 1,
       "email": "user@example.com",
       "first_name": "John",
       "last_name": "Doe",
       "is_email_verified": true
     }
   }
   ```

### Using JWT Tokens

```bash
curl -X GET http://localhost:8000/api/accounts/profile/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Architecture

### App Structure

- **`apps/accounts/`**: Authentication logic, user management, OTP flows
- **`apps/audit/`**: Audit logging and monitoring
- **`apps/core/`**: Shared utilities, middleware, tasks, filters, pagination

### Key Components

- **Rate Limiting**: Redis-backed sliding window algorithm with atomic operations
- **Audit Logging**: Automatic logging of all authentication events
- **Celery Tasks**:
  - `send_otp_email(email, otp)`: Asynchronous OTP email sending (console output)
  - `write_audit_log(event, email, ip, meta)`: Asynchronous audit log creation
- **JWT Tokens**: Secure token-based authentication
- **OpenAPI Docs**: Complete API documentation with examples

## Development

### Running Tests

```bash
python manage.py test
```

### Code Formatting

```bash
# Install development dependencies
pip install black isort flake8

# Format code
black .
isort .

# Lint code
flake8 .
```

### Docker Deployment

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: tses_app
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

  app:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/code
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    environment:
      - DEBUG=False
      - DB_HOST=db
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0

  celery:
    build: .
    command: celery -A tses_app worker --loglevel=info
    volumes:
      - .:/code
    depends_on:
      - redis
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0

volumes:
  postgres_data:
```

## Security Features

- **Rate Limiting**: Prevents brute force attacks
- **Audit Logging**: Complete audit trail
- **JWT Tokens**: Secure, stateless authentication
- **Password Hashing**: Django's secure password hashing
- **Email Verification**: OTP-based email verification
- **Request Logging**: Comprehensive request/response logging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.

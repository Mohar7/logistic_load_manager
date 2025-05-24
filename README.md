# Logistics Management System

A comprehensive FastAPI-based system for managing logistics operations, including load parsing, driver management, company tracking, and trip planning with Telegram notifications.

## Features

- **Load Management**
  - Text parsing of load information into structured data
  - Storage of load and leg information in PostgreSQL database
  - Load assignment and tracking

- **Driver Management**
  - Driver registration and profile management
  - Load assignment to drivers
  - Driver availability tracking

- **Company Management**
  - Company registration and profile management 
  - Company-driver relationship management
  - USDOT and MC number tracking

- **Notification System**
  - Telegram integration for driver notifications
  - Automated notifications for load assignments
  - Delivery status updates

- **API Integration**
  - RESTful endpoints for all operations
  - Pagination support for large datasets
  - Comprehensive error handling

## System Architecture

The system follows a clean architecture pattern with separate layers:

```
logistics-system/
├── app/                          # Application source code
│   ├── api/                      # API endpoints
│   │   └── routes/               # API routes
│   │       ├── company_management.py  # Company management
│   │       ├── driver_management.py   # Driver management
│   │       ├── load_management.py     # Load management
│   │       └── load_parser.py         # Load parsing
│   ├── core/                     # Application core
│   │   ├── parser/               # Parser modules
│   │   │   ├── parsing_service.py  # Parsing service
│   │   │   └── regex_patterns.py   # Regular expressions
│   │   └── utils/                # Utilities
│   │       ├── date_utils.py     # Date utilities
│   │       └── text_utils.py     # Text utilities
│   ├── db/                       # Database layer
│   │   ├── repositories/         # Repositories
│   │   │   ├── company_repository.py  # Company repository
│   │   │   ├── driver_repository.py   # Driver repository
│   │   │   └── load_repository.py     # Load repository
│   │   ├── database.py           # Database connection setup
│   │   ├── init_db.py            # Database initialization
│   │   └── models.py             # SQLAlchemy models
│   ├── schemas/                  # Pydantic schemas
│   │   ├── company.py            # Company schemas
│   │   ├── driver.py             # Driver schemas
│   │   └── load.py               # Load schemas
│   ├── services/                 # Business logic
│   │   ├── company_service.py    # Company management service
│   │   ├── driver_service.py     # Driver management service
│   │   ├── load_service.py       # Load management service
│   │   └── notification_service.py  # Notification service
│   ├── config.py                 # Application configuration
│   └── main.py                   # FastAPI entry point
├── alembic/                      # Database migrations
│   └── versions/                 # Migration files
├── .env                          # Environment variables
├── .env.example                  # Environment variables example
├── alembic.ini                   # Alembic configuration
├── docker-compose.yml            # Docker containers configuration
├── Dockerfile                    # Docker image instructions
├── init_app.py                   # Initialization script
├── requirements.txt              # Python dependencies
└── start.sh                      # Docker startup script
```

## Tech Stack

- **Backend**: FastAPI, Python 3.12
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Migrations**: Alembic
- **Containerization**: Docker, Docker Compose
- **Notifications**: Telegram Bot API
- **Validation**: Pydantic
- **HTTP Client**: aiohttp (for async API calls)

## Setup and Installation

### Using Docker (Recommended)

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd logistics-system
   ```

2. **Configure environment variables:**
   Copy the example environment file and update it with your settings:
   ```bash
   cp .env.example .env
   ```
   
   Update the `.env` file with your specific configuration:
   ```
   # App settings
   DEBUG=True

   # Database settings
   DB_HOST=localhost
   DB_PORT=5432
   DB_USER=postgres
   DB_PASSWORD=5115
   DB_NAME=logistics

   # Telegram settings
   TELEGRAM_BOT_TOKEN="your-telegram-bot-token"
   ```

3. **Start the application:**
   ```bash
   docker-compose up -d
   ```

   This will:
   - Start a PostgreSQL database on port 5115
   - Run the necessary database migrations
   - Initialize the database with default data
   - Start the FastAPI application on port 8000

4. **Access the application:**
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Manual Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd logistics-system
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   Copy the example environment file and update it with your settings:
   ```bash
   cp .env.example .env
   ```

5. **Set up the database:**
   - Install PostgreSQL
   - Create a database called `logistics`
   - Update the `.env` file with your database connection details
   - Run migrations: `alembic upgrade head`
   - Initialize data: `python -m app.db.init_db`

6. **Start the application:**
   ```bash
   uvicorn app.main:app --reload
   ```

## Database Configuration

The system uses PostgreSQL with the following default configuration in Docker:

- **Host**: localhost
- **Port**: 5115 (exposed from Docker)
- **Username**: postgres
- **Password**: 5115
- **Database**: logistics

To connect to the database manually:
```bash
psql -h localhost -p 5115 -U postgres -d logistics
```

## API Endpoints

### Load Management

- `POST /loads/parse` - Parse load text without saving to database
- `POST /loads/create` - Parse and save load to database
- `GET /loads/{load_id}` - Get a specific load by ID
- `GET /loads/` - Get all loads (with pagination)

### Load Assignment

- `PUT /load-management/{load_id}/assign-driver/{driver_id}` - Assign a driver to a load
- `GET /load-management/assigned-drivers` - Get all drivers with load assignments
- `GET /load-management/available-drivers` - Get all drivers without load assignments
- `POST /load-management/{load_id}/notify-driver` - Send notification to a driver about a load

### Driver Management

- `POST /drivers/` - Create a new driver
- `GET /drivers/{driver_id}` - Get a specific driver by ID
- `GET /drivers/` - Get all drivers (with pagination)
- `PUT /drivers/{driver_id}` - Update a driver
- `DELETE /drivers/{driver_id}` - Delete a driver

### Company Management

- `POST /companies/` - Create a new company
- `GET /companies/{company_id}` - Get a specific company by ID
- `GET /companies/` - Get all companies (with pagination)
- `PUT /companies/{company_id}` - Update a company
- `DELETE /companies/{company_id}` - Delete a company

### System

- `GET /` - Root endpoint (API info)
- `GET /health` - Health check endpoint

## Usage Examples

### Parsing a Load

```bash
curl -X POST "http://localhost:8000/loads/parse" \
  -H "Content-Type: text/plain" \
  -d "T-115CSXYJM

Spot

1

DCA2 Eastvale, California 91752

Sun, May 18, 05:28 PDT

3

SBD1 Bloomington, CA 92316

Sun, May 18, 15:38 PDT
342 mi

10h 41m
53' Trailer

P

Drop/Live

$1 019,44

$2.98/mi

P. Sementeyev"
```

### Creating a Load

```bash
curl -X POST "http://localhost:8000/loads/create" \
  -H "Content-Type: text/plain" \
  -d "T-115CSXYJM

Spot

1

DCA2 Eastvale, California 91752

Sun, May 18, 05:28 PDT

3

SBD1 Bloomington, CA 92316

Sun, May 18, 15:38 PDT
342 mi

10h 41m
53' Trailer

P

Drop/Live

$1 019,44

$2.98/mi

P. Sementeyev"
```

### Getting a Load

```bash
curl -X GET "http://localhost:8000/loads/1"
```

### Assigning a Driver to a Load

```bash
curl -X PUT "http://localhost:8000/load-management/1/assign-driver/1"
```

### Creating a Company

```bash
curl -X POST "http://localhost:8000/companies/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Logistics",
    "usdot": 12345,
    "carrier_identifier": "ACME",
    "mc": 67890
  }'
```

### Creating a Driver

```bash
curl -X POST "http://localhost:8000/drivers/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "company_id": 1,
    "chat_id": null
  }'
```

## Troubleshooting

### Docker Container Issues

If you encounter the error `no such file or directory: ./start.sh`:

1. Ensure the start.sh file exists in your project root
2. Make sure it has the correct permissions: `chmod +x start.sh`
3. Check for line ending issues (especially on Windows)

### Database Connection Issues

If you encounter database connection issues:

1. **Check if PostgreSQL is running:**
   ```bash
   docker-compose ps
   ```

2. **Verify database port:**
   ```bash
   docker-compose logs db
   ```

3. **Check connection settings:**
   Ensure your connection settings match those in the docker-compose.yml file.

### Missing Tables Error

If you see an error like `relation "loads" does not exist`:

1. **Run migrations manually:**
   ```bash
   docker-compose exec app bash -c "alembic upgrade head"
   ```

2. **Initialize the database:**
   ```bash
   docker-compose exec app python -m app.db.init_db
   ```

3. **Restart the application:**
   ```bash
   docker-compose restart app
   ```

## Development

### Adding New Features

1. **Create or modify models** in `app/db/models.py`
2. **Generate a migration**:
   ```bash
   alembic revision --autogenerate -m "description of changes"
   ```
3. **Apply the migration**:
   ```bash
   alembic upgrade head
   ```
4. **Update the corresponding schemas** in `app/schemas/`
5. **Implement repository methods** in `app/db/repositories/`
6. **Add business logic** in `app/services/`
7. **Create API endpoints** in `app/api/routes/`

### Code Structure Best Practices

- **Repository Layer**: Keep all database operations in repository classes
- **Service Layer**: Implement business logic in service classes
- **API Layer**: Keep endpoints thin, delegate to service layer
- **Schema Layer**: Use Pydantic schemas for validation and serialization/deserialization

## License

This project is licensed under the MIT License - see the LICENSE file for details.
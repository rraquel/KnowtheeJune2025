# KnowThee.AI - Talent Intelligence Platform

## Project Structure

```
/app/                           # Main application code
├── main.py                     # App entry point (FastAPI backend)
├── database/                   # Database config and models
│   ├── __init__.py            # DB engine and session setup
│   └── models.py              # SQLAlchemy ORM models
├── ingestion/                  # Data ingestion and processing
│   ├── __init__.py
│   ├── run_ingest.py          # Main ingestion service
│   ├── parsers/               # Parsers for CV and assessments
│   │   ├── __init__.py
│   │   ├── cv_parser.py
│   │   └── assessment_parser.py
│   ├── vector/                # For chunking & embedding logic
│   │   └── chunker.py
│   ├── migrations/            # Database migrations
│   │   ├── __init__.py
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/         # Auto-generated migration scripts
│   └── alembic.ini           # Alembic config file
├── api/                        # REST endpoints
│   ├── __init__.py
│   └── talent.py
└── utils/                      # Generic utility functions
    ├── __init__.py
    └── validators.py          # File format and size validation
/tests/                        # Test suite
├── test_parsers.py            # Unit tests for parsing logic
└── test_models.py
/data/
└── imports/                   # Raw input text files
```

## Setup Instructions

1. Install dependencies:
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

2. Set up PostgreSQL:
```bash
# Create database
createdb knowthee

# Or using psql:
psql -U postgres
CREATE DATABASE knowthee;
```

3. Set environment variables:
```bash
# Create .env file in app directory with:
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/knowthee
```

4. Run database migrations:
```bash
cd backend/ingestion
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

5. Run the API server:
```bash
cd app
uvicorn backend.api.api:app --reload
```

## API Endpoints

### CV Processing
- `POST /upload/cv`: Upload and process a CV file
- `GET /employees`: List all employees

### Assessment Processing
- `POST /upload/assessment`: Upload and process an assessment file

## Data Processing

The system processes two types of files:
1. CV text files (default)
2. Assessment files (must contain "assessment" in filename)

Place your files in `data/imports/` directory for batch processing.

### File Requirements
- Format: `.txt` files only
- Size: < 5MB
- Encoding: UTF-8

### CV Format
The CV parser expects sections marked with uppercase headers:
```
PERSONAL INFORMATION
[Name, contact details, etc.]

SUMMARY
[Professional summary]

EXPERIENCE
[Work experience entries]

EDUCATION
[Education history]

SKILLS
[List of skills]
```

### Assessment Format
The assessment parser expects:
```
Candidate Name: [Name]
Date: [Assessment Date]

HPI Score: [Score]
[HPI details]

HDS Score: [Score]
[HDS details]

MVPI Score: [Score]
[MVPI details]

RECOMMENDATIONS
[Recommendations text]

SUMMARY
[Summary text]
```

## Running Tests
```bash
pytest tests/
```

# KnowThee.AI - Comprehensive Talent Intelligence Platform

## Overview
KnowThee.AI is an advanced talent intelligence platform that combines CV processing, leadership assessment, team analytics, and organizational insights. The platform leverages state-of-the-art natural language processing, RAG (Retrieval-Augmented Generation) technology, and multiple assessment frameworks to provide comprehensive talent management solutions.

## Core Features

### 1. Leader Insights (👤)
Individual leadership profiling and analysis:
- Document upload and processing for leader assessment
- Multi-source data integration
- Comprehensive profile generation
- Leadership capability analysis
- Development recommendations

### 2. Talent Explorer (🔍)
Advanced CV management and talent search system:
- CV Upload and Processing:
  * Support for multiple formats (PDF, DOCX, DOC)
  * Automated information extraction
  * Structured data storage
  * Quality assurance checks

- Intelligent Search:
  * Natural language queries
  * Multi-criteria search capabilities
  * Relevance scoring
  * Detailed profile viewing

### 3. Organizational Pulse (📊)
Comprehensive organizational analytics dashboard:

- Executive Dashboard:
  * Key metrics overview
  * Organizational health indicators
  * Trend analysis

- Team Analytics:
  * Team performance metrics
  * Collaboration patterns
  * Development areas

- Assessment Insights:
  * HPI (Bright Side) - Personality characteristics
  * HDS (Dark Side) - Derailer patterns
  * MVPI (Values) - Motivational drivers
  * IDI (Intercultural) - Cultural adaptability
  * Capabilities - Organizational competencies
  * Derailers - Risk factors

### 4. Team Builder (👥)
Intelligent team composition and analysis:

- Team Selection:
  * Member selection interface
  * Role matching
  * Compatibility analysis

- Advanced Team Analysis:
  * Team Overview - Composition and dynamics
  * Capability Analysis - Collective strengths
  * Risk Assessment - Potential challenges
  * Optimization - Improvement recommendations

## Technical Architecture

### Database Layer
- SQLite for structured data storage
- ChromaDB for vector embeddings
- Integrated assessment data storage

### Core Components
1. RAG System:
   - Query analysis and intent detection
   - Context management
   - Intelligent response generation

2. Assessment Processing:
   - Multiple assessment framework integration
   - Scoring and analysis
   - Insight generation

3. Search System:
   - Hybrid search capabilities
   - Vector similarity matching
   - Priority-based filtering

4. Analytics Engine:
   - Metric calculation
   - Trend analysis
   - Visualization generation

## Setup and Installation

1. Environment Setup
```bash
# Create and activate Python virtual environment
python -m venv venv
source venv/bin/activate  # Unix/macOS
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Install Streamlit
pip install streamlit
```

2. Configuration
Required environment variables:
- `OPENAI_API_KEY`: For NLP and RAG functionality
- Database configuration
- Assessment system integration parameters

3. Running the Application
```bash
streamlit run main.py
```

## Docker Setup and Usage

### Prerequisites
- Docker and Docker Compose installed
- OpenAI API key (for embeddings)
- Git repository cloned locally

### Initial Setup

1. Create a `.env` file in the project root:
```bash
# Database configuration
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/knowthee
OPENAI_API_KEY=your_api_key_here
```

2. Build and start the containers:
```bash
# Build and start all services
docker-compose up -d
# Rebuild the containers with content
docker-compose build --no-cache
```

This will start the following services:
- PostgreSQL database
- Ingestion service
- API service

### Common Docker Commands

1. **View running containers**:
```bash
docker-compose ps
```

2. **View logs**:
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs ingest
docker-compose logs postgres

# Follow logs in real-time
docker-compose logs -f ingest
```

3. **Stop services**:
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (clears database)
docker-compose down -v
```

4. **Restart services**:
```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart ingest
```

### Running the Ingestion Pipeline

The ingestion process consists of two main steps:

1. **Initial Document Processing**
```bash
# Run the initial ingestion script
docker exec knowtheejune2025-ingest-1 python backend/ingestion/run_ingest.py
```

This script will:
- Process raw documents from the `backend/data/raw` directory
- Parse and structure the content
- Store the processed files in `backend/data/processed`

2. **Generate Embeddings**
```bash
# Run the embedding generation script
docker exec knowtheejune2025-ingest-1 python backend/ingestion/run_embedding.py --input-dir backend/data/processed
```

This script will:
- Process the documents from the specified input directory
- Generate embeddings for each document chunk
- Store the embeddings in the database

### Database Management

1. **Connect to the database**:
```bash
docker exec -it knowtheejune2025-postgres-1 psql -U postgres -d knowthee
```

2. **Common database commands**:
```sql
-- List all tables
\dt

-- Check embedding tables
SELECT COUNT(*) FROM embedding_documents;
SELECT COUNT(*) FROM embedding_chunks;

-- Check employee data
SELECT * FROM employees LIMIT 5;
```

### Troubleshooting

1. **Container Issues**:
```bash
# Check container status
docker-compose ps

# View detailed logs
docker-compose logs ingest
docker-compose logs postgres

# Restart problematic container
docker-compose restart ingest
```

2. **Database Issues**:
```bash
# Reset database (WARNING: This will delete all data)
docker-compose down -v
docker-compose up -d
```

3. **Common Problems**:
- Database connection errors: Check DATABASE_URL in .env
- Empty tables: Verify file permissions and input directory
- Embedding errors: Check OPENAI_API_KEY
- Container not starting: Check logs for specific errors

### File Organization

The system expects files to be organized as follows:
- `backend/data/raw/`: Place your raw input files here
- `backend/data/processed/`: Processed files will be stored here
- `backend/data/embeddings/`: Generated embeddings will be stored here

### Supported File Types

The system can process the following file types:
- CV files (format: `CV_[FirstName]_[LastName].txt`)
- IDI assessment files (format: `IDI_[FirstName]_[LastName].txt`)
- Hogan assessment files (format: `Hogan_[FirstName]_[LastName].txt`)

### Complete Workflow Example

1. **Start fresh**:
```bash
# Stop and remove everything
docker-compose down -v

# Start services
docker-compose up -d
```

2. **Process documents**:
```bash
# Run ingestion
docker exec knowtheejune2025-ingest-1 python backend/ingestion/run_ingest.py

# Generate embeddings
docker exec knowtheejune2025-ingest-1 python backend/ingestion/run_embedding.py --input-dir backend/data/processed
```

3. **Verify results**:
```bash
# Check database
docker exec -it knowtheejune2025-postgres-1 psql -U postgres -d knowthee -c "SELECT COUNT(*) FROM embedding_documents;"
```

## Usage Guide

### Leader Insights
1. Navigate to the Leader Insights tab
2. Upload relevant documents about the leader
3. Review generated insights and recommendations

### Talent Explorer
1. Use the Upload CV tab for adding new profiles
2. Switch to Search Talent for finding candidates
3. View detailed profiles and match scores

### Organizational Pulse
1. Access the executive dashboard for overview
2. Explore team analytics for group insights
3. Review assessment distributions and trends

### Team Builder
1. Select team members from the database
2. Review team composition analysis
3. Access optimization recommendations

## Technical Requirements
- Python 3.11+
- OpenAI API access
- SQLite
- ChromaDB
- Streamlit
- Assessment framework integrations

## Security Features
- PII (Personally Identifiable Information) protection
- Secure data storage
- Role-based access control
- Assessment data protection
- API key security

## Data Processing
- CV text extraction and structuring
- Assessment data integration
- Team dynamics analysis
- Organizational metrics calculation

## Future Roadmap
- Enhanced assessment integration
- Advanced team analytics
- Extended search capabilities
- Additional visualization options
- API expansion

## Support
For technical support or questions:
- Check documentation
- Contact system administrator
- Review error logs

## One-off Ingestion

The platform includes a standalone ingestion process that can be run locally or via Docker to process CV and assessment files.

### Prerequisites

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/knowthee"
```

### Running Locally

1. Place CV and assessment files in `backend/data/imports/`

2. Run the ingestion process:
```bash
# Process all files
python -m backend.ingestion.run_ingest ingest all

# Process a single file
python -m backend.ingestion.run_ingest ingest single filename.pdf

# Specify custom directories
python -m backend.ingestion.run_ingest ingest all --source /path/to/source --processed-dir /path/to/processed
```

### Running with Docker

1. Build and run the ingestion service:
```bash
docker-compose run --rm ingest run_ingest all
```

2. Process a single file:
```bash
docker-compose run --rm ingest run_ingest single filename.pdf
```

### Scheduled Ingestion

To run the ingestion process nightly at 2 AM, add this to your crontab:
```bash
0 2 * * * cd /path/to/project && docker-compose run --rm ingest run_ingest all >> /var/log/knowthee/ingest.log 2>&1
```

### Output

The ingestion process will:
1. Validate files for type and size
2. Parse CVs and assessments
3. Generate embeddings
4. Store data in the database
5. Move processed files to `backend/data/processed/`

Statistics and errors are logged to stdout in JSON format.
# KnowThee.AI - Talent Intelligence Platform

## Project Structure

```
/app/                           # Main application code
├── main.py                     # App entry point (FastAPI backend)
├── database/                   # Database config and migrations
│   ├── __init__.py            # DB engine and session setup
│   ├── models.py              # SQLAlchemy ORM models
│   ├── alembic.ini            # Alembic config file
│   └── alembic/               # Alembic migration folder
│       └── versions/          # Auto-generated migration scripts
├── services/                   # Business logic layer
│   ├── __init__.py
│   ├── parser/                # Parsers for CV and assessments
│   │   ├── __init__.py
│   │   ├── cv_parser.py
│   │   └── assessment_parser.py
│   └── vector/                # For chunking & embedding logic
│       └── chunker.py
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
cd app/database
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

5. Run the API server:
```bash
cd app
uvicorn main:app --reload
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
python -m backend.services.ingest ingest all

# Process a single file
python -m backend.services.ingest ingest single filename.pdf

# Specify custom directories
python -m backend.services.ingest ingest all --source /path/to/source --processed-dir /path/to/processed
```

### Running with Docker

1. Build and run the ingestion service:
```bash
docker-compose run --rm ingest ingest all
```

2. Process a single file:
```bash
docker-compose run --rm ingest ingest single filename.pdf
```

### Scheduled Ingestion

To run the ingestion process nightly at 2 AM, add this to your crontab:
```bash
0 2 * * * cd /path/to/project && docker-compose run --rm ingest ingest all >> /var/log/knowthee/ingest.log 2>&1
```

### Output

The ingestion process will:
1. Validate files for type and size
2. Parse CVs and assessments
3. Generate embeddings
4. Store data in the database
5. Move processed files to `backend/data/processed/`

Statistics and errors are logged to stdout in JSON format.
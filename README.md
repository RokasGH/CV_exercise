# Pitch Deck Analyzer

A Flask-based web application that analyzes startup pitch decks using Claude AI, specifically focused on climate tech ventures in Europe. The system provides automated analysis of pitch decks, scoring various aspects of the business, and maintaining a searchable database of analyses.

## Features

- **PDF Upload & Analysis**: Automatically extracts and analyzes text from PDF pitch decks
- **AI-Powered Analysis**: Utilizes Claude AI to evaluate:
  - Team composition and experience
  - Business model viability
  - Market traction
  - Climate tech potential
  - Geographic and industry fit
- **Comprehensive Scoring**: Generates weighted scores across multiple categories
- **Results Dashboard**: Detailed visualization of analysis results
- **Analytics Interface**: Search and filter through analyzed pitch decks
- **Automated Filtering**: Screens for:
  - Geographic focus (European + Israel markets)
  - Investment stage (Pre-seed to Series A)
  - Industry relevance (Excluding food/agriculture)
  - Climate tech alignment

## Prerequisites

- Python 3.12.7
- PostgreSQL 13 database
- Anthropic API key (for Claude AI)

## Web deployment

The application is available at [https://cv-exercise.onrender.com/](https://cv-exercise.onrender.com/)

## Project Structure

```
pitch-deck-analyzer/
├── app.py              # Main application file
├── templates/          # HTML templates
│   ├── index.html     # Upload page
│   ├── results.html   # Analysis results
│   └── analytics.html # Analytics dashboard
├── uploads/           # Temporary storage for uploads
├── requirements.txt   # Project dependencies
├── runtime.txt        # Runtime dependencies
└── README.md         # This file
```

### Scoring System

Overall score is calculated using weighted components:
- Team evaluation (40%)
- Business model (35%)
- Traction metrics (25%)

Each component is scored on multiple sub-criteria using a {0, 0.5, 1} scale.
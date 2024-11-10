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

The overall score is calculated using weighted components:
- **Team Evaluation (40%)**: Assesses team experience, previous collaborations, and sector relevance.
- **Business Model (35%)**: Evaluates scalability, upsell potential, and risk resilience.
- **Traction Metrics (25%)**: Analyzes customer acquisition, growth metrics, and retention.

Each component uses a scoring scale of {0, 0.5, 1} for each criterion, producing a weighted final score on a 0-100 scale.

### Criteria for Suitability

A pitch deck is considered suitable for follow-up calls if:
- It scores above 50.
- Meets criteria for industry, stage, and geography fit.
- Demonstrates climate-tech relevance.
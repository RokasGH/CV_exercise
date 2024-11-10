import os
import hashlib
from flask import Flask, request, render_template, flash, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
import PyPDF2
import anthropic
from dotenv import load_dotenv
import json
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import UniqueConstraint, text, desc, or_

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024  # 25MB max file size
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost/dbname')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

ALLOWED_EXTENSIONS = {'pdf'}
ALLOWED_STAGES = {'pre-seed', 'seed', 'series a'}
EXCLUDED_INDUSTRIES = {'food', 'agriculture', 'agtech', 'foodtech'}
ALLOWED_REGIONS = {'europe', 'ukraine', 'france', 'spain', 'sweden',
                   'germany', 'finland', 'norway', 'poland', 'italy',
                   'united kingdom', 'romania', 'belarus', 'kazakhstan',
                   'greece', 'bulgaria', 'iceland', 'hungary',
                   'portugal', 'austria', 'czech republic', 'czechia',
                   'serbia', 'ireland', 'lithuania', 'latvia',
                   'croatia', 'bosnia and herzegovina', 'slovakia',
                   'estonia', 'denmark', 'netherlands', 'switzerland',
                   'moldova', 'belgium', 'albania', 'north macedonia',
                   'turkey', 'slovenia', 'montenegro', 'kosovo',
                   'azerbaijan', 'georgia', 'luxembourg', 'faroe islands',
                   'isle of man', 'andorra', 'malta', 'liechtenstein',
                   'jersey (uk)', 'guernsey (uk)', 'san marino',
                   'gibraltar', 'monaco', 'vatican city',
                   'akrotiri and dhekelia (uk)', 'armenia',
                   'cyprus', 'greenland', 'israel'}

db = SQLAlchemy(app)

class PitchDeck(db.Model):
    __tablename__ = 'pitch_decks'
    
    id = db.Column(db.Integer, primary_key=True)
    file_hash = db.Column(db.String(64), unique=True, nullable=False)  # SHA-256 hash of file
    company_name = db.Column(db.String(255), nullable=False)
    industry = db.Column(db.String(500))  # Increased length
    is_industry_in_scope = db.Column(db.Boolean, nullable=False)
    stage = db.Column(db.String(255))  # Increased length
    is_stage_in_scope = db.Column(db.Boolean, nullable=False)
    geography = db.Column(db.String(500))  # Increased length
    is_geography_in_scope = db.Column(db.Boolean, nullable=False)
    team_score = db.Column(JSONB)
    business_model_score = db.Column(JSONB)
    traction_score = db.Column(JSONB)
    climate_tech_analysis = db.Column(JSONB)
    website = db.Column(db.String(500))  # Increased length
    summary = db.Column(db.Text)
    overall_score = db.Column(db.Integer)  # Changed to integer 0-100
    analysis_date = db.Column(db.DateTime, nullable=False)
    raw_text = db.Column(db.Text)
    suitable_for_call = db.Column(db.Boolean, default=False)
    
    __table_args__ = (UniqueConstraint('file_hash', name='uix_1'),)

def get_file_hash(file_path):
    """Generate SHA-256 hash of file content"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_path):
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ''
        for page in reader.pages:
            text += page.extract_text() + '\n'
    return text

def calculate_overall_score(team_score, business_score, traction_score):
    """Calculate weighted overall score from 0-100"""
    weights = {
        'team': 0.4,
        'business': 0.35,
        'traction': 0.25
    }
    
    team_total = sum(team_score.values()) / 3
    business_total = sum(business_score.values()) / 3
    traction_total = sum(traction_score.values()) / 3
    
    weighted_score = (
        team_total * weights['team'] +
        business_total * weights['business'] +
        traction_total * weights['traction']
    ) * 100  # Scale to 100-point system
    
    return round(weighted_score)

def analyze_pitch_deck(text):
    client = anthropic.Client(api_key=os.getenv('ANTHROPIC_API_KEY'))
    
    prompt = f"""Analyze this pitch deck text and extract the following information with high attention to detail:

    1. Company Name
    2. Industry/Sector (be specific about climate-tech focus if applicable)
    2.1. Is the industry not in {EXCLUDED_INDUSTRIES}?
    3. Stage (pre-seed/seed/Series A/Series B/Series C/Mezzanine/IPO)
    3.1. Is the stage in {ALLOWED_STAGES}?
    4. Geography/Location (be specific about the company's main location/HQ)
    4.1. Is the geography/location in {ALLOWED_REGIONS}?
    5. Team evaluation (score each YES = 1, PARTIAL YES = 0.5, NO = 0):
       - Relevant experience in climate/tech sector
       - Previous work together
       - Previous startup experience
    6. Business model evaluation (score each YES = 1, PARTIAL YES = 0.5, NO = 0):
       - Scalability (especially important for climate impact)
       - Upsell/expansion potential
       - Resilience to market/regulatory changes
    7. Traction evaluation (score each YES = 1, PARTIAL YES = 0.5, NO = 0):
       - Initial customers/pilots
       - Growth metrics
       - Customer retention/feedback
    8. Website or contact information
    9. Additional climate-tech specific analysis:
       - Clear climate impact potential
       - Technology readiness level
       - Regulatory alignment (especially EU regulations)

    Only extract specific company details from the text provided, no assumptions.
    If company name is not explicitly mentioned, mark as 'Name not found'.
    If any of is_industry_in_scope, is_stage_in_scope, is_geography_in_scope, is_climate_tech are false, the company is not suitable for a call.
    Evaluate if the company is suitable for a call based on the above criteria and overall score. Summarize why or why not.

    Pitch deck text:
    {text}

    Format response as JSON:
    {{
        "company_name": "",
        "industry": "",
        "is_industry_in_scope": true/false,
        "stage": "",
        "is_stage_in_scope": true/false,
        "geography": "",
        "is_geography_in_scope": true/false,
        "team_score": {{
            "relevant_experience": 0,
            "worked_together": 0,
            "previous_business": 0,
            "comments": ""
        }},
        "business_model_score": {{
            "scalability": 0,
            "upsell_potential": 0,
            "risk_resistance": 0,
            "comments": ""
        }},
        "traction_score": {{
            "initial_customers": 0,
            "rapid_growth": 0,
            "customer_retention": 0,
            "comments": ""
        }},
        "climate_tech_analysis": {{
            "is_climate_tech": true/false,
            "impact_potential": "",
            "tech_readiness": "",
            "regulatory_alignment": ""
        }},
        "website": "",
        "summary": ""
    }}
    """
    
    messages = [{"role": "user", "content": prompt}]
    
    response = client.messages.create(
        model="claude-3-5-sonnet-latest",
        max_tokens=4000,
        temperature=0.1,
        system="You are a venture capital analyst specializing in climate tech investments. Focus on identifying companies with strong climate impact potential and scalable solutions.",
        messages=messages
    )

    try:
        analysis = json.loads(response.content[0].text)

        # Calculate scores
        team_scores = {k: float(v) for k, v in analysis['team_score'].items() if k != 'comments'}
        business_scores = {k: float(v) for k, v in analysis['business_model_score'].items() if k != 'comments'}
        traction_scores = {k: float(v) for k, v in analysis['traction_score'].items() if k != 'comments'}
        
        analysis['overall_score'] = calculate_overall_score(team_scores, business_scores, traction_scores)
        
        # Determine if suitable for call (score > 50 and meets key criteria)
        analysis['suitable_for_call'] = (
            analysis['overall_score'] >= 50 and
            analysis['climate_tech_analysis']['is_climate_tech'] and
            analysis['is_industry_in_scope'] and
            analysis['is_stage_in_scope'] and
            analysis['is_geography_in_scope']
        )
        
        return analysis
    except Exception as e:
        print(f"Error parsing Claude response: {e}")
        return None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('home'))

    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('home'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(file_path)

        try:
            file_hash = get_file_hash(file_path)
            text = extract_text_from_pdf(file_path)
            # Remove null characters from the extracted text
            text = text.replace('\x00', '')
            analysis = analyze_pitch_deck(text)
            # Check if deck already exists
            existing_deck = PitchDeck.query.filter_by(file_hash=file_hash).first()
            
            if existing_deck:
                # Update existing record
                existing_deck.company_name = analysis['company_name']
                existing_deck.industry = analysis['industry']
                existing_deck.is_industry_in_scope = analysis['is_industry_in_scope']
                existing_deck.stage = analysis['stage']
                existing_deck.is_stage_in_scope = analysis['is_stage_in_scope']
                existing_deck.geography = analysis['geography']
                existing_deck.is_geography_in_scope = analysis['is_geography_in_scope']
                existing_deck.team_score = analysis['team_score']
                existing_deck.business_model_score = analysis['business_model_score']
                existing_deck.traction_score = analysis['traction_score']
                existing_deck.climate_tech_analysis = analysis['climate_tech_analysis']
                existing_deck.overall_score = analysis['overall_score']
                existing_deck.website = analysis.get('website', '')
                existing_deck.summary = analysis.get('summary', '')
                existing_deck.analysis_date = datetime.now()
                existing_deck.raw_text = text
                existing_deck.suitable_for_call = analysis['suitable_for_call']
                
                db.session.commit()
                deck_id = existing_deck.id
            else:
                # Create new record
                new_deck = PitchDeck(
                    file_hash=file_hash,
                    company_name=analysis['company_name'],
                    industry=analysis['industry'],
                    is_industry_in_scope=analysis['is_industry_in_scope'],
                    stage=analysis['stage'],
                    is_stage_in_scope=analysis['is_stage_in_scope'],
                    geography=analysis['geography'],
                    is_geography_in_scope=analysis['is_geography_in_scope'],
                    team_score=analysis['team_score'],
                    business_model_score=analysis['business_model_score'],
                    traction_score=analysis['traction_score'],
                    climate_tech_analysis=analysis['climate_tech_analysis'],
                    overall_score=analysis['overall_score'],
                    website=analysis.get('website', ''),
                    summary=analysis.get('summary', ''),
                    analysis_date=datetime.now(),
                    raw_text=text,
                    suitable_for_call=analysis['suitable_for_call']
                )
                
                db.session.add(new_deck)
                db.session.commit()
                deck_id = new_deck.id

            return redirect(url_for('results', deck_id=deck_id))

        except Exception as e:
            flash(f'Error processing file: {str(e)}')
            return redirect(url_for('home'))
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

    flash('Invalid file type')
    return redirect(url_for('home'))

@app.route('/results/<int:deck_id>')
def results(deck_id):
    deck = PitchDeck.query.get_or_404(deck_id)
    return render_template('results.html', deck=deck)

@app.route('/analytics')
def analytics():
    # Get initial decks without filters
    decks = PitchDeck.query.order_by(desc(PitchDeck.analysis_date)).all()
    
    # Convert decks to JSON-serializable format
    decks_data = [{
        'id': deck.id,
        'company_name': deck.company_name,
        'industry': deck.industry,
        'stage': deck.stage,
        'geography': deck.geography,
        'overall_score': deck.overall_score,
        'suitable_for_call': deck.suitable_for_call,
        'analysis_date': deck.analysis_date.strftime('%Y-%m-%d')
    } for deck in decks]
    
    return render_template('analytics.html', 
                         decks=decks_data)

@app.route('/api/search')
def search_decks():
    query = request.args.get('q', '').lower()
    stage = request.args.get('stage')
    min_score = request.args.get('min_score')
    suitable_only = request.args.get('suitable_only') == 'true'
    
    deck_query = PitchDeck.query
    
    # Apply filters
    if query:
        deck_query = deck_query.filter(
            or_(
                PitchDeck.company_name.ilike(f'%{query}%'),
                PitchDeck.industry.ilike(f'%{query}%'),
                PitchDeck.geography.ilike(f'%{query}%')
            )
        )
    
    if stage:
        deck_query = deck_query.filter(PitchDeck.stage.ilike(f'%{stage}%'))
    if min_score:
        deck_query = deck_query.filter(PitchDeck.overall_score >= int(min_score))
    if suitable_only:
        deck_query = deck_query.filter(PitchDeck.suitable_for_call == True)
    
    # Order by most recent first
    deck_query = deck_query.order_by(desc(PitchDeck.analysis_date))
    
    results = deck_query.all()
    
    return jsonify([{
        'id': deck.id,
        'company_name': deck.company_name,
        'industry': deck.industry,
        'stage': deck.stage,
        'geography': deck.geography,
        'overall_score': deck.overall_score,
        'suitable_for_call': deck.suitable_for_call,
        'analysis_date': deck.analysis_date.strftime('%Y-%m-%d')
    } for deck in results])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
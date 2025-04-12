import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
import pandas as pd
from reddit_scraper import scrape_reddit_data
from text_processor import process_text, find_similar_confessions

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Database setup
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure SQLite database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///confessions.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize app with SQLAlchemy
db.init_app(app)

# Import models after db initialization
with app.app_context():
    from models import Confession, Category
    db.create_all()
    
    # Initialize categories if they don't exist
    categories = ['Academics', 'Campus Life', 'Relationships', 'Mental Health', 'PS/Thesis', 'General']
    existing_categories = Category.query.all()
    existing_names = [c.name for c in existing_categories]
    
    for cat in categories:
        if cat not in existing_names:
            new_category = Category(name=cat)
            db.session.add(new_category)
    
    db.session.commit()

# Routes
@app.route('/')
def index():
    categories = Category.query.all()
    current_year = datetime.now().year
    return render_template('index.html', categories=categories, current_year=current_year)

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query', '')
    category_id = request.form.get('category', '')
    current_year = datetime.now().year
    
    if not query:
        flash('Please enter a search query', 'warning')
        return redirect(url_for('index'))
    
    try:
        # Get all confessions from database
        confessions_query = Confession.query
        
        # Filter by category if provided
        if category_id and category_id != 'all':
            confessions_query = confessions_query.filter_by(category_id=category_id)
            
        confessions = confessions_query.all()
        
        # Convert to DataFrame for processing
        confessions_df = pd.DataFrame([
            {'id': c.id, 'text': c.text, 'source': c.source, 'score': c.score, 'url': c.url} 
            for c in confessions
        ])
        
        if confessions_df.empty:
            flash('No confessions found. Try a different search or category.', 'info')
            return redirect(url_for('index'))
        
        # Find similar confessions
        similar_confessions = find_similar_confessions(query, confessions_df)
        
        if not similar_confessions:
            flash('No matches found for your query. Try different keywords.', 'info')
            return redirect(url_for('index'))
            
        # Get full confession objects for results
        result_ids = [c['id'] for c in similar_confessions]
        results = Confession.query.filter(Confession.id.in_(result_ids)).all()
        
        # Sort results in the order of similarity scores
        id_to_result = {r.id: r for r in results}
        sorted_results = [id_to_result[id] for id in result_ids if id in id_to_result]
        
        return render_template('results.html', 
                               query=query, 
                               results=sorted_results, 
                               categories=Category.query.all(),
                               current_year=current_year)
    
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        flash(f'An error occurred while processing your search: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/categories')
def categories():
    categories = Category.query.all()
    category_data = []
    current_year = datetime.now().year
    
    for category in categories:
        confession_count = Confession.query.filter_by(category_id=category.id).count()
        category_data.append({
            'name': category.name,
            'id': category.id,
            'count': confession_count
        })
    
    return render_template('categories.html', categories=category_data, current_year=current_year)

@app.route('/about')
def about():
    stats = {
        'confession_count': Confession.query.count(),
        'category_count': Category.query.count(),
        'subreddits': ['r/BITSPilani', 'r/Indian_Academia', 'r/bitsians']
    }
    current_year = datetime.now().year
    return render_template('about.html', stats=stats, current_year=current_year)

@app.route('/refresh_data')
def refresh_data():
    """Admin route to refresh Reddit data"""
    try:
        # Only allow this in development mode
        if not app.debug:
            flash('This feature is only available in development mode', 'warning')
            return redirect(url_for('index'))
            
        subreddits = ['BITSPilani', 'Indian_Academia', 'bitsians']
        scraped_data = scrape_reddit_data(subreddits)
        
        # Process and categorize the scraped data
        processed_data = process_text(scraped_data)
        
        # Get existing categories
        categories = {cat.name: cat.id for cat in Category.query.all()}
        
        # Save to database
        new_count = 0
        for item in processed_data:
            # Check if confession already exists by URL
            existing = Confession.query.filter_by(url=item['url']).first()
            if not existing:
                category_id = categories.get(item['category'], categories['General'])
                new_confession = Confession(
                    text=item['text'],
                    title=item['title'],
                    category_id=category_id,
                    url=item['url'],
                    source=item['subreddit'],
                    score=item['score']
                )
                db.session.add(new_confession)
                new_count += 1
        
        db.session.commit()
        flash(f'Successfully added {new_count} new confessions from Reddit', 'success')
    
    except Exception as e:
        logger.error(f"Data refresh error: {str(e)}")
        flash(f'Error refreshing data: {str(e)}', 'danger')
        db.session.rollback()
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

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
from perplexity_api import generate_summary, fallback_summary

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

# Add a custom Jinja2 filter for handling newlines
@app.template_filter('nl2br')
def nl2br(value):
    """Convert newlines to <br> tags"""
    if value:
        return value.replace('\n', '<br>')
    return value

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
    
    # Add sample confessions if the database is empty
    if Confession.query.count() == 0:
        logger.info("Adding sample confessions to the database")
        
        # Get category IDs
        category_dict = {cat.name: cat.id for cat in Category.query.all()}
        
        # Sample confessions with realistic data for each category
        sample_confessions = [
            {
                "text": "I'm struggling with my Data Structures course. The professor is going too fast, and I can't keep up with the assignments. Has anyone been in this situation? What should I do?",
                "title": "Struggling with Data Structures",
                "category": "Academics",
                "source": "BITSPilani",
                "score": 45,
                "url": "https://www.reddit.com/r/BITSPilani/sample1"
            },
            {
                "text": "The mess food has been terrible lately. I've found insects in the rice twice this week. Are others experiencing the same issue? How do we raise this with the administration?",
                "title": "Mess Food Quality",
                "category": "Campus Life",
                "source": "BITSPilani",
                "score": 78,
                "url": "https://www.reddit.com/r/BITSPilani/sample2"
            },
            {
                "text": "I've had a crush on this girl in my Computer Science class for two semesters now. We talk occasionally but I'm too nervous to ask her out. She's brilliant and way out of my league. Any advice?",
                "title": "Crush in CS class",
                "category": "Relationships",
                "source": "bitsians",
                "score": 92,
                "url": "https://www.reddit.com/r/bitsians/sample3"
            },
            {
                "text": "The academic pressure is killing me. I haven't slept properly in weeks, my CGPA is dropping, and I'm constantly anxious. Does anyone else feel like they're drowning?",
                "title": "Academic pressure and mental health",
                "category": "Mental Health",
                "source": "Indian_Academia",
                "score": 106,
                "url": "https://www.reddit.com/r/Indian_Academia/sample4"
            },
            {
                "text": "Just got my PS station at Amazon Bangalore! So excited for this opportunity. Any tips for making the most of it? What's the work culture like?",
                "title": "PS at Amazon Bangalore",
                "category": "PS/Thesis",
                "source": "BITSPilani",
                "score": 67,
                "url": "https://www.reddit.com/r/BITSPilani/sample5"
            },
            {
                "text": "The BITS Pilani courses are much harder than I expected. I was a top student in my school, but here I'm barely average. Is this normal or am I not cut out for this?",
                "title": "Difficulty of courses",
                "category": "Academics",
                "source": "Indian_Academia",
                "score": 34,
                "url": "https://www.reddit.com/r/Indian_Academia/sample6"
            },
            {
                "text": "The hostel internet is so unreliable, especially in the evenings when everyone is trying to use it. How am I supposed to submit assignments or attend online interviews?",
                "title": "Hostel internet issues",
                "category": "Campus Life",
                "source": "BITSPilani",
                "score": 56,
                "url": "https://www.reddit.com/r/BITSPilani/sample7"
            },
            {
                "text": "I broke up with my girlfriend last semester, and now we have 3 classes together. The awkwardness is unbearable. How do I handle this situation?",
                "title": "Ex in same classes",
                "category": "Relationships",
                "source": "bitsians",
                "score": 87,
                "url": "https://www.reddit.com/r/bitsians/sample8"
            },
            {
                "text": "I've been feeling depressed and isolated for months now. My friends don't understand, and I'm too embarrassed to see a counselor. Does anyone have experience with the campus mental health services?",
                "title": "Depression and seeking help",
                "category": "Mental Health",
                "source": "BITSPilani",
                "score": 112,
                "url": "https://www.reddit.com/r/BITSPilani/sample9"
            },
            {
                "text": "My PS station is boring and I'm not learning anything valuable. The work is repetitive and my mentor rarely has time for me. Is it worth trying to change stations mid-semester?",
                "title": "Disappointing PS experience",
                "category": "PS/Thesis",
                "source": "Indian_Academia",
                "score": 45,
                "url": "https://www.reddit.com/r/Indian_Academia/sample10"
            },
            {
                "text": "I'm a first-year student and still haven't made any close friends. Everyone seems to already have their groups. Any advice on how to connect with people?",
                "title": "Trouble making friends",
                "category": "General",
                "source": "BITSPilani",
                "score": 65,
                "url": "https://www.reddit.com/r/BITSPilani/sample11"
            },
            {
                "text": "I just bombed my Thermodynamics exam. I studied for weeks but blanked out completely. Now I'm worried about my grade in this course. Has anyone recovered from a bad exam?",
                "title": "Failed an important exam",
                "category": "Academics",
                "source": "bitsians",
                "score": 41,
                "url": "https://www.reddit.com/r/bitsians/sample12"
            },
            {
                "text": "Which clubs are worth joining at BITS Pilani? I'm interested in robotics and programming but don't want to overcommit in my first year.",
                "title": "Club recommendations",
                "category": "Campus Life",
                "source": "BITSPilani",
                "score": 33,
                "url": "https://www.reddit.com/r/BITSPilani/sample13"
            },
            {
                "text": "My roommate and I have completely different schedules and habits. They party late, I wake up early. The tension is making living together unbearable. How do I request a room change?",
                "title": "Roommate conflicts",
                "category": "Campus Life",
                "source": "Indian_Academia",
                "score": 76,
                "url": "https://www.reddit.com/r/Indian_Academia/sample14"
            },
            {
                "text": "I'm struggling to balance academics with my relationship. My girlfriend attends a different college, and the long-distance is taking a toll. Any advice from those who've made it work?",
                "title": "Long-distance relationship struggles",
                "category": "Relationships",
                "source": "BITSPilani",
                "score": 54,
                "url": "https://www.reddit.com/r/BITSPilani/sample15"
            }
        ]
        
        for confession in sample_confessions:
            new_confession = Confession(
                text=confession["text"],
                title=confession["title"],
                category_id=category_dict[confession["category"]],
                source=confession["source"],
                score=confession["score"],
                url=confession["url"]
            )
            db.session.add(new_confession)
        
        db.session.commit()
        logger.info(f"Added {len(sample_confessions)} sample confessions to the database")

# Routes
@app.route('/')
def index():
    categories = Category.query.all()
    current_year = datetime.now().year
    return render_template('index.html', categories=categories, current_year=current_year)

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        query = request.form.get('query', '')
        category_id = request.form.get('category', '')
        summarize = request.form.get('summarize') == 'true'
    else:  # GET request
        query = request.args.get('query', '')
        category_id = request.args.get('category', '')
        summarize = request.args.get('summarize') == 'true'
    
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
        
        # If summarize is enabled, generate a summary of the results
        if summarize:
            try:
                # Convert results to format needed for summarization
                confession_data = []
                for result in sorted_results:
                    confession_data.append({
                        'id': result.id,
                        'text': result.text,
                        'title': result.title,
                        'category': result.category.name,
                        'source': result.source,
                        'score': result.score,
                        'url': result.url
                    })
                
                # Try to get a summary from Perplexity API
                summary = generate_summary(query, confession_data)
                
                # If Perplexity API is not available, use fallback summary
                if summary is None:
                    logger.warning("Perplexity API unavailable, using fallback summary")
                    summary = fallback_summary(query, confession_data)
                
                return render_template('summarized_results.html',
                                    query=query,
                                    results=sorted_results,
                                    categories=Category.query.all(),
                                    summary=summary,
                                    current_year=current_year)
            except Exception as e:
                logger.error(f"Error generating summary: {str(e)}")
                # If there's an error with summarization, fall back to regular results
                flash('Could not generate summary. Showing regular results instead.', 'warning')
        
        # Regular search results without summary
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
    current_year = datetime.now().year
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

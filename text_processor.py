import re
import pandas as pd
import numpy as np
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize NLTK resources - handled gracefully if they're already downloaded
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)
    
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)
    
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet', quiet=True)

# Create lemmatizer instance
lemmatizer = WordNetLemmatizer()

# Stopwords
stop_words = set(stopwords.words('english'))

def clean_text(text):
    """Clean and normalize text"""
    if not text or not isinstance(text, str):
        return ""
        
    # Convert to lowercase
    text = text.lower()
    
    # Remove URLs
    text = re.sub(r'http\S+', '', text)
    
    # Remove special characters, keeping only letters, numbers and spaces
    text = re.sub(r'[^\w\s]', '', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def tokenize_and_lemmatize(text):
    """Tokenize, remove stopwords and lemmatize text"""
    if not text:
        return []
        
    # Tokenize
    tokens = word_tokenize(text)
    
    # Remove stopwords and lemmatize
    tokens = [lemmatizer.lemmatize(token) for token in tokens if token not in stop_words]
    
    return tokens

def categorize_post(text):
    """Categorize a post into predefined categories"""
    text = text.lower()
    
    # Define keywords for each category
    categories = {
        'Academics': ['class', 'course', 'professor', 'lecture', 'exam', 'grade', 'cgpa', 
                     'assignment', 'project', 'study', 'academic', 'subject', 'department'],
        'Campus Life': ['hostel', 'mess', 'food', 'campus', 'library', 'club', 'event', 
                       'fest', 'facility', 'accommodation', 'room', 'roommate'],
        'Relationships': ['relationship', 'crush', 'love', 'date', 'girlfriend', 'boyfriend',
                         'breakup', 'friend', 'friendship'],
        'Mental Health': ['stress', 'anxiety', 'depression', 'mental health', 'counselor',
                         'therapy', 'pressure', 'burnout', 'exhausted', 'overwhelmed'],
        'PS/Thesis': ['ps', 'practice school', 'thesis', 'research', 'industry', 'intern', 
                     'supervisor', 'project', 'dissertation']
    }
    
    # Count matches for each category
    category_counts = {category: 0 for category in categories}
    
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in text:
                category_counts[category] += 1
    
    # Find category with most keyword matches
    max_count = max(category_counts.values())
    
    # If no keywords matched or tie, return General
    if max_count == 0:
        return 'General'
        
    # Get categories with the max count (in case of ties)
    max_categories = [cat for cat, count in category_counts.items() if count == max_count]
    
    return max_categories[0]  # Return the first category in case of ties

def process_text(df):
    """Process the scraped data"""
    if df.empty:
        logger.warning("Empty DataFrame provided for processing")
        return []
        
    try:
        # Make a copy to avoid modifying the original
        processed_df = df.copy()
        
        # Clean text fields
        processed_df['clean_title'] = processed_df['title'].apply(clean_text)
        processed_df['clean_text'] = processed_df['text'].apply(clean_text)
        
        # Combine title and text for processing
        processed_df['combined_text'] = processed_df['clean_title'] + ' ' + processed_df['clean_text']
        
        # Categorize posts
        processed_df['category'] = processed_df.apply(
            lambda row: categorize_post(row['combined_text']), axis=1
        )
        
        # Convert to list of dictionaries for easier handling
        result = processed_df.to_dict('records')
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing text: {str(e)}")
        return []

def find_similar_confessions(query, confessions_df, top_n=5):
    """Find confessions similar to the user query"""
    if confessions_df.empty:
        logger.warning("No confessions available for search")
        return []
        
    try:
        # Clean the query
        clean_query = clean_text(query)
        
        # Create a combined text field if not exists
        if 'combined_text' not in confessions_df.columns:
            # Combine title and text if available, otherwise just use text
            if 'title' in confessions_df.columns:
                confessions_df['combined_text'] = confessions_df['title'] + ' ' + confessions_df['text']
            else:
                confessions_df['combined_text'] = confessions_df['text']
        
        # Create TF-IDF vectorizer
        vectorizer = TfidfVectorizer(
            max_features=5000,
            min_df=2,
            max_df=0.8,
            strip_accents='unicode',
            analyzer='word',
            token_pattern=r'\w{1,}',
            stop_words='english'
        )
        
        # Create corpus with query at index 0
        corpus = [clean_query] + confessions_df['combined_text'].tolist()
        
        # Fit and transform
        tfidf_matrix = vectorizer.fit_transform(corpus)
        
        # Get similarity scores between query and confessions
        similarity_scores = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
        
        # Get indices of top N most similar confessions
        top_indices = similarity_scores.argsort()[::-1][:top_n]
        
        # Filter for minimum similarity (optional)
        min_similarity = 0.05  # Can be adjusted
        top_indices = [idx for idx in top_indices if similarity_scores[idx] >= min_similarity]
        
        # If no good matches, return empty list
        if not top_indices:
            return []
            
        # Get results
        results = []
        for idx in top_indices:
            confession_idx = confessions_df.index[idx]
            confession = confessions_df.loc[confession_idx].to_dict()
            confession['similarity'] = float(similarity_scores[idx])
            results.append(confession)
            
        return results
        
    except Exception as e:
        logger.error(f"Error finding similar confessions: {str(e)}")
        return []

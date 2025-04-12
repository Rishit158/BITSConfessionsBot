import logging
import re
import random
from typing import List, Dict, Any, Optional
from collections import Counter
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Ensure NLTK resources are downloaded
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')

def extract_key_phrases(texts, num_phrases=10):
    """Extract key phrases from a list of texts"""
    stop_words = set(stopwords.words('english'))
    
    # Combine all texts
    combined_text = ' '.join(texts)
    
    # Tokenize and remove stopwords
    words = [word.lower() for word in word_tokenize(combined_text) 
             if word.isalnum() and word.lower() not in stop_words and len(word) > 3]
    
    # Find most common words
    fdist = FreqDist(words)
    return [word for word, _ in fdist.most_common(num_phrases)]

def get_key_sentences(texts, key_phrases, num_sentences=5):
    """Extract key sentences containing important phrases"""
    all_sentences = []
    
    for text in texts:
        sentences = sent_tokenize(text)
        for sentence in sentences:
            # Score sentence based on how many key phrases it contains
            score = sum(1 for phrase in key_phrases if phrase in sentence.lower())
            if score > 0:
                all_sentences.append((sentence, score))
    
    # Sort sentences by score and take top ones
    all_sentences.sort(key=lambda x: x[1], reverse=True)
    return [s[0] for s in all_sentences[:num_sentences]]

def identify_common_themes(confessions):
    """Identify common themes from confessions"""
    themes = []
    
    # Extract categories
    categories = [conf.get('category', '') for conf in confessions]
    category_count = Counter(categories)
    
    # Add common categories as themes
    for category, count in category_count.most_common(2):
        if count > 1 and category:
            themes.append(f"{category}")
    
    return themes

def generate_summary(query: str, confessions: List[Dict[str, Any]]) -> str:
    """
    Generate a summary of confessions without using external APIs
    
    Args:
        query: The user's original query
        confessions: List of confession dictionaries containing text and other metadata
    
    Returns:
        A summary of the confessions in relation to the query
    """
    try:
        if not confessions:
            return "No relevant confessions found for your query."
        
        # Extract texts from confessions
        texts = [conf['text'] for conf in confessions if 'text' in conf]
        if not texts:
            return "No text content found in the provided confessions."
        
        # Extract key information
        key_phrases = extract_key_phrases(texts)
        key_sentences = get_key_sentences(texts, key_phrases)
        themes = identify_common_themes(confessions)
        
        # Generate a query-specific introduction
        intro = generate_introduction(query, len(confessions), themes)
        
        # Generate insights paragraphs from key sentences
        insights = generate_insights(key_sentences, query)
        
        # Generate advice section based on query and content
        advice = generate_advice(query, key_phrases, confessions)
        
        # Combine all sections and convert newlines to HTML paragraph breaks
        intro_html = f"<p>{intro}</p>"
        insights_html = insights.replace("\n\n", "</p><p>")
        advice_html = f"<p>{advice}</p>"
        
        summary = f"{intro_html}{insights_html}{advice_html}"
        
        return summary
            
    except Exception as e:
        logger.error(f"Error generating custom summary: {str(e)}")
        return fallback_summary(query, confessions)

def generate_introduction(query, count, themes):
    """Generate an introduction paragraph based on the query and confessions"""
    query_lower = query.lower()
    
    # Generate different intros based on query type
    if any(word in query_lower for word in ['how', 'tips', 'advice', 'way']):
        intro = f"Based on {count} relevant confessions from BITS Pilani students, I've gathered insights on {query}. "
    elif any(word in query_lower for word in ['what', 'where', 'who', 'which']):
        intro = f"After analyzing {count} confessions from BITS Pilani students, here's what I found about {query}. "
    elif any(word in query_lower for word in ['why', 'reason']):
        intro = f"From {count} BITS Pilani confessions, I've identified several perspectives on {query}. "
    else:
        intro = f"I found {count} relevant confessions from BITS Pilani students discussing {query}. "
    
    # Add themes if available
    if themes:
        theme_text = " and ".join(themes)
        intro += f"These confessions primarily relate to {theme_text}, revealing common experiences shared by BITSians."
    else:
        intro += f"These confessions reveal several experiences and perspectives shared by BITSians."
        
    return intro

def generate_insights(key_sentences, query):
    """Generate insights paragraphs from key sentences"""
    if not key_sentences:
        return "Unable to extract specific insights from the confessions."
    
    # Start with a transition sentence
    insights = "Here's what BITS students have shared:"
    
    # Group sentences into 2-3 paragraphs
    sentences_per_para = max(1, len(key_sentences) // 2)
    
    for i in range(0, len(key_sentences), sentences_per_para):
        paragraph_sentences = key_sentences[i:i+sentences_per_para]
        # Add connecting words and clean up sentences
        connected_sentences = []
        
        for j, sentence in enumerate(paragraph_sentences):
            # Clean up the sentence
            cleaned = re.sub(r'\s+', ' ', sentence).strip()
            
            # Add appropriate connectors for flow
            if j == 0:
                connected_sentences.append(cleaned)
            elif random.random() < 0.3:
                connectors = ["Additionally, ", "Moreover, ", "Furthermore, ", "Also, "]
                connected_sentences.append(f"{random.choice(connectors)}{cleaned.lower() if cleaned[0].isalpha() else cleaned}")
            else:
                connected_sentences.append(cleaned)
                
        insights += "\n\n" + " ".join(connected_sentences)
    
    return insights

def generate_advice(query, key_phrases, confessions):
    """Generate advice section based on query and content"""
    query_lower = query.lower()
    
    # Check if query is asking for advice
    if any(word in query_lower for word in ['how', 'tips', 'advice', 'help', 'way', 'should']):
        # Different advice templates based on categories
        categories = [conf.get('category', '') for conf in confessions]
        most_common = Counter(categories).most_common(1)
        
        if most_common and most_common[0][0]:
            category = most_common[0][0]
            
            if category == 'Academics':
                advice = f"Based on these experiences, consider: (1) forming study groups with peers, (2) scheduling regular meetings with professors during office hours, and (3) utilizing resources like previous year papers and online materials. Remember that many BITSians have gone through similar challenges and emerged successful."
            
            elif category == 'Campus Life':
                advice = f"From these confessions, I'd recommend: (1) getting involved in clubs or departments that match your interests, (2) being open to new friendships and experiences, and (3) finding a balance between social activities and personal time. Campus life at BITS Pilani offers diverse experiences, so don't hesitate to explore what works best for you."
            
            elif category == 'Relationships':
                advice = f"These confessions suggest: (1) maintaining open communication, (2) respecting boundaries and academic priorities, and (3) finding supportive communities on campus. Many students navigate relationships while balancing academic demands - remember that your experience is unique to you."
            
            elif category == 'Mental Health':
                advice = f"Based on these experiences, consider: (1) reaching out to the counseling services available on campus, (2) maintaining connections with friends and family, and (3) establishing healthy routines for sleep, exercise, and relaxation. Remember that seeking help is a sign of strength, not weakness."
            
            elif category == 'PS/Thesis':
                advice = f"These confessions indicate: (1) starting preparations early for PS/thesis applications, (2) networking with seniors who've been to stations you're interested in, and (3) focusing on building relevant skills rather than just grades. Your PS/thesis experience can be significantly shaped by your own initiative."
            
            else:
                advice = f"Based on these confessions, my advice would be to connect with other BITSians who have similar experiences, be patient with yourself as you navigate these challenges, and remember that the BITS community offers various resources and support systems."
        else:
            advice = f"Looking at these experiences, I'd suggest: (1) connecting with peers who share similar interests or challenges, (2) leveraging the diverse resources available at BITS Pilani, and (3) maintaining a balanced approach between academics and personal well-being."
    else:
        # For non-advice queries, provide a conclusion
        advice = f"These confessions offer valuable perspectives from the BITS community. While experiences vary widely, they highlight the diverse and rich culture at BITS Pilani. You can read the individual confessions below for more detailed accounts and personal stories."
    
    return advice

def fallback_summary(query: str, confessions: List[Dict[str, Any]]) -> str:
    """
    Generate a simple fallback summary when the main summarization method fails
    
    Args:
        query: The user's original query
        confessions: List of confession dictionaries
    
    Returns:
        A simple summary of the confessions
    """
    # Count categories for analysis
    categories = {}
    for conf in confessions:
        cat = conf.get('category', 'Unknown')
        if isinstance(cat, dict) and 'name' in cat:
            cat = cat['name']
        categories[cat] = categories.get(cat, 0) + 1
    
    most_common_category = max(categories.items(), key=lambda x: x[1])[0] if categories else "various topics"
    
    # Simple template for fallback summary with HTML formatting
    summary = f"""<p>Based on {len(confessions)} confessions from BITS Pilani students about {most_common_category.lower()}, 
I found several relevant experiences related to your query about "{query}".</p>

<p>These confessions highlight common themes and experiences among BITS Pilani students. 
Many share similar challenges and insights, particularly in relation to {most_common_category.lower()}.</p>

<p>You can read the detailed confessions below for more specific insights and personal experiences.
Remember that individual experiences vary, and what works for one person may not work for everyone.</p>"""
    
    return summary
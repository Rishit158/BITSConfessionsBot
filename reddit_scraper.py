import os
import praw
import logging
import pandas as pd
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def scrape_reddit_data(subreddits, limit=100):
    """
    Scrape confession-style posts from specified subreddits
    
    Args:
        subreddits (list): List of subreddit names to scrape
        limit (int): Maximum number of posts to scrape per subreddit
        
    Returns:
        pd.DataFrame: DataFrame containing the scraped data
    """
    try:
        # Initialize PRAW with environment variables
        reddit = praw.Reddit(
            client_id=os.environ.get('REDDIT_CLIENT_ID', 'placeholder'),
            client_secret=os.environ.get('REDDIT_CLIENT_SECRET', 'placeholder'),
            user_agent=os.environ.get('REDDIT_USER_AGENT', 'BITS Confessions Bot v1.0')
        )
        
        # Check if credentials are valid
        if not reddit.read_only:
            logger.info("Successfully authenticated with Reddit API (read-write mode)")
        else:
            logger.info("Successfully connected to Reddit API (read-only mode)")
        
        all_posts = []
        
        # Keywords to filter relevant posts
        relevant_keywords = [
            'bits', 'pilani', 'college', 'campus', 'hostel', 'mess', 'confession',
            'academics', 'professor', 'student', 'exam', 'assignment', 
            'relationship', 'mental health', 'placement', 'ps', 'thesis',
            'goa', 'hyderabad', 'professor', 'course', 'cgpa', 'grade'
        ]
        
        # Search each subreddit
        for subreddit_name in subreddits:
            try:
                logger.info(f"Scraping r/{subreddit_name}")
                subreddit = reddit.subreddit(subreddit_name)
                
                # Get posts from different categories
                for post_source in ['hot', 'new', 'top']:
                    if post_source == 'hot':
                        posts = subreddit.hot(limit=limit)
                    elif post_source == 'new':
                        posts = subreddit.new(limit=limit)
                    else:
                        posts = subreddit.top(limit=limit, time_filter='all')
                    
                    for post in posts:
                        # Filter out non-text posts and removed/deleted content
                        if not post.is_self or post.selftext in ['[removed]', '[deleted]', '']:
                            continue
                            
                        # Check if post is relevant to BITS Pilani
                        is_relevant = False
                        combined_text = (post.title + ' ' + post.selftext).lower()
                        
                        for keyword in relevant_keywords:
                            if keyword.lower() in combined_text:
                                is_relevant = True
                                break
                                
                        if not is_relevant and subreddit_name != 'BITSPilani':
                            continue
                        
                        # Extract post data
                        post_data = {
                            'id': post.id,
                            'title': post.title,
                            'text': post.selftext,
                            'score': post.score,
                            'url': f"https://www.reddit.com{post.permalink}",
                            'created_utc': datetime.fromtimestamp(post.created_utc),
                            'subreddit': subreddit_name,
                            'comment_count': post.num_comments
                        }
                        all_posts.append(post_data)
                        
                        # Also collect top comments (could contain relevant confessions)
                        post.comments.replace_more(limit=3)
                        for comment in post.comments[:10]:  # Top 10 comments
                            if comment.body in ['[removed]', '[deleted]', '']:
                                continue
                                
                            comment_data = {
                                'id': comment.id,
                                'title': f"Comment on: {post.title}",
                                'text': comment.body,
                                'score': comment.score,
                                'url': f"https://www.reddit.com{post.permalink}{comment.id}/",
                                'created_utc': datetime.fromtimestamp(comment.created_utc),
                                'subreddit': subreddit_name,
                                'comment_count': 0
                            }
                            all_posts.append(comment_data)
                
            except Exception as e:
                logger.error(f"Error scraping r/{subreddit_name}: {str(e)}")
                continue
        
        # Convert to DataFrame
        df = pd.DataFrame(all_posts)
        
        # Remove duplicates based on URL
        df = df.drop_duplicates(subset=['url'])
        
        logger.info(f"Successfully scraped {len(df)} posts and comments from Reddit")
        return df
        
    except Exception as e:
        logger.error(f"Reddit scraping error: {str(e)}")
        
        # Return empty DataFrame with expected columns if scraping fails
        return pd.DataFrame(columns=[
            'id', 'title', 'text', 'score', 'url', 'created_utc', 
            'subreddit', 'comment_count'
        ])

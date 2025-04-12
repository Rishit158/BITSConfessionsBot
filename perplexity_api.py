import os
import json
import logging
import requests
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def generate_summary(query: str, confessions: List[Dict[str, Any]]) -> Optional[str]:
    """
    Generate a summary of confessions using Perplexity API
    
    Args:
        query: The user's original query
        confessions: List of confession dictionaries containing text and other metadata
    
    Returns:
        A summary of the confessions in relation to the query, or None if API call fails
    """
    api_key = os.environ.get("PERPLEXITY_API_KEY")
    
    if not api_key:
        logger.warning("No Perplexity API key found in environment variables")
        return None
    
    try:
        # Construct the prompt with the query and confessions
        confession_texts = [f"Confession {i+1}: {conf['text']}" for i, conf in enumerate(confessions)]
        combined_confessions = "\n\n".join(confession_texts)
        
        # Create the system prompt for the API
        system_prompt = """You are a helpful AI that summarizes confessions from BITS Pilani students.
Based on the confessions provided, create a comprehensive summary that directly answers the user's query.
Your summary should:
1. Be concise yet informative (3-4 paragraphs maximum)
2. Include specific points from the confessions when relevant
3. Have a supportive, empathetic tone
4. Provide actionable advice when appropriate
5. Acknowledge different perspectives if the confessions have varied experiences
6. Write in first person as if you are summarizing experiences from the BITS Pilani community

Focus on being accurate and helpful. Don't add details that aren't supported by the confessions."""
        
        # User prompt combining the query and confessions
        user_prompt = f"""Query: {query}

Here are confessions from BITS Pilani students related to this query:

{combined_confessions}

Please summarize these confessions to directly answer the query. Create a comprehensive, well-structured response that captures the key insights from these confessions."""
        
        # Make the API request
        url = "https://api.perplexity.ai/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "llama-3.1-sonar-small-128k-online",
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            "temperature": 0.2,
            "top_p": 0.9,
            "max_tokens": 1024,
            "stream": False
        }
        
        response = requests.post(url, headers=headers, data=json.dumps(data))
        
        if response.status_code == 200:
            result = response.json()
            logger.debug(f"Perplexity API response: {result}")
            
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                logger.error("No choices found in Perplexity API response")
                return None
        else:
            logger.error(f"Perplexity API request failed with status code {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error generating summary with Perplexity API: {str(e)}")
        return None

def fallback_summary(query: str, confessions: List[Dict[str, Any]]) -> str:
    """
    Generate a simple fallback summary when Perplexity API is not available
    
    Args:
        query: The user's original query
        confessions: List of confession dictionaries
    
    Returns:
        A simple summary of the confessions
    """
    # Count categories for analysis
    categories = {}
    for conf in confessions:
        cat = conf.get('category', {}).get('name', 'Unknown')
        categories[cat] = categories.get(cat, 0) + 1
    
    most_common_category = max(categories.items(), key=lambda x: x[1])[0] if categories else "various topics"
    
    # Simple template for fallback summary
    summary = f"""Based on {len(confessions)} confessions from BITS Pilani students about {most_common_category.lower()}, 
I found several relevant experiences related to your query about "{query}".

These confessions highlight common themes and experiences among BITS Pilani students. 
You can read the detailed confessions below for more specific insights and personal experiences."""
    
    return summary
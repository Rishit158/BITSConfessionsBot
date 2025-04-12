# BITS Confessions Bot

A Flask-based web application that enables users to search, browse, and receive AI-generated summaries of anonymous confessions from BITS Pilani students scraped from Reddit.

![BITS Confessions Bot](static/img/hero-image.png)

## 🚀 Features

- **Smart Search**: Find relevant confessions based on your queries
- **AI-Powered Summaries**: Get Perplexity-like summaries of multiple confessions without using external APIs
- **Category Browsing**: Explore confessions organized by categories (Academics, Campus Life, Relationships, etc.)
- **Chat-Style Interface**: Ask follow-up questions after getting summarized results
- **Responsive Design**: Works on desktop and mobile devices

## 📋 Table of Contents

- [Demo](#-demo)
- [Technology Stack](#-technology-stack)
- [Installation](#-installation)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [Data Sources](#-data-sources)
- [How It Works](#-how-it-works)
- [Contributing](#-contributing)
- [License](#-license)

## 🌐 Demo

Access the live demo: [BITS Confessions Bot Demo](https://your-app.replit.app) *(Replace with your deployed URL)*

## 💻 Technology Stack

- **Backend**: Python, Flask, SQLAlchemy
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Data Processing**: NLTK, Pandas, Scikit-learn
- **Data Source**: Reddit via PRAW API
- **Database**: SQLite (default), PostgreSQL (production)

## 🔧 Installation

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/bits-confessions-bot.git
cd bits-confessions-bot
```

2. **Create a virtual environment**

```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Set up NLTK data**

```python
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"
```

5. **Initialize the database**

```python
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

## 🚀 Usage

1. **Run the application**

```bash
python main.py
```

2. **Access the web interface**

Open your browser and go to: `http://localhost:5000`

3. **Search for confessions**

Enter a query in the search box to find relevant confessions

4. **Browse by category**

Click on any category card to see confessions from that specific category

5. **Get AI summaries**

Enable the "Summarize Results" option to get AI-generated insights

## 📁 Project Structure

```
bits-confessions-bot/
├── app.py              # Flask application setup and routes
├── main.py             # Application entry point
├── models.py           # Database models
├── perplexity_api.py   # Custom summarization logic
├── reddit_scraper.py   # Reddit data scraping functionality
├── text_processor.py   # Text processing utilities
├── static/             # Static files (CSS, JS, images)
│   ├── css/
│   └── js/
├── templates/          # HTML templates
├── instance/           # Database files
└── README.md           # Project documentation
```

## 📊 Data Sources

The application scrapes confession-style posts from the following subreddits:
- r/BITSPilani
- r/Indian_Academia 
- r/bitsians

Data is categorized into the following topics:
- Academics
- Campus Life
- Relationships
- Mental Health
- PS/Thesis
- General

## 🔍 How It Works

1. **Data Collection**: The application scrapes confession-style posts from relevant subreddits.
2. **Text Processing**: Posts are cleaned, tokenized, and categorized using NLP techniques.
3. **Search**: When a user submits a query, the application finds the most similar confessions using TF-IDF and cosine similarity.
4. **Summarization**: A custom algorithm extracts key phrases and sentences, identifies themes, and generates a structured response similar to Perplexity's format.
5. **Presentation**: Results are displayed with highlighted search terms and organized by relevance.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.
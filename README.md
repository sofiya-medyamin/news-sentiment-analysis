<header>

<!--
  <<< Author notes: Course header >>>
  Include a 1280×640 image, course title in sentence case, and a concise description in emphasis.
  In your repository settings: enable template repository, add your 1280×640 social image, auto delete head branches.
  Add your open source license, GitHub uses MIT license.
-->

# News Sentiment Analysis using Streamlit

</header>

### Overview
This is a Streamlit dashboard that fetches news headlines from a live news API, performs sentiment analysis on the articles, and visualizes the overall tone (positive, negative, neutral) of the news.

👉 **[Live Demo on Streamlit](https://sofiya-medyamin-news-sentiment-analysis.streamlit.app/)**

## Features
- Fetches real-time news using NewsAPI
- Sentiment analysis using TextBlob
- Interactive bar chart with Altair
- Download filtered articles as CSV

### 🧰 **Tools  Used**:
- **Python**
- **Streamlit**
- **News API** (like [NewsAPI.org](https://newsapi.org/))
- **TextBlob** (for sentiment analysis)
- **Pandas** & **Altair** (for visualization)

### Usage
- Enter your search topics in the sidebar.
- Adjust the number of articles to fetch.
- Explore the sentiment table, chart, and article tabs.
- Download the filtered articles as CSV if desired.

### Deployment
- The app is deployable on Streamlit Cloud.
- When deploying, add your NEWS_API_KEY as a secret in the Streamlit Cloud dashboard instead of using a .env file.

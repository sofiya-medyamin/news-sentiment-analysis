from dotenv import load_dotenv
import os
import streamlit as st
import pandas as pd
import requests
from textblob import TextBlob
from datetime import datetime, timedelta
import altair as alt


# ---- CONFIGURATION ----
st.set_page_config(
    page_title="News Sentiment Analysis",
    initial_sidebar_state="expanded",
    layout="wide"
)

# ---- API DETAILS ----
load_dotenv()  # Load environment variables from .env file

API_KEY = os.getenv("NEWS_API_KEY")
NEWS_ENDPOINT = "https://newsapi.org/v2/everything"


# ---- HELPER FUNCTION: GET SENTIMENT LABEL ----
# Converts numerical sentiment score into a readable label
def get_sentiment_label(score):
    if score > 0.1:
        return "😊 Positive"
    elif score < -0.1:
        return "😠 Negative"
    else:
        return "😐 Neutral"


# ---- STREAMLIT APP TITLE ----
st.markdown("<h1 style='text-align: left;'>📰 News Sentiment Analysis</h1>", unsafe_allow_html=True)


# ---- SIDEBAR FOR USER INPUTS ----
with st.sidebar:
    st.markdown("### Search Parameters")
    # User input for news topic
    query = st.text_input("Enter a topic to search for:", value="AI, Technology, Economy, & Others")
    # Slider for controlling the number of articles to fetch
    num_articles = st.slider("Number of Articles", 5, 50, 25)


# ---- FUNCTION: FETCH NEWS ARTICLES FROM API ----
# Prepare dictionary (params) to send to the API
def fetch_articles(query, limit):
    params = {
        "q": query,           # Search query
        "language": "en",     # English articles
        "pageSize": limit,    # Number of articles per request
        "apiKey": API_KEY     # API key
    }
    
    # Make a GET request to the News API
    response = requests.get(NEWS_ENDPOINT, params=params) 
    if response.status_code == 200:
        return response.json().get("articles", []) # Return list of articles. If missing, return an empty list
    else:
        st.error(f"Failed to fetch news articles. Status Code: {response.status_code}")
        return [] # Empty list if request fails. To prevent app crash

# Fetch raw articles from the API
raw_articles = fetch_articles(query, num_articles)


# ---- FUNCTION: PROCESS AND ANALYZE ARTICLES ----
# Processes raw articles, extracts data, calculates sentiment, and includes source
def process_articles(articles):
    processed_data = []
    for article in articles:
        try:
            title = article.get("title")
            description = article.get("description", "")
            date_str = article.get("publishedAt") # Get the published date string
            source_name = article.get("source", {}).get("name", "Unknown") # different than description bcs source is a nested dict
            source_url = article.get("url", "") # Get the source URL if available

            # Skip to the next article if title or date is missing
            if not title or not date_str:
                continue
            
            # Convert published date string to a Python datetime object
            date_obj = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")

            # Ensure description is a string even if originally None
            if description is None:
                description = "" # convert None to empty string to avoid TypeError
                
            if source_url is None:
                source_url = ""

            # Combine title and description for comprehensive sentiment analysis
            content_for_sentiment = title + " " + description
            
            # Calculate sentiment polarity using TextBlob
            blob = TextBlob(content_for_sentiment)
            polarity = blob.sentiment.polarity
            

            # Append all relevant processed data to the list
            processed_data.append({
                "title": title,
                "description": description,
                "date": date_obj,          # Datetime object for easy filtering
                "polarity": polarity,       # Numerical sentiment score
                "sentiment_label": get_sentiment_label(polarity), # Human-readable sentiment
                "source": source_name,      # Article source name
                "source_url": source_url    # URL of the article source
            })
        except (KeyError, ValueError, TypeError) as e:
            # Log a warning and skip the article if parsing fails
            st.warning(f"Skipping article due to parsing error: {e}")
            continue
    return processed_data

# Process all fetched raw articles into a structured list
parsed_articles = process_articles(raw_articles)

# Create a Pandas DataFrame from the processed articles for dashboard elements
df = pd.DataFrame(parsed_articles)


# ---- FILTER ARTICLES BY DATE (for tabs) ----
# Define today's date and the start of the current week
today = datetime.now().date() # get date only, not time
start_of_week = today - timedelta(days=today.weekday()) 

# Filter articles for specific date ranges
today_articles = [a for a in parsed_articles if a["date"].date() == today]
week_articles = [a for a in parsed_articles if start_of_week <= a["date"].date() <= today]
all_articles = parsed_articles # 'All Time' tab simply shows all processed articles

# ---- DASHBOARD METRICS AND VISUALIZATIONS ----
# Create two columns for dashboard layout
col1, col2, spacer1, spacer2, col3 = st.columns([1, 1, 1, 1, 1])

with col1:
    st.metric("📈 Avg Sentiment Polarity", round(df["polarity"].mean(), 2) if not df.empty else 0.0)
    st.markdown("")

with col2:
    st.metric("🗞️ Articles Analyzed", len(df))
    st.markdown("")

with col3:
    st.download_button("📥 Download as CSV", df.to_csv(index=False), file_name="filtered_articles.csv")


st.markdown("### 📰 Article Sentiment Table")


# Display a table showing title, sentiment label, polarity, and source
# Capitalize the first letter for each column name
df_display = df[["title", "sentiment_label", "polarity", "source"]].rename(
    columns={
        "title": "Title",
        "sentiment_label": "Sentiment",
        "polarity": "Polarity",
        "source": "Source"
    }
)

st.dataframe(df_display, use_container_width=True)

st.markdown("### 📊 Sentiment Distribution")
# Display a bar chart of sentiment polarity
df["color"] = df["polarity"].apply(
    lambda x: "darkseagreen" if x > 0 else ("darkred" if x < 0 else "darkorange")
)

# Create bar chart using Altair
df = df.reset_index(drop=True)  # Ensure the index is clean
df["article_id"] = df.index  # Create a simple numeric label

chart = alt.Chart(df).mark_bar().encode(  # alt.Chart(df) accesses the entire df dataframe (index, title... color)
    x=alt.X("article_id:O", title="Articles based on Index", axis=alt.Axis(labelAngle=0)),
    y=alt.Y("polarity:Q", title="Sentiment Polarity"),
    color=alt.Color("color:N", scale=None),
    tooltip=["title", "polarity"]
).properties(
    width=500,
    height=400,
)


# Show chart in Streamlit
st.altair_chart(chart, use_container_width=True)


# ---- STREAMLIT TABS FOR NEWS DISPLAY ----
# Define three tabs for organizing news articles by date
tab1, tab2, tab3 = st.tabs(["📅 Today", "📆 This Week", "🕰️ All Time"])


# ---- FUNCTION: DISPLAY ARTICLES IN TABS ----
# Iterates through a list of article dictionaries and displays their details
def display_articles(articles_list_of_dicts):
    if not articles_list_of_dicts:
        st.info("No articles found for this period.")
        return
    for article_data in articles_list_of_dicts:
        st.markdown(f"**{article_data['title']}**")
        
        # Display published date/time and the article source
        st.caption(f"{article_data['date'].strftime('%Y-%m-%d %H:%M')} | Source: {article_data['source']}")
        
        # Display the pre-calculated sentiment label
        st.write(f"Sentiment: {article_data['sentiment_label']}")
        
        # Display URL if available
        if article_data['source_url']: # Check if source URL exists
            st.markdown(f"[Read more]({article_data['source_url']})")
        else:
            st.write("No source URL available.")
        
        # Display source URL if available
        st.markdown("---") # Visual separator between articles


# ---- TAB CONTENT DISPLAY ----
with tab1:
    st.subheader("Today's News")
    display_articles(today_articles)

with tab2:
    st.subheader("This Week's News")
    display_articles(week_articles)

with tab3:
    st.subheader("All Articles")
    display_articles(all_articles)

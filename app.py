import streamlit as st
import pandas as pd
import requests
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from bs4 import BeautifulSoup
from stqdm import stqdm
import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Load environment variables
load_dotenv()

# Initialize Spotify API
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=os.getenv('SPOTIFY_CLIENT_ID'), client_secret=os.getenv('SPOTIFY_CLIENT_SECRET')))

# Function to fetch YouTube links using Selenium
def fetch_youtube_links(df, song_col, album_col):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    with webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options) as driver:
        youtube_links = []
        for index, row in stqdm(df.iterrows(), desc="Fetching YouTube Links"):
            try:
                song_name = row[song_col]
                album_name = row[album_col]
                search_query = f"{song_name} {album_name}"
                url = f"https://www.youtube.com/results?search_query={search_query}"
                driver.get(url)
                driver.implicitly_wait(5)
                video_tags = driver.find_elements(By.CSS_SELECTOR, "a.yt-simple-endpoint.style-scope.ytd-video-renderer")
                if video_tags:
                    video_id = video_tags[0].get_attribute('href').split("=")[1]
                    youtube_links.append(f"https://www.youtube.com/watch?v={video_id}")
                else:
                    youtube_links.append(None)
            except Exception as e:
                youtube_links.append(None)
                st.error(f"Error fetching YouTube link for {song_name} - {album_name}: {e}")
        return youtube_links

# Function to fetch YouTube views using ScraperAPI
def fetch_youtube_views(df, link_col):
    scraper_api_key = os.getenv('SCRAPER_API_KEY')
    views = []
    for index, row in stqdm(df.iterrows(), desc="Fetching YouTube Views"):
        try:
            link = row[link_col]
            if pd.isna(link):
                views.append(None)
                continue
            response = requests.get(link, headers={'X-API-KEY': scraper_api_key})
            soup = BeautifulSoup(response.text, 'html.parser')
            view_tag = soup.find("meta", itemprop="interactionCount")
            if view_tag:
                view_count = int(view_tag['content'].replace(',', ''))
                views_in_millions = view_count // 1_000_000
                views.append(views_in_millions)
            else:
                views.append(None)
        except Exception as e:
            views.append(None)
            st.error(f"Error fetching YouTube views for {link}: {e}")
    return views

# Function to fetch Spotify links using Spotify API
def fetch_spotify_links(df, song_col, album_col):
    spotify_links = []
    for index, row in stqdm(df.iterrows(), desc="Fetching Spotify Links"):
        try:
            song_name = row[song_col]
            album_name = row[album_col]
            results = sp.search(q=f"track:{song_name} album:{album_name}", type="track", limit=1)
            if results['tracks']['items']:
                spotify_links.append(results['tracks']['items'][0]['external_urls']['spotify'])
            else:
                spotify_links.append(None)
        except Exception as e:
            spotify_links.append(None)
            st.error(f"Error fetching Spotify link for {song_name} - {album_name}: {e}")
    return spotify_links

# Function to fetch Spotify play counts using Selenium
def fetch_spotify_playcounts(df, link_col):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    with webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options) as driver:
        playcounts = []
        for index, row in stqdm(df.iterrows(), desc="Fetching Spotify Playcounts"):
            try:
                link = row[link_col]
                if pd.isna(link):
                    playcounts.append(None)
                    continue
                driver.get(link)
                driver.implicitly_wait(5)
                playcount_tag = driver.find_element(By.CSS_SELECTOR, 'meta[property="music:playcount"]')
                if playcount_tag:
                    playcount = int(playcount_tag.get_attribute('content').replace(',', ''))
                    playcounts.append(playcount)
                else:
                    playcounts.append(None)
            except Exception as e:
                playcounts.append(None)
                st.error(f"Error fetching Spotify playcount for {link}: {e}")
        return playcounts

# Streamlit App
st.image("mirchi_logo.png", use_container_width=False, width=100)
st.title("Mirchi Playlist Tracker v1")
st.sidebar.header("Guide")
st.sidebar.markdown("""
1. Upload your Excel file.
2. Select the sheet for YouTube and Spotify data.
3. Select the columns for each task.
4. Configure the output columns.
5. Click the buttons to process the data.
6. Download the updated Excel file.
""", unsafe_allow_html=True)

# Upload Excel file
uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])
if uploaded_file is not None:
    xls = pd.ExcelFile(uploaded_file)
    sheet_names = xls.sheet_names
    
    # Select sheets
    youtube_sheet = st.selectbox("Select the sheet for YouTube data", sheet_names)
    spotify_sheet = st.selectbox("Select the sheet for Spotify data", sheet_names)
    
    # Load dataframes
    df_youtube = pd.read_excel(xls, sheet_name=youtube_sheet)
    df_spotify = pd.read_excel(xls, sheet_name=spotify_sheet)
    
    st.write("Uploaded YouTube DataFrame:")
    st.write(df_youtube.head())
    st.write("Uploaded Spotify DataFrame:")
    st.write(df_spotify.head())

    # Column selection for YouTube links
    st.header("YouTube Links")
    song_col_yt = st.selectbox("Select Song Name column for YouTube Links", df_youtube.columns, key="song_col_yt")
    album_col_yt = st.selectbox("Select Album Name column for YouTube Links", df_youtube.columns, key="album_col_yt")
    yt_link_output_col = st.text_input("Output column for YouTube Links", "YouTube Links", key="yt_link_output_col")

    # Column selection for YouTube views
    st.header("YouTube Views")
    yt_link_col = st.selectbox("Select YouTube Links column for YouTube Views", df_youtube.columns, key="yt_link_col")
    yt_view_output_col = st.text_input("Output column for YouTube Views", "YouTube Views", key="yt_view_output_col")

    # Column selection for Spotify links
    st.header("Spotify Links")
    song_col_sp = st.selectbox("Select Song Name column for Spotify Links", df_spotify.columns, key="song_col_sp")
    album_col_sp = st.selectbox("Select Album Name column for Spotify Links", df_spotify.columns, key="album_col_sp")
    sp_link_output_col = st.text_input("Output column for Spotify Links", "Spotify Links", key="sp_link_output_col")

    # Column selection for Spotify playcounts
    st.header("Spotify Playcounts")
    sp_link_col = st.selectbox("Select Spotify Links column for Spotify Playcounts", df_spotify.columns, key="sp_link_col")
    sp_playcount_output_col = st.text_input("Output column for Spotify Playcounts", "Spotify Playcounts", key="sp_playcount_output_col")

    # Process YouTube Links
    if st.button("Fetch YouTube Links"):
        df_youtube[yt_link_output_col] = fetch_youtube_links(df_youtube, song_col_yt, album_col_yt)
        st.write("Updated YouTube DataFrame:")
        st.write(df_youtube.head())

    # Process YouTube Views
    if st.button("Fetch YouTube Views"):
        df_youtube[yt_view_output_col] = fetch_youtube_views(df_youtube, yt_link_col)
        st.write("Updated YouTube DataFrame:")
        st.write(df_youtube.head())

    # Process Spotify Links
    if st.button("Fetch Spotify Links"):
        df_spotify[sp_link_output_col] = fetch_spotify_links(df_spotify, song_col_sp, album_col_sp)
        st.write("Updated Spotify DataFrame:")
        st.write(df_spotify.head())

    # Process Spotify Playcounts
    if st.button("Fetch Spotify Playcounts"):
        df_spotify[sp_playcount_output_col] = fetch_spotify_playcounts(df_spotify, sp_link_col)
        st.write("Updated Spotify DataFrame:")
        st.write(df_spotify.head())

    # Download the updated Excel file
    if st.button("Download Updated Excel File"):
        with pd.ExcelWriter('updated_file.xlsx') as writer:
            df_youtube.to_excel(writer, sheet_name=youtube_sheet, index=False)
            df_spotify.to_excel(writer, sheet_name=spotify_sheet, index=False)
        with open('updated_file.xlsx', 'rb') as f:
            st.download_button("Download Excel", f, file_name="updated_file.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# Custom CSS for design
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(to right, #ffcc00, #ff6600);
        color: white;
    }
    .stTitle {
        color: white;
    }
    .stButton > button {
        background-color: #ff6600;
        color: white;
        border: none;
        padding: 10px 20px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 4px;
    }
    .stButton > button:hover {
        background-color: #ff9900;
    }
    .stSelectbox > label {
        color: black;
    }
    .stTextInput > label {
        color: black;
    }
    .stSidebar .markdown-text {
        color: black;
    }
</style>
""", unsafe_allow_html=True)
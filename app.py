import streamlit as st
import pandas as pd
import io
from yt_dlp import YoutubeDL
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from playwright.sync_api import sync_playwright
import time
from stqdm import stqdm




# Set page configuration
st.set_page_config(page_title="Playlist Tracker", page_icon="🎵", layout="wide")


# Custom CSS for Material Design
st.markdown(
    """
    <style>
    /* Full-page background */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
        background-color: #ffffff !important; /* Bright yellow */
        font-family: 'Roboto', sans-serif;
    }
    /* Logo and Title */
    .logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 20px;
    }
    .logo-container img {
        width: 150px;
        height: auto;
    }
    .main-title {
        text-align: center;
        font-size: 36px;
        font-weight: bold;
        color: #e30512;
        margin-top: 10px;
    }
    /* Card style */
    .card {
        background: white;
        padding: 15px;
        margin-bottom: 15px;
        border-radius: 8px;
        box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
    }
    .task-header {
        font-size: 18px;
        font-weight: bold;
        margin-bottom: 10px;
        color: #e30512;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Logo and Title
st.markdown(
    """
    <div class="logo-container">
        <img src="mirchi_logo.png" alt="Mirchi Logo">
    </div>
    <div class="main-title">Mirchi Playlist Tracker V1</div>
    """,
    unsafe_allow_html=True,
)

# Persistent issue tracker
error_tracker = {"error_count": 0}

# Function to log errors
def log_error(error_message):
    error_tracker["error_count"] += 1
    if error_tracker["error_count"] >= 3:  # Set threshold for recurring issues
        st.error(f"Recurring Issue Detected: {error_message}")
        st.info("Contact Developer: siddhant.sharma@timesgroup.com")
    else:
        st.warning(f"Error Occurred: {error_message}")


# Spotify API credentials (hardcoded)
SPOTIFY_CLIENT_ID = "09977d3dd0cc42e7b96e444a1dda16d8"
SPOTIFY_CLIENT_SECRET = "d68fbcd41dcf45da83f977aa9d4ddb17"

# Sidebar
with st.sidebar:
    st.header("App Guide")
    st.write("""
    1. Upload an Excel file.
    2. Select one or more tasks to perform.
    3. Choose inputs and outputs for each task.
    4. Process the tasks and download the results.
    """)

# Upload Excel file
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:
    try:
        excel_data = pd.ExcelFile(uploaded_file)
        sheet_names = excel_data.sheet_names
        st.success(f"Found {len(sheet_names)} sheet(s): {sheet_names}")
    except Exception as e:
        st.error(f"Error reading Excel file: {e}")
else:
    st.warning("Please upload a valid Excel file to proceed.")

# Task Selection
operation = st.sidebar.multiselect(
    "Select Tasks to Perform",
    ["YouTube Links", "YouTube Views", "Spotify Links", "Spotify Playcount"],
)

if uploaded_file:
    st.markdown("## Input Configuration")

    # Unique keys for dropdowns
    youtube_sheet_key = "youtube_sheet_selection"
    spotify_sheet_key = "spotify_sheet_selection"

    # Dropdowns to select sheets for YouTube and Spotify tasks
    youtube_sheet_name = st.selectbox(
        "Select Sheet for YouTube Tasks", 
        options=sheet_names, 
        key=youtube_sheet_key
    )
    spotify_sheet_name = st.selectbox(
        "Select Sheet for Spotify Tasks", 
        options=sheet_names, 
        key=spotify_sheet_key
    )

    # Show a preview of the selected sheets
    st.markdown("### YouTube Sheet Preview")
    youtube_preview = pd.read_excel(uploaded_file, sheet_name=youtube_sheet_name)
    st.dataframe(youtube_preview.head(10))  # Show top 10 rows

    st.markdown("### Spotify Sheet Preview")
    spotify_preview = pd.read_excel(uploaded_file, sheet_name=spotify_sheet_name)
    st.dataframe(spotify_preview.head(10))  # Show top 10 rows

    # Initialize the DataFrame globally based on selected tasks
    if operation:
        if "YouTube" in operation[0]:  # If YouTube-related tasks are selected
            df = youtube_preview.copy()
        elif "Spotify" in operation[0]:  # If Spotify-related tasks are selected
            df = spotify_preview.copy()

    # Iterate through selected tasks and configure each dynamically
    for task in operation:
        st.markdown(f"## Configuration for {task}")
        task_key = task.replace(" ", "_").lower()  # Generate unique suffix for task-related keys

        if "YouTube Links" in task:
            st.markdown('<div class="task-header">YouTube Links Configuration</div>', unsafe_allow_html=True)
            with st.container():
                song_column_youtube = st.selectbox(
                    "Select Column for Song Names (YouTube Links)", 
                    options=youtube_preview.columns, 
                    key=f"song_col_youtube_links_{task_key}"
                )
                album_column_youtube = st.selectbox(
                    "Select Column for Album Names (YouTube Links)", 
                    options=youtube_preview.columns, 
                    key=f"album_col_youtube_links_{task_key}"
                )
                output_column_links_option_youtube = st.radio(
                    "Output Column for YouTube Links",
                    options=["Create New Column", "Use Existing Column"],
                    index=0,
                    key=f"output_option_youtube_links_{task_key}"
                )
                output_column_links_youtube = (
                    st.selectbox(
                        "Select Existing Output Column for YouTube Links", 
                        options=youtube_preview.columns, 
                        key=f"output_col_youtube_links_{task_key}"
                    )
                    if output_column_links_option_youtube == "Use Existing Column"
                    else st.text_input(
                        "Enter New Column Name for YouTube Links", 
                        value="YouTube_Links", 
                        key=f"new_output_col_youtube_links_{task_key}"
                    )
                )

        if "YouTube Views" in task:
            st.markdown('<div class="task-header">YouTube Views Configuration</div>', unsafe_allow_html=True)
            with st.container():
                link_column_youtube_views = st.selectbox(
                    "Select Column for YouTube Links (YouTube Views)", 
                    options=youtube_preview.columns, 
                    key=f"link_col_youtube_views_{task_key}"
                )
                output_column_stats_option_youtube_views = st.radio(
                    "Output Column for YouTube Views",
                    options=["Create New Column", "Use Existing Column"],
                    index=0,
                    key=f"output_option_youtube_views_{task_key}"
                )
                output_column_stats_youtube_views = (
                    st.selectbox(
                        "Select Existing Output Column for YouTube Views", 
                        options=youtube_preview.columns, 
                        key=f"output_col_youtube_views_{task_key}"
                    )
                    if output_column_stats_option_youtube_views == "Use Existing Column"
                    else st.text_input(
                        "Enter New Column Name for YouTube Views", 
                        value="YouTube_Views", 
                        key=f"new_output_col_youtube_views_{task_key}"
                    )
                )

        if "Spotify Links" in task:
            st.markdown('<div class="task-header">Spotify Links Configuration</div>', unsafe_allow_html=True)
            with st.container():
                song_column_spotify = st.selectbox(
                    "Select Column for Song Names (Spotify Links)", 
                    options=spotify_preview.columns, 
                    key=f"song_col_spotify_links_{task_key}"
                )
                album_column_spotify = st.selectbox(
                    "Select Column for Album Names (Spotify Links)", 
                    options=spotify_preview.columns, 
                    key=f"album_col_spotify_links_{task_key}"
                )
                output_column_links_option_spotify = st.radio(
                    "Output Column for Spotify Links",
                    options=["Create New Column", "Use Existing Column"],
                    index=0,
                    key=f"output_option_spotify_links_{task_key}"
                )
                output_column_links_spotify = (
                    st.selectbox(
                        "Select Existing Output Column for Spotify Links", 
                        options=spotify_preview.columns, 
                        key=f"output_col_spotify_links_{task_key}"
                    )
                    if output_column_links_option_spotify == "Use Existing Column"
                    else st.text_input(
                        "Enter New Column Name for Spotify Links", 
                        value="Spotify_Links", 
                        key=f"new_output_col_spotify_links_{task_key}"
                    )
                )

        if "Spotify Playcount" in task:
            st.markdown('<div class="task-header">Spotify Playcount Configuration</div>', unsafe_allow_html=True)
            with st.container():
                link_column_spotify_playcount = st.selectbox(
                    "Select Column for Spotify Links (Spotify Playcount)", 
                    options=spotify_preview.columns, 
                    key=f"link_col_spotify_playcount_{task_key}"
                )
                output_column_stats_option_spotify_playcount = st.radio(
                    "Output Column for Spotify Playcount",
                    options=["Create New Column", "Use Existing Column"],
                    index=0,
                    key=f"output_option_spotify_playcount_{task_key}"
                )
                output_column_stats_spotify_playcount = (
                    st.selectbox(
                        "Select Existing Output Column for Spotify Playcount", 
                        options=spotify_preview.columns, 
                        key=f"output_col_spotify_playcount_{task_key}"
                    )
                    if output_column_stats_option_spotify_playcount == "Use Existing Column"
                    else st.text_input(
                        "Enter New Column Name for Spotify Playcount", 
                        value="Spotify_Playcount", 
                        key=f"new_output_col_spotify_playcount_{task_key}"
                    )
                )





# Helper Functions


def fetch_youtube_link(song_name, album_name):
    ydl_opts = {"quiet": True, "format": "best"}
    query = f"{song_name} {album_name}"
    try:
        with YoutubeDL(ydl_opts) as ydl:
            results = ydl.extract_info(f"ytsearch:{query}", download=False)
            video = max(results["entries"], key=lambda x: x.get("view_count", 0))
            return video["webpage_url"]
    except Exception as e:
        return f"Error: {str(e)}"

def fetch_youtube_views(video_url):
    ydl_opts = {"quiet": True}
    try:
        with YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(video_url, download=False)
            views = result.get("view_count", 0)
            return f"{views / 1_000_000:.1f}M" if views >= 1_000_000 else f"{views // 1_000}K"
    except Exception as e:
        return f"Error: {str(e)}"

def fetch_spotify_playcount(track_url):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            # Navigate to the Spotify track URL
            page.goto(track_url, timeout=60000)  # 60 seconds timeout for loading the page
            
            # Wait for the playcount element to appear
            playcount_selector = '[data-testid="playcount"]'
            page.wait_for_selector(playcount_selector, timeout=30000)  # Wait up to 30 seconds

            # Extract the playcount text
            playcount_text = page.locator(playcount_selector).inner_text()

            # Convert playcount to integer (remove commas and non-numeric characters)
            playcount = int(playcount_text.replace(',', '').strip())

            browser.close()
            return playcount

    except Exception as e:
        if "Timeout" in str(e):
            return "Error: Timeout while fetching playcount. Try again later."
        else:
            return f"Error: {str(e)}"

def fetch_spotify_link(song_name, album_name):
    try:
        sp = Spotify(auth_manager=SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET))
        results = sp.search(q=f"track:{song_name} album:{album_name}", type="track", limit=1)
        if results["tracks"]["items"]:
            return results["tracks"]["items"][0]["external_urls"]["spotify"]
        else:
            return "Song Not Found"
    except Exception as e:
        return f"Error: {str(e)}"

if st.button("Process Tasks"):
    if uploaded_file and operation:  # Initialize progress bar and time tracking
        total_rows = len(youtube_preview) if "YouTube" in operation else len(spotify_preview)
        start_time = time.time()

        # Iterate through the selected tasks and process each
        for task in operation:
            if "YouTube Links" in task:
                st.info("Processing YouTube Links...")
                youtube_preview[output_column_links_youtube] = ""
                for idx, row in stqdm(youtube_preview.iterrows(), total=total_rows, desc="Processing YouTube Links"):
                    # Fetch song and album from user-selected columns
                    song_name = row[song_column_youtube]
                    album_name = row[album_column_youtube]

                    # Logic to fetch YouTube links
                    youtube_link = fetch_youtube_link(song_name, album_name)

                    # Store results in the output column
                    youtube_preview.at[idx, output_column_links_youtube] = youtube_link

                    # Calculate progress and time remaining
                    progress = (idx + 1) / total_rows
                    elapsed_time = time.time() - start_time
                    estimated_total_time = elapsed_time / progress
                    estimated_time_remaining = estimated_total_time - elapsed_time

                    st.info(f"Progress: {progress * 100:.2f}% | Estimated time remaining: {estimated_time_remaining:.2f} seconds")

                st.success(f"YouTube Links processed and saved to column '{output_column_links_youtube}'.")

            if "YouTube Views" in task:
                st.info("Processing YouTube Views...")
                youtube_preview[output_column_stats_youtube_views] = ""
                for idx, row in stqdm(youtube_preview.iterrows(), total=total_rows, desc="Processing YouTube Views"):
                    # Fetch YouTube link from user-selected column
                    youtube_url = row[link_column_youtube_views]

                    # Logic to fetch YouTube views
                    youtube_views = fetch_youtube_views(youtube_url)

                    # Store results in the output column
                    youtube_preview.at[idx, output_column_stats_youtube_views] = youtube_views

                    # Calculate progress and time remaining
                    progress = (idx + 1) / total_rows
                    elapsed_time = time.time() - start_time
                    estimated_total_time = elapsed_time / progress
                    estimated_time_remaining = estimated_total_time - elapsed_time

                    st.info(f"Progress: {progress * 100:.2f}% | Estimated time remaining: {estimated_time_remaining:.2f} seconds")

                st.success(f"YouTube Views processed and saved to column '{output_column_stats_youtube_views}'.")

            if "Spotify Links" in task:
                st.info("Processing Spotify Links...")
                spotify_preview[output_column_links_spotify] = ""
                for idx, row in stqdm(spotify_preview.iterrows(), total=total_rows, desc="Processing Spotify Links"):
                    # Fetch song and album from user-selected columns
                    song_name = row[song_column_spotify]
                    album_name = row[album_column_spotify]

                    # Logic to fetch Spotify links
                    spotify_link = fetch_spotify_link(song_name, album_name)

                    # Store results in the output column
                    spotify_preview.at[idx, output_column_links_spotify] = spotify_link

                    # Calculate progress and time remaining
                    progress = (idx + 1) / total_rows
                    elapsed_time = time.time() - start_time
                    estimated_total_time = elapsed_time / progress
                    estimated_time_remaining = estimated_total_time - elapsed_time

                    st.info(f"Progress: {progress * 100:.2f}% | Estimated time remaining: {estimated_time_remaining:.2f} seconds")

                st.success(f"Spotify Links processed and saved to column '{output_column_links_spotify}'.")

            if "Spotify Playcount" in task:
                st.info("Processing Spotify Playcount...")
                spotify_preview[output_column_stats_spotify_playcount] = ""
                for idx, row in stqdm(spotify_preview.iterrows(), total=total_rows, desc="Processing Spotify Playcount"):
                    # Fetch Spotify link from user-selected column
                    spotify_url = row[link_column_spotify_playcount]

                    # Logic to fetch Spotify playcount
                    spotify_playcount = fetch_spotify_playcount(spotify_url)

                    # Store results in the output column
                    spotify_preview.at[idx, output_column_stats_spotify_playcount] = spotify_playcount

                    # Calculate progress and time remaining
                    progress = (idx + 1) / total_rows
                    elapsed_time = time.time() - start_time
                    estimated_total_time = elapsed_time / progress
                    estimated_time_remaining = estimated_total_time - elapsed_time

                    st.info(f"Progress: {progress * 100:.2f}% | Estimated time remaining: {estimated_time_remaining:.2f} seconds")

                st.success(f"Spotify Playcount processed and saved to column '{output_column_stats_spotify_playcount}'.")

        # Final output for download
        st.info("Saving results...")
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            youtube_preview.to_excel(writer, sheet_name=youtube_sheet_name, index=False)
            spotify_preview.to_excel(writer, sheet_name=spotify_sheet_name, index=False)
        output.seek(0)

        st.success("Processing complete! Download your file below:")
        st.download_button(
            label="Download Processed File",
            data=output,
            file_name="processed_playlist.xlsx"
        )
    else:
        st.error("Please upload a file and select tasks before processing.")
        
        # Function to process each task with progress bar and estimated time remaining
def process_task(df, task_name, total_rows, start_time, fetch_function, column1, column2, output_column, output_option):
    task_counter = 0
    for idx, row in df.iterrows():
         # Fetch data based on the task and store the result
        result = fetch_function(*args)
        if isinstance(result, tuple):
            df.at[idx, result[0]] = result[1]
        else:
            df.at[idx, output_column] = result
        # Fetch data from user-selected columns
        data1 = row[column1]
        data2 = row[column2] if column2 else None

        # Logic to fetch data based on the task
        result = fetch_function(data1, data2)
        
        # Store results in the output column
        if output_option == "Create New Column":
            df[output_column] = ""
        df.at[idx, output_column] = result
        # Update progress bar
        
        
        progress_percentage = (i + 1) / len(operation)
        progress_bar.progress(progress_percentage)
        st.progress(progress_percentage)

        # Calculate and display estimated time remaining
        elapsed_time = time.time() - start_time
        estimated_total_time = elapsed_time / progress_percentage
        estimated_time_remaining = estimated_total_time - elapsed_time
        st.info(f"Estimated time remaining for {task_name}: {estimated_time_remaining:.2f} seconds")


        # Save processed file
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name=selected_sheet, index=False)
        output.seek(0)

        st.success("Processing complete! Download the file below.")
        st.download_button(label="Download Processed File", data=output, file_name="processed_file.xlsx")
    else:
        st.error("Please upload a valid file.")

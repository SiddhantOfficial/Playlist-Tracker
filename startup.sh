#!/bin/bash

# Install Playwright dependencies
python3 -m playwright install

# Start the Streamlit app
streamlit run app.py --server.port $PORT --server.headless true

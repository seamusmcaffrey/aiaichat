import os
import sys
import time
import random
import logging
from datetime import datetime
import streamlit as st
import openai
from anthropic import Client

# AI Expert Roles for randomization
AI_ROLES = [
    "Code Architecture Expert",
    "Performance Optimization Guru",
    "UX/UI Design Specialist",
    "Systems Integration Expert",
    "Database Design Oracle",
    "Security Implementation Sage",
    "API Design Architect",
    "Testing & QA Mastermind",
    "DevOps Engineering Wizard",
    "Cloud Infrastructure Expert",
    "Mobile Development Specialist",
    "Frontend Framework Guru",
    "Backend Systems Architect",
    "Machine Learning Engineer",
    "Scalability Expert"
]

# Initial demo state
DEMO_CONVERSATION = [
    {"role": "User", "content": "Is a hotdog a sandwich? Please analyze this from a software architecture perspective."},
    {"role": "\U0001f535 GPT-4", "content": """As a Systems Integration Expert, let me analyze this using software design patterns:

If we model a sandwich using Object-Oriented Design, we'd have:
```python
class Sandwich(FoodItem):
    def __init__(self, fillings: List[Ingredient], bread_type: BreadContainer):
        self.fillings = fillings
        self.container = bread_type
```

The hotdog presents an interesting inheritance vs. composition dilemma. While it implements the key sandwich interface (bread containing fillings), its unique cylindrical bread architecture suggests it might be better as a separate microservice... I mean, food category."""},
]

# Set page config FIRST
st.set_page_config(
    page_title="Parrot AI Thinktank",
    page_icon="\U0001f99c",
    layout="wide"
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Version tracking
VERSION = "1.0.1"
LAST_UPDATE = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Demo warning notice
st.error("This is a demo page. Download the code [here](https://github.com/seamusmcaffrey/parrot) and check out the README for instructions on setting it up for use and see [here](https://www.prometheus.ninja/projects/parrot) for a detailed writeup and more information!", icon="\U0001f6a8")

# Move input elements to top
st.write("## Start a Discussion")
user_input = st.text_area("Describe your coding problem:", height=100)
start_button = st.button("\U0001f680 Start AI Discussion")

# Initialize session state
if "showing_demo" not in st.session_state:
    st.session_state.showing_demo = True

if start_button:
    logger.info("Start button pressed - removing demo content")
    st.session_state.showing_demo = False
    
    # Display red warning message
    st.markdown(
        """
        <div style="background-color: #ffcccc; color: #a94442; padding: 15px; border-radius: 5px;">
            <strong>⚠️ Sorry! This is just a visual demo.</strong><br>
            Download the code <a href="https://github.com/seamusmcaffrey/parrot" target="_blank">here</a> and check out the README for instructions on setting it up for use with your own API keys. 
            See <a href="https://www.prometheus.ninja/projects/parrot" target="_blank">here</a> for a detailed writeup and more information!
        </div>
        """,
        unsafe_allow_html=True
    )

# Keep the rest of the functional code intact
if "chat_history" not in st.session_state:
    st.session_state.chat_history = DEMO_CONVERSATION.copy()

st.title("🦜 Parrot AI Thinktank")

# Display demo if we're in demo state
if st.session_state.showing_demo:
    logger.info("Displaying demo conversation")
    st.info("👋 Welcome! Here's a sample discussion to demonstrate how our AI experts analyze problems:", icon="🎯")
    
    for msg in DEMO_CONVERSATION:
        st.markdown(f"**{msg['role']}:** {msg['content']}")

@st.cache_resource
def init_clients():
    """Initialize API clients for all AI models using Streamlit secrets"""
    logger.info("Initializing AI clients")
    claude = None
    openai_client = None
    deepseek_api_key = None
    
    try:
        if "CLAUDE_API_KEY" in st.secrets:
            logger.info("Initializing Claude client")
            claude_api_key = st.secrets["CLAUDE_API_KEY"]
            claude = Client(api_key=claude_api_key)
        
        if "OPENAI_API_KEY" in st.secrets:
            logger.info("Initializing OpenAI client")
            openai_api_key = st.secrets["OPENAI_API_KEY"]
            openai_client = openai.Client(api_key=openai_api_key)
        
        if "DEEPSEEK_API_KEY" in st.secrets:
            logger.info("Getting DeepSeek API key")
            deepseek_api_key = st.secrets["DEEPSEEK_API_KEY"]
        
        return claude, openai_client, deepseek_api_key
    except Exception as e:
        logger.error(f"Error initializing clients: {str(e)}")
        return None, None, None

# Initialize AI clients
claude_client, openai_client, deepseek_api_key = init_clients()

# Display version info
st.sidebar.info(f"Version: {VERSION}\nLast Updated: {LAST_UPDATE}")

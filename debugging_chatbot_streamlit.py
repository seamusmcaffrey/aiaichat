import os
import streamlit as st
import openai
from anthropic import Client
import logging
import time
import random
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add version tracking
VERSION = "1.0.1"
LAST_UPDATE = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Set page config FIRST - before any other Streamlit commands
st.set_page_config(
    page_title="Parrot AI Thinktank",
    page_icon="🦜",
    layout="wide"
)

# Now we can add version info and debug panel to sidebar
st.sidebar.info(f"Version: {VERSION}\nLast Updated: {LAST_UPDATE}")

# Debug Info Section
if st.sidebar.checkbox("Show Debug Info"):
    st.sidebar.text("Debug Information")
    st.sidebar.text(f"Python Version: {sys.version}")
    st.sidebar.text(f"Streamlit Version: {st.__version__}")
    st.sidebar.text(f"Current Working Directory: {os.getcwd()}")

def log_operation(func):
    """Decorator to log function operations"""
    def wrapper(*args, **kwargs):
        logger.info(f"Entering {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logger.info(f"Successfully completed {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            raise
    return wrapper

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
        
        # Log available services
        services = []
        if claude: services.append("Claude")
        if openai_client: services.append("OpenAI")
        if deepseek_api_key: services.append("DeepSeek")
        logger.info(f"Available services: {', '.join(services)}")
        
        return claude, openai_client, deepseek_api_key
    except Exception as e:
        logger.error(f"Error initializing clients: {str(e)}")
        st.error(f"Error initializing AI clients: {str(e)}")
        return None, None, None

@log_operation
def format_code_blocks(text):
    """Format code blocks with proper markdown syntax"""
    logger.info("Starting code block formatting")
    try:
        if not text:
            return text
            
        lines = text.split('\n')
        formatted_lines = []
        in_code_block = False
        
        for i, line in enumerate(lines):
            try:
                if line.strip().startswith('```'):
                    in_code_block = not in_code_block
                    formatted_lines.append(line)
                else:
                    if in_code_block:
                        formatted_lines.append(line)
                    else:
                        formatted_lines.append(line)
            except Exception as e:
                logger.error(f"Error processing line {i}: {str(e)}")
                formatted_lines.append(line)
        
        result = '\n'.join(formatted_lines)
        logger.info("Code block formatting completed")
        return result
    except Exception as e:
        logger.error(f"Error in format_code_blocks: {str(e)}")
        return text

@log_operation
def format_paragraphs(text):
    """Ensure proper paragraph spacing in markdown"""
    logger.info("Starting paragraph formatting")
    try:
        if not text:
            return text
        
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        result = '\n\n'.join(paragraphs)
        logger.info("Paragraph formatting completed")
        return result
    except Exception as e:
        logger.error(f"Error in format_paragraphs: {str(e)}")
        return text

@log_operation
def get_ai_response(prompt, history, model, role):
    """Get a response from the selected AI model with assigned role"""
    logger.info(f"Getting AI response for model: {model}, role: {role}")
    try:
        role_context = f"You are acting as a {role}. "
        
        if model == "claude":
            messages = [
                {"role": "user", "content": f"{role_context}{history}\n\n{prompt}"}
            ]
            response = claude_client.messages.create(
                model="claude-3-5-sonnet-latest",
                max_tokens=1024,
                messages=messages
            )
            content = response.content
            
        elif model == "gpt4":
            messages = [
                {"role": "system", "content": f"You are acting as a {role}."},
                {"role": "user", "content": f"{history}\n\n{prompt}"}
            ]
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=1024,
                temperature=0.7
            )
            content = response.choices[0].message.content
            
        elif model == "deepseek":
            messages = [
                {"role": "system", "content": f"You are acting as a {role}."},
                {"role": "user", "content": f"{history}\n\n{prompt}"}
            ]
            deepseek_client = openai.Client(
                base_url="https://api.deepseek.com/v1",
                api_key=deepseek_api_key,
            )
            response = deepseek_client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
                stream=False
            )
            content = response.choices[0].message.content

        logger.info(f"Successfully got response from {model}")
        formatted_content = format_code_blocks(format_paragraphs(content))
        return formatted_content
    except Exception as e:
        error_msg = f"Error generating response from {model}: {str(e)}"
        logger.error(error_msg)
        return error_msg

# Initialize AI clients
logger.info("Starting client initialization")
claude_client, openai_client, deepseek_api_key = init_clients()

# Model selection with availability checks
st.sidebar.header("Select AI Models for Discussion")
available_models = {
    "claude": claude_client is not None,
    "gpt4": openai_client is not None,
    "deepseek": deepseek_api_key is not None
}

logger.info(f"Available models: {available_models}")

use_claude = st.sidebar.checkbox("Claude", value=True, disabled=not available_models["claude"])
use_gpt4 = st.sidebar.checkbox("GPT-4", value=True, disabled=not available_models["gpt4"])
use_deepseek = st.sidebar.checkbox("DeepSeek", value=False, disabled=not available_models["deepseek"])

# Selected models tracking
selected_models = []
if use_claude and available_models["claude"]:
    selected_models.append(("claude", "🟡 Claude"))
if use_gpt4 and available_models["gpt4"]:
    selected_models.append(("gpt4", "🔵 GPT-4"))
if use_deepseek and available_models["deepseek"]:
    selected_models.append(("deepseek", "🟣 DeepSeek"))

logger.info(f"Selected models: {selected_models}")

if len(selected_models) < 2:
    st.warning("Please select at least two AI models for discussion")
    st.stop()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# File upload and user input
allowed_extensions = ["txt", "py", "json", "md", "ts", "tsx", "yaml", "yml", "csv", "toml", "ini", "html", "css", "js"]
uploaded_file = st.file_uploader("📎 Attach a file for reference (optional)", type=allowed_extensions)
user_input = st.text_area("💡 Describe your coding problem:")

max_rounds = st.slider("🔄 Max AI Discussion Rounds", min_value=1, max_value=10, value=5)

if st.button("🚀 Start AI Discussion"):
    logger.info("Starting new AI discussion")
    if user_input:
        st.session_state.chat_history.append({"role": "User", "content": user_input})
        
        if uploaded_file:
            file_extension = uploaded_file.name.split('.')[-1]
            logger.info(f"Processing uploaded file: {uploaded_file.name}")
            if file_extension in allowed_extensions:
                file_content = uploaded_file.getvalue().decode("utf-8")
                st.session_state.chat_history.append({
                    "role": "System", 
                    "content": f"📄 Attached file content:\n```{file_extension}\n{file_content}\n```"
                })
            else:
                logger.warning(f"Unsupported file type: {file_extension}")
                st.warning("⚠️ Unsupported file type uploaded.")

        conversation_context = "\n\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.chat_history])
        
        # Randomize initial responder order
        random.shuffle(selected_models)
        logger.info(f"Randomized model order: {selected_models}")

        for round_num in range(max_rounds):
            logger.info(f"Starting round {round_num + 1}")
            for model, model_name in selected_models:
                with st.spinner(f"💭 {model_name} is thinking..."):
                    response = get_ai_response(
                        "Analyze the issue and propose a detailed solution." if round_num == 0
                        else f"Consider the previous response and provide your perspective.",
                        conversation_context,
                        model,
                        "Code Expert"
                    )
                    
                    st.session_state.chat_history.append({"role": model_name, "content": response})
                    
                    # Style the response
                    bg_colors = {
                        "🔵 GPT-4": "rgba(0, 122, 255, 0.1)",
                        "🟡 Claude": "rgba(255, 196, 0, 0.1)",
                        "🟣 DeepSeek": "rgba(147, 51, 234, 0.1)"
                    }
                    
                    st.markdown(
                        f"""
                        <div style="
                            background-color: {bg_colors[model_name]};
                            border-radius: 10px;
                            padding: 20px;
                            margin: 10px 0;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        ">
                            <h3>{model_name} (Code Expert)</h3>
                            <div>{response}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                
                time.sleep(1)
            
            logger.info(f"Completed round {round_num + 1}")

logger.info("Script execution completed")
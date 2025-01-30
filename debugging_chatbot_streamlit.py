import os
import streamlit as st
import openai
from anthropic import Client
import logging
import time
import random
import sys
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

def clean_string(text):
    """Clean string of invalid characters and standardize formatting"""
    if not text:
        return text
    # Remove null bytes and other problematic characters
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
    return text

def format_code_blocks(text):
    """Format code blocks with proper markdown syntax"""
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

def format_ai_response(response, is_code=False):
    """Standardize AI response formatting"""
    try:
        # Ensure response is a string
        if isinstance(response, list):
            response = ' '.join(str(item) for item in response)
        response = str(response)
        
        # Pre-process the response to handle common formatting issues
        response = response.replace('\r\n', '\n')  # Normalize line endings
        
        # Add section headers if they don't exist
        if not any(header in response for header in ['Identified Issues', 'Proposed Solutions', 'Conclusion']):
            parts = response.split('\n\n')
            if len(parts) > 2:
                response = "## Analysis\n\n" + response

        # Format sections consistently
        sections = []
        current_section = []
        
        for line in response.split('\n'):
            if line.strip().startswith('#'):
                if current_section:
                    sections.append('\n'.join(current_section))
                    current_section = []
                # Ensure consistent header formatting
                header_text = line.lstrip('#').strip()
                current_section.append(f"\n## {header_text}")
            elif line.strip().startswith(('*', '-', '•')):
                # Format list items consistently
                item_text = line.lstrip('*-• ').strip()
                current_section.append(f"* {item_text}")
            else:
                current_section.append(line)
        
        if current_section:
            sections.append('\n'.join(current_section))
            
        response = '\n\n'.join(sections)
        
        # Ensure code blocks are properly formatted
        if is_code:
            response = format_code_blocks(response)
            
        # Final cleanup
        response = clean_string(response)
        
        # Add spacing after headers and before lists
        response = response.replace('\n##', '\n\n##')
        response = response.replace('\n*', '\n\n*')
        
        return response.strip()
    except Exception as e:
        logger.error(f"Error formatting response: {str(e)}")
        if isinstance(response, (str, list)):
            # Return raw response if formatting fails
            return str(response) if isinstance(response, list) else response
        return "Error formatting response"

def get_chat_context(history, last_response=None):
    """Generate contextual prompt for the next response"""
    if last_response:
        return f"""Previous response: {last_response}

Please review the above response and provide your perspective. Consider:
1. What aspects do you agree or disagree with?
2. What important considerations might have been missed?
3. What alternative approaches could be worth exploring?

Current conversation history:
{history}"""
    return history

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
        
        services = []
        if claude: services.append("Claude")
        if openai_client: services.append("OpenAI")
        if deepseek_api_key: services.append("DeepSeek")
        logger.info(f"Available services: {', '.join(services)}")
        
        return claude, openai_client, deepseek_api_key
    except Exception as e:
        logger.error(f"Error initializing clients: {str(e)}")
        st.warning(f"Some AI services may be unavailable: {str(e)}")
        return None, None, None

def get_ai_response(prompt, history, model, role):
    """Get a response from the selected AI model with assigned role"""
    logger.info(f"Getting AI response for model: {model}, role: {role}")
    try:
        role_context = f"You are acting as a {role}. "
        
        if model == "claude":
            prompt_template = f"""
You are a coding expert analyzing technical issues. Please provide your analysis in a clear, structured format with sections and bullet points.

Context: {role_context}

History: {history}

Task: {prompt}

Please structure your response with:
1. Clear section headers (##)
2. Bulleted lists for key points (*)
3. Code examples in proper code blocks (```)
4. A conclusion section
"""
            messages = [
                {"role": "user", "content": prompt_template}
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
        formatted_content = format_ai_response(content, is_code=True)
        return formatted_content
    except Exception as e:
        error_msg = f"Error generating response from {model}: {str(e)}"
        logger.error(error_msg)
        return error_msg

# Now we can add version info and debug panel to sidebar
st.sidebar.info(f"Version: {VERSION}\nLast Updated: {LAST_UPDATE}")

# Debug Info Section
if st.sidebar.checkbox("Show Debug Info"):
    st.sidebar.text("Debug Information")
    st.sidebar.text(f"Python Version: {sys.version}")
    st.sidebar.text(f"Streamlit Version: {st.__version__}")
    st.sidebar.text(f"Current Working Directory: {os.getcwd()}")

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

st.title("🦜 Parrot AI Thinktank")

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
        
        last_response = None
        for round_num in range(max_rounds):
            logger.info(f"Starting round {round_num + 1}")
            for model, model_name in selected_models:
                with st.spinner(f"💭 {model_name} is thinking..."):
                    # Generate contrarian prompt based on context
                    if round_num == 0:
                        base_prompt = "Analyze the issue and propose a detailed solution, focusing on:"
                        if model == "claude":
                            base_prompt += "\n1. Code architecture and implementation details\n2. Performance implications\n3. Error handling strategies"
                        elif model == "gpt4":
                            base_prompt += "\n1. User experience and interaction flow\n2. Edge cases and potential issues\n3. Testing considerations"
                        else:
                            base_prompt += "\n1. Technical feasibility\n2. Scalability concerns\n3. Integration challenges"
                    else:
                        base_prompt = get_chat_context(conversation_context, last_response)
                    
                    response = get_ai_response(
                        base_prompt,
                        conversation_context,
                        model,
                        "Code Expert"
                    )
                    
                    # Format response and update context
                    formatted_response = format_ai_response(response, is_code=True)
                    last_response = formatted_response
                    
                    st.session_state.chat_history.append({"role": model_name, "content": formatted_response})
                    
                    # Style the response with background color
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
                            <div>{formatted_response}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                
                time.sleep(1)
            
            logger.info(f"Completed round {round_num + 1}")

logger.info("Script execution completed")
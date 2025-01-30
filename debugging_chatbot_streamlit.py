import os
import sys
import time
import random
import logging
from datetime import datetime
import streamlit as st
import openai
from anthropic import Client

# IMPORTANT: st.set_page_config must be the absolute first Streamlit command
st.set_page_config(
    page_title="Parrot AI Thinktank",
    page_icon="🦜",
    layout="wide"
)

# Now we can do other initialization
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VERSION = "1.0.1"
LAST_UPDATE = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Initialize clients
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
        return content
    except Exception as e:
        error_msg = f"Error generating response from {model}: {str(e)}"
        logger.error(error_msg)
        return error_msg

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

# Initial demo state for homepage
DEMO_CONVERSATION = [
    {"role": "User", "content": "Is a hotdog a sandwich? Please analyze this from a software architecture perspective."},
    {"role": "🔵 GPT-4", "content": """As a Systems Integration Expert, let me analyze this using software design patterns:

If we model a sandwich using Object-Oriented Design, we'd have:
```python
class Sandwich(FoodItem):
    def __init__(self, fillings: List[Ingredient], bread_type: BreadContainer):
        self.fillings = fillings
        self.container = bread_type
```

The hotdog presents an interesting inheritance vs. composition dilemma. While it implements the key sandwich interface (bread containing fillings), its unique cylindrical bread architecture suggests it might be better as a separate microservice... I mean, food category."""},
    {"role": "🟡 Claude", "content": """As a Code Architecture Expert, I must respectfully disagree with the proposed inheritance model.

A hotdog clearly violates the Liskov Substitution Principle - you cannot reliably substitute a hotdog in contexts expecting a sandwich without breaking the application's... I mean, diner's expectations. 

The single-seam bread architecture and cylindrical payload structure suggest this is more of a "Food Wrapper" pattern:
```python
class HotDog(WrapperFood):
    def __init__(self, filling: Sausage, bun: CylindricalBun):
        super().__init__(container=bun)
        self.validate_structural_integrity()
```"""},
    {"role": "🔵 GPT-4", "content": """Your point about LSP is well-taken, but perhaps we're approaching this too rigidly. What about a Decorator pattern?

A hotdog could be viewed as a runtime decoration of a base sausage component, with the bun acting as a stateless wrapper... Though I admit this architecture falls apart under load (literally, if the bun isn't properly reinforced)."""},
    {"role": "Consensus", "content": """After careful technical analysis, we've reached consensus that a hotdog implements a unique architectural pattern distinct from traditional sandwich design principles.

Key findings:
1. Violates standard sandwich interface expectations
2. Implements a specialized wrapper pattern
3. Has unique structural integrity requirements
4. Cannot be safely substituted in sandwich contexts

Recommendation: Classify hotdog as its own microservice in the food hierarchy. Further investigation needed for edge cases like subway sandwiches which share the single-seam architecture.

In conclusion: A hotdog is not a sandwich - it's a deployment configuration."""}
]

# Initialize AI clients
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
    # Clear demo state and start new discussion
    st.session_state.showing_demo = False
    st.session_state.chat_history = []
    
    if user_input:
        logger.info("Starting new AI discussion")
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
        
        # Randomize initial responder order and assign random roles
        random.shuffle(selected_models)
        model_roles = {model: random.choice(AI_ROLES) for model, _ in selected_models}
        logger.info(f"Randomized model order: {selected_models}")
        logger.info(f"Assigned roles: {model_roles}")
        
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
                        base_prompt = f"""Previous response: {last_response}

Please review the above response and provide your perspective. Consider:
1. What aspects do you agree or disagree with?
2. What important considerations might have been missed?
3. What alternative approaches could be worth exploring?

Current conversation history:
{conversation_context}"""
                    
                    response = get_ai_response(
                        base_prompt,
                        conversation_context,
                        model,
                        model_roles[model]
                    )
                    
                    last_response = response
                    st.session_state.chat_history.append({"role": model_name, "content": response})
                    
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
                            <div>{response}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                
                time.sleep(1)
            
            logger.info(f"Completed round {round_num + 1}")

        # Generate and display final consensus
        st.markdown("### ✅ Final Consensus")
        consensus_prompt = """Please provide a clear consensus summary that:
1. Synthesizes the key agreements between participants
2. Highlights the best solutions agreed upon
3. Provides concrete next steps for implementation
4. Addresses any remaining concerns"""
        
        consensus = get_ai_response(consensus_prompt, conversation_context, "gpt4", "Consensus Builder")
        st.session_state.chat_history.append({"role": "Consensus", "content": consensus})
        
        consensus_container = st.container()
        with consensus_container:
            st.markdown(
                f"""
                <div style="
                    background-color: rgba(0, 200, 0, 0.1);
                    border-radius: 10px;
                    padding: 20px;
                    margin: 10px 0;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                ">
                    <div>{consensus}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
        if st.button("📋 Copy Consensus"):
            st.write(
                f"""
                <script>
                    navigator.clipboard.writeText(`{consensus}`);
                </script>
                """,
                unsafe_allow_html=True
            )

logger.info("Script execution completed")
import os
import streamlit as st
import openai
from anthropic import Client
import logging
import time
import random
import json

# Configure logging
logging.getLogger().setLevel(logging.WARNING)

# AI Roles for randomization
AI_ROLES = [
    "Code Architecture Expert",
    "Performance Optimization Specialist",
    "Security Implementation Expert",
    "Database Design Specialist",
    "UI/UX Implementation Expert",
    "System Integration Specialist",
    "Testing & Quality Assurance Expert",
    "DevOps Implementation Specialist",
    "API Design Expert",
    "Scalability Architect"
]

# Contrarian prompts for dynamic discussion
CONTRARIAN_PROMPTS = [
    "While that approach could work, have we considered the implications of {}? I would suggest...",
    "I see the merit in that solution, but what about {} as an alternative approach?",
    "That's an interesting perspective, though I wonder if {} might be more effective...",
    "I understand your reasoning, but have you considered the impact of {} on the system?",
    "While I agree with the overall direction, I think {} might be worth exploring...",
    "That's a solid approach, though we might want to consider {} as well...",
]

# Set page title and favicon
st.set_page_config(
    page_title="Parrot AI Thinktank",
    page_icon="🦜",
    layout="wide"
)

@st.cache_resource
def init_clients():
    """Initialize API clients for all AI models using Streamlit secrets"""
    try:
        claude_api_key = st.secrets["CLAUDE_API_KEY"]
        openai_api_key = st.secrets["OPENAI_API_KEY"]
        deepseek_api_key = st.secrets["DEEPSEEK_API_KEY"]
        
        claude = Client(api_key=claude_api_key)
        openai_client = openai.Client(api_key=openai_api_key)
        
        return claude, openai_client, deepseek_api_key
    except Exception as e:
        st.error(f"Error initializing AI clients: {str(e)}")
        return None, None, None

def get_ai_response(prompt, history, model, role):
    """Get a response from the selected AI model with assigned role"""
    try:
        role_context = f"You are acting as a {role}. "
        
        # Format system and user messages
        messages = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": f"{role_context}{history}\n\n{prompt}"}
        ]
        
        if model == "claude":
            response = claude_client.messages.create(
                model="claude-3-5-sonnet-latest",
                max_tokens=1024,
                messages=messages
            )
            content = response.content
        elif model == "gpt4":
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=1024
            )
            content = response.choices[0].message.content
        elif model == "deepseek":
            # Create OpenAI client configured for DeepSeek
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
        
        return format_code_blocks(format_paragraphs(content))
    except Exception as e:
        return f"Error generating response: {str(e)}"

def copy_to_clipboard(text):
    """Create a JavaScript function to copy text to clipboard"""
    js_code = f"""
        navigator.clipboard.writeText('{text}').then(function() {{
            console.log('Text copied');
        }})
        .catch(function(error) {{
            console.error('Error copying text:', error);
        }});
    """
    st.components.v1.html(f"""
        <button onclick="{js_code}">Copy Consensus</button>
    """, height=50)

st.title("🦜 Parrot AI Thinktank")

# Initialize AI clients
claude_client, openai_client, deepseek_api_key = init_clients()

# Configure OpenAI client for DeepSeek compatibility
if deepseek_api_key:
    openai.api_base = "https://api.deepseek.com/v1"

# Model selection
st.sidebar.header("Select AI Models for Discussion")
use_claude = st.sidebar.checkbox("Claude", value=True)
use_gpt4 = st.sidebar.checkbox("GPT-4", value=True)
use_deepseek = st.sidebar.checkbox("DeepSeek", value=False)

# Ensure at least two models are selected
selected_models = []
if use_claude:
    selected_models.append(("claude", "🟡 Claude"))
if use_gpt4:
    selected_models.append(("gpt4", "🔵 GPT-4"))
if use_deepseek:
    selected_models.append(("deepseek", "🟣 DeepSeek"))

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
    if user_input:
        st.session_state.chat_history.append({"role": "User", "content": user_input})
        
        # Handle file upload
        if uploaded_file:
            file_extension = uploaded_file.name.split('.')[-1]
            if file_extension in allowed_extensions:
                file_content = uploaded_file.getvalue().decode("utf-8")
                st.session_state.chat_history.append({"role": "System", "content": f"📄 Attached file content:\n```{file_extension}\n{file_content}\n```"})
            else:
                st.warning("⚠️ Unsupported file type uploaded.")

        conversation_context = "\n\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.chat_history])

        # Randomize initial responder and roles
        random.shuffle(selected_models)
        current_roles = random.sample(AI_ROLES, len(selected_models))
        model_roles = dict(zip(selected_models, current_roles))

        for round_num in range(max_rounds):
            for i, (model, model_name) in enumerate(selected_models):
                role = model_roles[(model, model_name)]
                
                with st.spinner(f"💭 Round {round_num+1}: {model_name} ({role}) is thinking..."):
                    # Generate contrarian prompt for subsequent responses
                    if i == 0:
                        prompt = "Analyze the issue and propose a detailed solution."
                    else:
                        previous_response = st.session_state.chat_history[-1]["content"]
                        contrarian_topic = random.choice([
                            "scalability", "security", "maintainability", 
                            "performance", "error handling", "edge cases"
                        ])
                        prompt = random.choice(CONTRARIAN_PROMPTS).format(contrarian_topic)
                        prompt += f"\n\nPrevious response: {previous_response}"
                    
                    response = get_ai_response(prompt, conversation_context, model, role)
                    st.session_state.chat_history.append({"role": model_name, "content": response})
                    st.markdown(f"""### {model_name} ({role})\n\n{response}""")
                
                time.sleep(1)
            
            # Check for consensus
            consensus_prompt = "Based on the discussion, is there a clear best approach? Answer YES or NO and briefly explain why."
            consensus_check = get_ai_response(consensus_prompt, conversation_context, "gpt4", "Consensus Evaluator")
            
            if "YES" in consensus_check.upper():
                break

        # Generate actionable consensus
        final_prompt = """
        Based on the discussion, provide a clear, actionable consensus that includes:
        1. The specific solution agreed upon
        2. Key implementation steps
        3. Any important considerations or caveats
        
        Focus on the concrete solution rather than summarizing the discussion.
        """
        final_consensus = get_ai_response(final_prompt, conversation_context, "claude", "Solution Architect")
        st.session_state.chat_history.append({"role": "Consensus", "content": final_consensus})
        
        st.markdown("### ✅ Final Consensus")
        st.markdown(final_consensus)
        
        # Add copy consensus button
        st.button("📋 Copy Consensus", on_click=lambda: st.write(copy_to_clipboard(final_consensus)))

# Download chat history
st.download_button(
    "📥 Download Chat History",
    data="\n\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.chat_history]),
    file_name="debug_chat_history.txt",
    mime="text/plain"
)
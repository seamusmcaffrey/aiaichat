import os
import streamlit as st
import openai
from anthropic import Client
import logging
import time

# Configure logging
logging.getLogger().setLevel(logging.WARNING)

@st.cache_resource
def init_clients():
    """Initialize API clients for Claude and ChatGPT using Streamlit secrets"""
    try:
        claude_api_key = st.secrets["CLAUDE_API_KEY"]
        openai_api_key = st.secrets["OPENAI_API_KEY"]
        
        claude = Client(api_key=claude_api_key)
        openai_client = openai.Client(api_key=openai_api_key)
        
        return claude, openai_client
    except Exception as e:
        st.error(f"Error initializing AI clients: {str(e)}")
        return None, None

def get_ai_response(prompt, history, model):
    """Get a response from the selected AI model with structured conversation flow"""
    try:
        if model == "claude":
            response = claude_client.messages.create(
                model="claude-3-5-sonnet-latest",
                max_tokens=1024,
                messages=[{"role": "user", "content": f"{history}\n\n{prompt}"}]
            )
            return response.content
        else:
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": f"{history}\n\n{prompt}"}],
                max_tokens=1024
            )
            return response.choices[0].message.content
    except Exception as e:
        return f"Error generating response: {str(e)}"

st.title("🤖 AI Debugging Chatbot: Conversational Mode")

claude_client, openai_client = init_clients()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

uploaded_file = st.file_uploader("📎 Attach a file for reference (optional)", type=["txt", "py", "json", "md"])
user_input = st.text_area("💡 Describe your coding problem:")

max_rounds = st.slider("🔄 Max AI Discussion Rounds", min_value=1, max_value=10, value=5)

if st.button("🚀 Start AI Discussion"):
    if user_input:
        st.session_state.chat_history.append({"role": "User", "content": user_input})

        file_content = ""
        if uploaded_file:
            file_content = uploaded_file.getvalue().decode("utf-8")
            st.session_state.chat_history.append({"role": "System", "content": f"📄 Attached file content: {file_content}"})

        conversation_context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.chat_history])

        for round_num in range(max_rounds):
            with st.spinner(f"🧠 Round {round_num+1}: Claude is brainstorming..."):
                claude_prompt = "Given the problem below, analyze it and propose 2-3 possible solutions, listing both pros and cons. Format the response as a markdown-formatted debate."
                claude_response = get_ai_response(claude_prompt, conversation_context, model="claude")
                st.session_state.chat_history.append({"role": "Claude", "content": claude_response})
                st.markdown(f"""### 🟡 Claude\n\n{claude_response}""", unsafe_allow_html=True)

            time.sleep(1)

            with st.spinner(f"💡 Round {round_num+1}: ChatGPT is refining the approach..."):
                chatgpt_prompt = "Claude has suggested the following solutions. Evaluate these critically, highlight potential weaknesses or missing considerations, and propose refinements or alternatives."
                chatgpt_response = get_ai_response(chatgpt_prompt, conversation_context, model="gpt-4o")
                st.session_state.chat_history.append({"role": "ChatGPT", "content": chatgpt_response})
                st.markdown(f"""### 🔵 ChatGPT\n\n{chatgpt_response}""", unsafe_allow_html=True)

            time.sleep(1)

            consensus_prompt = "ChatGPT has critiqued your solutions and proposed modifications. Do you agree or disagree? Justify your response. If you agree, refine your original proposal to reflect the most effective plan."
            claude_followup = get_ai_response(consensus_prompt, conversation_context, model="claude")
            st.session_state.chat_history.append({"role": "Claude Follow-up", "content": claude_followup})
            st.markdown(f"""### 🟡 Claude Follow-up\n\n{claude_followup}""", unsafe_allow_html=True)

            final_prompt = "Summarize the entire discussion and arrive at a consensus solution that synthesizes the best parts of both viewpoints."
            final_consensus = get_ai_response(final_prompt, conversation_context, model="gpt-4o")
            st.session_state.chat_history.append({"role": "Consensus", "content": final_consensus})
            st.markdown(f"""### ✅ Final Consensus\n\n{final_consensus}""", unsafe_allow_html=True)
            break

st.download_button("📥 Download Chat History", data="\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.chat_history]), file_name="debug_chat_history.txt", mime="text/plain")

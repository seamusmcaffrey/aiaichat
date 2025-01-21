import os
import streamlit as st
import openai
from anthropic import Client
import logging
import time
import mimetypes

# Configure logging
logging.getLogger().setLevel(logging.INFO)

# Set a custom favicon and title
st.set_page_config(
    page_title="🦜Parrot AI Thinktank",
    page_icon="🦜"
)

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

st.title("🦜Parrot AI Thinktank")

claude_client, openai_client = init_clients()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Allow more file types explicitly
allowed_extensions = ["txt", "py", "json", "md", "ts", "tsx", "yaml", "yml", "csv", "toml", "ini", "html", "css", "js"]

uploaded_file = st.file_uploader("📎 Attach a file for reference (optional)", type=None)  # Remove MIME filtering

user_input = st.text_area("💡 Describe your coding problem:")

max_rounds = st.slider("🔄 Max AI Discussion Rounds", min_value=1, max_value=10, value=5)

if uploaded_file:
    # Extract file extension
    file_extension = uploaded_file.name.split('.')[-1].lower()
    detected_mime = mimetypes.guess_type(uploaded_file.name)[0]

    st.write(f"📂 **Debug Log:**")
    st.write(f"🔹 **Uploaded File Name:** `{uploaded_file.name}`")
    st.write(f"🔹 **Detected MIME Type:** `{detected_mime}`")
    st.write(f"🔹 **Extracted Extension:** `{file_extension}`")

    # If the MIME type is incorrect for TypeScript, manually override it
    if detected_mime == "video/mp2t" and file_extension in ["ts", "tsx"]:
        detected_mime = "text/typescript"
        st.write(f"⚠️ **Manually corrected MIME type to:** `{detected_mime}`")

    # Proceed if the extension is allowed
    if file_extension in allowed_extensions or detected_mime.startswith("text"):
        try:
            file_content = uploaded_file.getvalue().decode("utf-8")
            st.session_state.chat_history.append({"role": "System", "content": f"📄 Attached file content: {file_content}"})
            st.success("✅ File processed successfully!")
        except UnicodeDecodeError:
            st.error("🚫 Unable to process this file. Ensure it's a valid text-based file.")
    else:
        st.error(f"⚠️ Unsupported file type: `{file_extension}` with MIME `{detected_mime}`. Only text-based files are allowed.")

if st.button("🚀 Start AI Discussion"):
    if user_input:
        st.session_state.chat_history.append({"role": "User", "content": user_input})

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
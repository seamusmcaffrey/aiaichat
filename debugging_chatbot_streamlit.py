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
        openai.api_key = openai_api_key
        
        return claude, openai
    except Exception as e:
        st.error(f"Error initializing AI clients: {str(e)}")
        return None, None
def get_ai_response(prompt, context, model):
    """Get a response from the selected AI model"""
    try:
        if model == "claude":
            response = claude_client.messages.create(
                model="claude-3-5-sonnet",
                messages=[{"role": "user", "content": f"{context}\n\n{prompt}"}]
            )
            return response.content
        else:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": f"{context}\n\n{prompt}"}]
            )
            return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error generating response: {str(e)}"

st.title("AI Debugging Chatbot: Live Discussion")

claude_client, openai_client = init_clients()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

uploaded_file = st.file_uploader("Attach a file for reference (optional)", type=["txt", "py", "json", "md"])
user_input = st.text_area("Describe your coding problem:")

max_rounds = st.slider("Max AI Discussion Rounds", min_value=1, max_value=10, value=5)

if st.button("Start AI Discussion"):
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        # File content inclusion if uploaded
        file_content = ""
        if uploaded_file:
            file_content = uploaded_file.getvalue().decode("utf-8")
            st.session_state.chat_history.append({"role": "system", "content": f"Attached file content: {file_content}"})

        conversation_context = "\n".join([msg["content"] for msg in st.session_state.chat_history])

        # AI agent discussion loop
        for round_num in range(max_rounds):
            with st.spinner(f"Round {round_num+1}: Claude is thinking..."):
                claude_response = get_ai_response(user_input, conversation_context, model="claude")
                st.session_state.chat_history.append({"role": "Claude", "content": claude_response})
                st.write(f"**Claude:** {claude_response}")

            time.sleep(1)  # Simulating a delay for better readability

            with st.spinner(f"Round {round_num+1}: ChatGPT is thinking..."):
                chatgpt_response = get_ai_response(claude_response, conversation_context, model="gpt-4")
                st.session_state.chat_history.append({"role": "ChatGPT", "content": chatgpt_response})
                st.write(f"**ChatGPT:** {chatgpt_response}")

            time.sleep(1)

            # Consensus Check
            consensus_prompt = "Based on the conversation so far, is there a clear best solution? Respond only with 'YES' or 'NO'."
            consensus_check = get_ai_response(consensus_prompt, conversation_context, model="gpt-4")

            if "YES" in consensus_check.upper():
                break  # Stop early if consensus is reached

        # Generate final consensus solution
        final_consensus_prompt = "Summarize the best approach based on the AI discussion so far."
        final_consensus = get_ai_response(final_consensus_prompt, conversation_context, model="gpt-4")
        st.session_state.chat_history.append({"role": "Consensus", "content": final_consensus})
        st.success("Consensus reached!")
        st.write(f"**Final Consensus:** {final_consensus}")

st.download_button("Download Chat History", data="\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.chat_history]), file_name="debug_chat_history.txt", mime="text/plain")

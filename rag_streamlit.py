import os
import json
from datetime import datetime
import streamlit as st
import voyageai
from pinecone import Pinecone
from anthropic import Client
import logging

# Configure minimal logging
logging.getLogger().setLevel(logging.WARNING)
for log_name in ['streamlit', 'watchdog.observers.inotify_buffer']:
    logging.getLogger(log_name).setLevel(logging.WARNING)

@st.cache_resource
def init_clients():
    """Initialize API clients with error handling"""
    try:
        claude = Client(api_key=os.getenv("CLAUDE_API_KEY"))
        voyage = voyageai.Client(api_key=os.getenv("VOYAGE_API_KEY"))
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"), environment=os.getenv("PINECONE_ENV"))
        index = pc.Index("rag-index")
        return claude, voyage, index
    except Exception as e:
        st.error(f"Error initializing clients: {str(e)}")
        return None, None, None

@st.cache_data(ttl="1h")
def get_rag_context(query, _voyage_client, _pinecone_index):
    """Get relevant context from RAG system"""
    try:
        embedding = _voyage_client.embed([query], model="voyage-3", input_type="query").embeddings[0]
        results = _pinecone_index.query(vector=embedding, top_k=3, include_metadata=True)
        return "\n\n".join([match["metadata"].get("content", "") for match in results["matches"]])
    except Exception as e:
        st.error(f"Error retrieving context: {str(e)}")
        return ""

def get_assistant_response(prompt, context, claude_client, message_history):
    """Get response from Claude with conversation history"""
    try:
        messages = []
        for msg in message_history:
            if msg["role"] != "system":
                messages.append({"role": msg["role"], "content": msg["content"]})
        
        messages.append({
            "role": "user",
            "content": f"{context}\n\nUser: {prompt}" if context else prompt
        })
        
        response = claude_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1500,
            messages=messages,
            system="You are an expert coder specialized in the boardgame.io library with extensive node.js and typescript knowledge. Remember to keep track of the conversation context and refer back to previous discussion when relevant for problem solving."
        )
        
        # Clean response content
        content = response.content
        if isinstance(content, str):
            content = content.strip(' \'"')  # Remove quotes and spaces
        return content
    except Exception as e:
        return f"I apologize, but I encountered an error: {str(e)}"

def clean_response(response):
    """Clean response text by removing artifacts and formatting properly"""
    if isinstance(response, str):
        # Remove TextBlock artifacts
        if response.startswith('[TextBlock(text="'):
            response = response[16:-15]
        if response.startswith('[TextBlock(text='):
            response = response[15:-14]
            
        # Clean up artifacts and quotes
        response = response.replace('\\"', '"').replace('\\n', '\n')
        response = response.replace('", type=\'text\')', '')
        response = response.replace('", type="text")', '')
        response = response.strip(' \'"')  # Remove quotes and spaces
        
        return response
    return str(response)

def format_response(response):
    """Format the response for display, handling code blocks properly"""
    response = clean_response(response)
    
    if "```" in response:
        parts = response.split("```")
        for i, part in enumerate(parts):
            if i % 2 == 0:  # Regular text
                if part.strip():
                    st.markdown(part.strip())
            else:  # Code block
                # Parse language if specified
                code_lines = part.strip().split('\n')
                if code_lines and code_lines[0] in ['python', 'javascript', 'typescript', 'html', 'css', 'json']:
                    language = code_lines[0]
                    code = '\n'.join(code_lines[1:])
                else:
                    language = ''
                    code = part
                
                # Display code with copy button
                st.code(code.strip(), language=language)
    else:
        st.markdown(response)

def summarize_conversation(claude_client, conversation_history):
    """Generate a summary of the conversation"""
    try:
        summary_prompt = {
            "role": "user",
            "content": """As an AI specialized in boardgame.io, analyze this conversation and extract knowledge that would be valuable for future interactions. Focus on:

1. New Knowledge Gained:
   - What specific technical details about boardgame.io were discussed?
   - What user implementation patterns or use cases were revealed?
   - What common integration scenarios were uncovered?

2. Context Improvements:
   - What additional context would have made your responses more accurate?
   - Which parts of the documentation were most relevant?
   - What related technologies were discussed that need better integration understanding?

3. User Interaction Patterns:
   - How did users phrase their technical questions?
   - What assumptions did users make about boardgame.io?
   - What level of technical detail was most effective in responses?

4. Knowledge Gaps Identified:
   - What questions were you uncertain about?
   - Which features needed more detailed explanation?
   - What related technologies need better coverage?

Format this as structured, actionable knowledge that could be used to improve future responses. Focus on specific, technical details rather than general summaries."""
        }

        messages = [
            {"role": "system", "content": "You are analyzing a conversation about boardgame.io to improve future responses."},
            *[{"role": msg["role"], "content": msg["content"]} for msg in conversation_history],
            summary_prompt
        ]

        response = claude_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            messages=messages
        )
        
        return clean_response(response.content)
    except Exception as e:
        return f"Error generating summary: {str(e)}"

def init_session_state():
    """Initialize all session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    if "summaries" not in st.session_state:
        st.session_state.summaries = []

def create_download_files():
    """Create and offer download buttons for conversation data"""
    if len(st.session_state.messages) > 0:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Prepare conversation markdown
        conversation_md = "# Conversation History\n\n"
        for msg in st.session_state.messages:
            conversation_md += f"## {msg['role'].title()}\n"
            conversation_md += f"{msg['content']}\n\n"
        
        # Get and prepare summary
        summary = summarize_conversation(st.session_state.claude, st.session_state.messages)
        summary_md = "# Conversation Summary\n\n" + summary
        
        # Prepare combined markdown
        combined_md = f"{conversation_md}\n\n{summary_md}"
        
        # Extract structured learnings for training
        learning_prompt = {
            "role": "user",
            "content": """Convert the above analysis into structured training data by identifying:
1. Specific code patterns and implementations discussed
2. Technical terms and their contextual usage
3. Common user questions and effective response patterns
4. Areas where documentation enhancement would help
5. Integration points with other technologies

Format as clear, structured JSON that could be used for training. Include specific examples and contexts."""
        }

        learning_response = claude_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            messages=[
                {"role": "system", "content": "You are extracting structured training data from a boardgame.io conversation."},
                *[{"role": msg["role"], "content": msg["content"]} for msg in st.session_state.messages],
                learning_prompt
            ]
        )

        try:
            structured_learnings = json.loads(clean_response(learning_response.content))
        except json.JSONDecodeError:
            structured_learnings = {"error": "Could not parse structured learnings"}

        # Create JSON structure for potential training data
        training_data = {
            "timestamp": timestamp,
            "conversation": st.session_state.messages,
            "summary": summary,
            "structured_learnings": structured_learnings,
            "metadata": {
                "total_messages": len(st.session_state.messages),
                "total_user_queries": len([m for m in st.session_state.messages if m["role"] == "user"]),
                "topics_covered": [],  # To be filled by analysis
                "learning_effectiveness": None  # Could be filled by additional analysis
            }
        }
        
        # Create download buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.download_button(
                "Download Conversation",
                conversation_md,
                f"conversation_{timestamp}.md",
                "text/markdown"
            )
        
        with col2:
            st.download_button(
                "Download Summary",
                summary_md,
                f"summary_{timestamp}.md",
                "text/markdown"
            )
        
        with col3:
            st.download_button(
                "Download Training Data",
                json.dumps(training_data, indent=2),
                f"training_{timestamp}.json",
                "application/json"
            )
        
        # Store in session state
        st.session_state.conversation_history.append({
            "timestamp": timestamp,
            "conversation": conversation_md,
            "summary": summary_md,
            "training_data": training_data
        })
        
        return summary
    return None

def main():
    st.set_page_config(page_title="RAG-Assisted Claude Chat", layout="wide")
    
    # Initialize session state
    init_session_state()
    
    # Initialize clients (cached)
    claude, voyage, index = init_clients()
    if not all([claude, voyage, index]):
        return
    
    # Store Claude client in session state for summary generation
    st.session_state.claude = claude
    
    st.title("RAG-Assisted Claude Chat")
    st.markdown("A conversational AI powered by RAG-assisted Claude, specialized in boardgame.io")
    
    # Add sidebar controls
    with st.sidebar:
        st.header("Conversation Tools")
        if st.button("Generate Summary & Downloads"):
            summary = create_download_files()
            if summary:
                st.markdown("### Latest Summary")
                st.markdown(summary)
        
        if len(st.session_state.conversation_history) > 0:
            st.header("Previous Conversations")
            for i, conv in enumerate(st.session_state.conversation_history):
                with st.expander(f"Conversation {conv['timestamp']}"):
                    st.markdown(conv['summary'])
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            format_response(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me anything about boardgame.io..."):
        # Add user message
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Get assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                context = get_rag_context(prompt, voyage, index)
                response = get_assistant_response(
                    prompt, 
                    context, 
                    claude, 
                    st.session_state.messages[-10:]
                )
                
                response = clean_response(response)
                format_response(response)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response,
                    "context": context
                })

if __name__ == "__main__":
    main()
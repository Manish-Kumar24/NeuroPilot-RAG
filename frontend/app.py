import streamlit as st
import requests
from typing import Dict, Any, List

# Configure the page
st.set_page_config(
    page_title="NeuroPilot - LangGraph Chatbot Agent",
    page_icon="🤖",
    layout="wide"
)

# Add custom CSS
st.markdown("""
<style>
    .stApp {
        max-width: 1000px;
        margin: 0 auto;
    }
    .user-message {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    .assistant-message {
        background-color: #ffffff;
        border-left: 3px solid #0066cc;
        padding: 1rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Constants
API_URL = "http://127.0.0.1:8000/chat"
MODEL_NAMES = [
    "llama3-70b-8192",
    "mixtral-8x7b-32768"
]

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

def send_message(message: str, model: str, system_prompt: str) -> Dict[str, Any]:
    """Send message to backend API"""
    try:
        response = requests.post(
            API_URL,
            json={
                "messages": [message],
                "model_name": model,
                "system_prompt": system_prompt
            }
        )
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to connect to the server: {str(e)}")
        return None

def main():
    st.title("🤖 LangGraph Chatbot Agent")
    st.markdown("Interact with the LangGraph-based agent using this interface.")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("Define your AI Agent")
        
        model_name = st.selectbox(
            "Select Model",
            MODEL_NAMES,
            index=0
        )
        
        system_prompt = st.text_area(
            "System Prompt",
            value="You are a helpful AI assistant. Provide detailed and accurate responses.",
            height=100
        )
        
        if st.button("Clear Chat History"):
            st.session_state.messages = []
            st.rerun()
    
    # Chat interface
    chat_container = st.container()
    
    # Display chat history
    with chat_container:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f"""<div class="user-message">
                    <b>You:</b><br>{msg["content"]}
                    </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""<div class="assistant-message">
                    <b>Assistant:</b><br>{msg["content"]}
                    </div>""", unsafe_allow_html=True)
    
    # User input
    user_input = st.text_area("Enter your message:", height=100)
    
    # Submit button
    if st.button("Submit"):
        if not user_input.strip():
            st.warning("Please enter a message.")
            return
        
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Get response with loading indicator
        with st.spinner("Thinking..."):
            response = send_message(user_input, model_name, system_prompt)
            
        if response and "messages" in response:
            # Add assistant response to history
            assistant_message = response["messages"][0]["content"]
            st.session_state.messages.append({"role": "assistant", "content": assistant_message})
            st.rerun()
        elif response and "error" in response:
            st.error(response["error"])
        else:
            st.error("Failed to get a response. Please try again.")

if __name__ == "__main__":
    main()
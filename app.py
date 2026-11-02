import streamlit as st
from google import genai
from google.genai import types

# Page Title
st.title("🤖 Customer Support Assistant")

# Fetch API key securely from Streamlit secrets
api_key = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=api_key)

# Read Knowledge Base
@st.cache_data
def load_knowledge():
    with open("knowledge.txt", "r", encoding="utf-8") as f:
        return f.read()

knowledge_text = load_knowledge()

system_instruction = f"""
You are a helpful customer support chatbot. 
Answer user questions based on the provided knowledge base below.

--- KNOWLEDGE BASE ---
{knowledge_text}
--- END KNOWLEDGE BASE ---
"""

# Store chat history in web session
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Chat Input
if prompt := st.chat_input("Ask a question..."):
    # Display user input in UI
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response from Gemini
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=0.3,
    )

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        # Safely attempt to generate and stream content
        try:
            response = client.models.generate_content_stream(
                model="gemini-3.5-flash",
                contents=prompt,
                config=config,
            )

            # Stream response directly to browser
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌")
                
            # If output was stopped/filtered before text generated
            if not full_response:
                full_response = "I was unable to process that specific request. Please try rephrasing your question."

            message_placeholder.markdown(full_response)

        except Exception as e:
            # Friendly fallback message when API or network errors occur
            full_response = "I am experiencing temporary connection issues. Please try sending your message again in a moment."
            message_placeholder.markdown(full_response)

    # Save assistant message to history
    st.session_state.messages.append({"role": "assistant", "content": full_response})
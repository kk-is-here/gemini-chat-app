import streamlit as st
from google import genai
from google.genai import types
from github import Github

# Page Configuration & Title
st.set_page_config(page_title="Customer Support & Admin", layout="wide")
st.title("🤖 Customer Support Assistant")

# Fetch API key securely from Streamlit secrets
api_key = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=api_key)

# Hide Streamlit header and main menu
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Function to update GitHub repo (Defined at top-level)
def update_github_knowledge(new_content: str):
    """Updates knowledge.txt directly in the GitHub repository."""
    g = Github(st.secrets["GITHUB_TOKEN"])
    repo = g.get_repo(st.secrets["REPO_NAME"])
    
    file_path = "knowledge.txt"
    contents = repo.get_contents(file_path, ref="main")
    
    repo.update_file(
        path=contents.path,
        message="Update knowledge.txt via Streamlit Admin Panel",
        content=new_content,
        sha=contents.sha,
        branch="main"
    )

# Read Knowledge Base
@st.cache_data
def load_knowledge():
    with open("knowledge.txt", "r", encoding="utf-8") as f:
        return f.read()

knowledge_text = load_knowledge()

system_instruction = f"""
You are a helpful customer support chatbot for IIT Guwahati School of Business. 
Answer user questions based on the provided knowledge base below.

--- KNOWLEDGE BASE ---
{knowledge_text}
--- END KNOWLEDGE BASE ---
"""

# --- Admin Sidebar Section ---
st.sidebar.title("⚙️ Admin Dashboard")
if st.sidebar.checkbox("Manage Knowledge Base"):
    st.sidebar.markdown("---")
    st.header("📝 Knowledge Base Manager")
    
    # Read current local knowledge.txt
    current_knowledge = load_knowledge()

    updated_text = st.text_area(
        "Edit Bot Knowledge Base (updates both Chatbot & Voice Bot):",
        value=current_knowledge,
        height=350
    )

    if st.button("Save & Deploy to GitHub"):
        try:
            update_github_knowledge(updated_text)
            st.cache_data.clear()  # Clear cache so new text is loaded immediately
            st.success("Successfully updated knowledge.txt on GitHub! Render & Streamlit will auto-redeploy.")
        except Exception as e:
            st.error(f"Failed to update GitHub: {e}")

# --- Customer Support Chat Interface ---
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

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=0.3,
    )

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        try:
            response = client.models.generate_content_stream(
                model="gemini-3.5-flash",
                contents=prompt,
                config=config,
            )

            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌")
                
            if not full_response:
                full_response = "I was unable to process that specific request. Please try rephrasing your question."

            message_placeholder.markdown(full_response)

        except Exception as e:
            full_response = "I am experiencing temporary connection issues. Please try sending your message again in a moment."
            message_placeholder.markdown(full_response)

    # Save assistant message to history
    st.session_state.messages.append({"role": "assistant", "content": full_response})

# Inject custom CSS to hide Streamlit header and internal menu
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
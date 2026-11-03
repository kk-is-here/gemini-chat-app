import requests
import streamlit as st
from github import Github
from google import genai
from google.genai import types

# --- Page Configuration & Title ---
st.set_page_config(
    page_title="IIT Guwahati School of Business - AI Assistant",
    page_icon="🎓",
    layout="wide"
)

# --- UI Customization (Hide Standard Streamlit Chrome) ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp {
        margin-top: -30px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🎓 IIT Guwahati School of Business")
st.caption("AI Executive Workshop Assistant")

# --- Initialize Gemini Client ---
api_key = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=api_key)

# --- Helper Functions ---
@st.cache_data
def load_knowledge():
    """Reads the knowledge base file locally."""
    try:
        with open("knowledge.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Knowledge base file not found."

def update_github_knowledge(new_content: str):
    """Updates knowledge.txt directly in the GitHub repository via PyGithub."""
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

# Load Knowledge Text
knowledge_text = load_knowledge()

system_instruction = f"""
You are an official AI Assistant for the IIT Guwahati School of Business. 
Answer user inquiries regarding the Executive AI Workshops, curriculum, registration, and schedules strictly using the provided knowledge base.
Be concise, professional, and helpful.

--- KNOWLEDGE BASE ---
{knowledge_text}
--- END KNOWLEDGE BASE ---
"""

# --- Sidebar Admin Dashboard ---
st.sidebar.title("⚙️ Admin Control Panel")
if st.sidebar.checkbox("Open Admin Dashboard"):
    st.sidebar.markdown("---")
    
    # Tab 1: Knowledge Management
    tab1, tab2 = st.sidebar.tabs(["📝 Knowledge Base", "📧 Email Campaign"])
    
    with tab1:
        st.subheader("Edit Knowledge Base")
        current_knowledge = load_knowledge()

        updated_text = st.text_area(
            "Modify knowledge.txt content:",
            value=current_knowledge,
            height=300
        )

        if st.button("Save & Commit to GitHub"):
            try:
                update_github_knowledge(updated_text)
                st.cache_data.clear()
                st.success("Updated knowledge.txt on GitHub! Reloading app...")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to update GitHub: {e}")

    # Tab 2: Apps Script Outreach Trigger
    with tab2:
        st.subheader("Trigger Prospect Campaign")
        campaign_topic = st.text_input("Target Domain/Topic", "AI for Decision-Makers")
        webhook_url = st.secrets.get("APPS_SCRIPT_URL", "")

        if st.button("🚀 Launch Email Pipeline"):
            if not webhook_url:
                st.error("Please configure APPS_SCRIPT_URL in Streamlit secrets.")
            else:
                try:
                    res = requests.post(webhook_url, json={"topic": campaign_topic})
                    if res.status_code == 200:
                        st.success("Apps Script campaign triggered successfully!")
                    else:
                        st.error(f"Error triggering campaign: {res.status_code}")
                except Exception as e:
                    st.error(f"Request failed: {e}")

# --- Chat Interface ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display message history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Process user prompt
if prompt := st.chat_input("Ask about our AI Executive Workshops..."):
    # Append and render user query
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Convert chat history into contents format for Gemini
    history_contents = []
    for msg in st.session_state.messages:
        role = "user" if msg["role"] == "user" else "model"
        history_contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])]))

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
                contents=history_contents,
                config=config,
            )

            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌")

            if not full_response:
                full_response = "I was unable to process that specific query. Please try rephrasing."

            message_placeholder.markdown(full_response)

        except Exception as e:
            full_response = "I am experiencing temporary connection issues. Please try again shortly."
            message_placeholder.markdown(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})
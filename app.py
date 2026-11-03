
import streamlit as st
import requests
from github import Github, GithubException
from google import genai
from google.genai import types


# =========================================================
# 1. PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="IIT Guwahati School of Business - AI Assistant",
    page_icon="🎓",
    layout="wide"
)

st.markdown("""
<style>
#MainMenu {visibility: hidden;}
.stAppHeader {background: transparent;}
footer {visibility: hidden;}

[data-testid="stSidebarCollapseButton"] {
    visibility: visible !important;
    display: block !important;
    z-index: 999999;
}

.knowledge-note {
    background-color: #eef4ff;
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 12px;
}
</style>
""", unsafe_allow_html=True)


# =========================================================
# 2. CONFIGURATION
# =========================================================

BRANCH = "main"
KNOWLEDGE_FILE = "knowledge.txt"

try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"]

except Exception:
    st.error(
        "Missing configuration. Please check GEMINI_API_KEY, "
        "GITHUB_TOKEN and REPO_NAME in Streamlit Secrets."
    )
    st.stop()

client = genai.Client(api_key=GEMINI_API_KEY)


# =========================================================
# 3. GITHUB FUNCTIONS
# =========================================================

def get_github_repo():
    """Connect to the configured GitHub repository."""
    github = Github(GITHUB_TOKEN)
    return github.get_repo(REPO_NAME)


def load_knowledge():
    """Load the latest knowledge.txt directly from GitHub."""

    repo = get_github_repo()

    contents = repo.get_contents(
        KNOWLEDGE_FILE,
        ref=BRANCH
    )

    return contents.decoded_content.decode("utf-8")


def update_github_knowledge(new_content):
    """Create or update knowledge.txt in GitHub."""

    repo = get_github_repo()

    try:
        contents = repo.get_contents(
            KNOWLEDGE_FILE,
            ref=BRANCH
        )

        result = repo.update_file(
            path=KNOWLEDGE_FILE,
            message="Update chatbot knowledge via Streamlit dashboard",
            content=new_content,
            sha=contents.sha,
            branch=BRANCH
        )

    except GithubException as error:

        if error.status != 404:
            raise

        result = repo.create_file(
            path=KNOWLEDGE_FILE,
            message="Create chatbot knowledge via Streamlit dashboard",
            content=new_content,
            branch=BRANCH
        )

    return result


# =========================================================
# 4. INITIALIZE SESSION STATE
# =========================================================

if "knowledge_text" not in st.session_state:

    try:
        st.session_state.knowledge_text = load_knowledge()
        st.session_state.knowledge_error = None

    except Exception as error:

        st.session_state.knowledge_text = ""

        st.session_state.knowledge_error = str(error)

        # Local fallback, if available
        try:
            with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as file:
                st.session_state.knowledge_text = file.read()

        except FileNotFoundError:
            pass


if "knowledge_revision" not in st.session_state:
    st.session_state.knowledge_revision = 0


if "messages" not in st.session_state:
    st.session_state.messages = []


# =========================================================
# 5. PAGE HEADER
# =========================================================

st.title("🎓 IIT Guwahati School of Business")
st.caption("AI Executive Workshop Assistant")


# =========================================================
# 6. ADMIN DASHBOARD
# =========================================================

st.sidebar.title("⚙️ Admin Control Panel")

admin_open = st.sidebar.checkbox("Open Admin Dashboard")


if admin_open:

    st.divider()

    st.header("⚙️ Knowledge & Campaign Management")

    tab1, tab2 = st.tabs([
        "📝 Knowledge Management",
        "📧 Email Campaign"
    ])


    # -----------------------------------------------------
    # TAB 1: KNOWLEDGE MANAGEMENT
    # -----------------------------------------------------

    with tab1:

        st.subheader("Manage Chatbot Knowledge")

        st.markdown("""
        Add, edit or remove information that your Gemini chatbot
        uses when answering prospect questions.

        **Changes are saved directly to your GitHub repository.**
        """)

        if st.session_state.knowledge_error:

            st.warning(
                "Could not load knowledge from GitHub. "
                "A local fallback may be displayed. "
                "Check your GitHub configuration before saving."
            )

            with st.expander("Technical details"):
                st.code(st.session_state.knowledge_error)


        if st.button("🔄 Refresh from GitHub"):

            try:
                latest_knowledge = load_knowledge()

                st.session_state.knowledge_text = latest_knowledge
                st.session_state.knowledge_error = None

                st.session_state.knowledge_revision += 1

                st.success("Knowledge refreshed from GitHub.")

                st.rerun()

            except Exception as error:
                st.error(f"Unable to refresh: {error}")


        st.markdown("### Edit existing knowledge")

        st.caption(
            "You can add, modify or delete any text in this editor. "
            "Save your changes when finished."
        )

        editor_key = (
            "knowledge_editor_"
            + str(st.session_state.knowledge_revision)
        )

        current_editor_content = st.text_area(
            "Knowledge Base",
            value=st.session_state.knowledge_text,
            height=400,
            key=editor_key
        )


        if st.button(
            "💾 Save Changes to GitHub",
            type="primary",
            key="save_knowledge"
        ):

            try:

                update_github_knowledge(current_editor_content)

                st.session_state.knowledge_text = current_editor_content
                st.session_state.knowledge_error = None

                st.session_state.knowledge_revision += 1

                st.success(
                    "Knowledge successfully saved to GitHub!"
                )

                st.rerun()

            except Exception as error:

                st.error(
                    f"Unable to save knowledge: {error}"
                )


        st.divider()

        # ADD NEW INFORMATION

        st.markdown("### ➕ Add new information")

        st.caption(
            "This will append new information to your existing knowledge base."
        )

        with st.form("add_knowledge_form"):

            new_information = st.text_area(
                "Enter new information",
                height=150,
                placeholder=(
                    "Example:\n"
                    "Workshop Module: Generative AI\n"
                    "Duration: 2 hours\n"
                    "Description: ..."
                )
            )

            add_submitted = st.form_submit_button(
                "➕ Add Information & Save to GitHub",
                type="primary"
            )


        if add_submitted:

            if not new_information.strip():

                st.warning("Please enter some information first.")

            else:

                try:

                    existing_content = current_editor_content.strip()

                    updated_content = (
                        existing_content
                        + "\n\n"
                        + new_information.strip()
                        + "\n"
                    )

                    update_github_knowledge(updated_content)

                    st.session_state.knowledge_text = updated_content
                    st.session_state.knowledge_error = None

                    st.session_state.knowledge_revision += 1

                    st.success(
                        "New information added and saved successfully!"
                    )

                    st.rerun()

                except Exception as error:

                    st.error(
                        f"Unable to add information: {error}"
                    )


        st.divider()

        st.markdown("### 📊 Knowledge Base Status")

        st.write(
            f"**Characters:** "
            f"{len(st.session_state.knowledge_text)}"
        )

        st.write(
            f"**Storage:** GitHub repository"
        )

        st.write(
            f"**File:** `{KNOWLEDGE_FILE}`"
        )

        st.write(
            f"**Branch:** `{BRANCH}`"
        )


    # -----------------------------------------------------
    # TAB 2: EMAIL CAMPAIGN
    # -----------------------------------------------------

    with tab2:

        st.subheader("Trigger Prospect Campaign")

        campaign_topic = st.text_input(
            "Target Domain/Topic",
            "AI for Decision-Makers"
        )

        webhook_url = st.secrets.get(
            "APPS_SCRIPT_URL",
            ""
        )

        if st.button("🚀 Launch Email Pipeline"):

            if not webhook_url:

                st.error(
                    "Please configure APPS_SCRIPT_URL in Streamlit Secrets."
                )

            else:

                try:

                    response = requests.post(
                        webhook_url,
                        json={"topic": campaign_topic},
                        timeout=30
                    )

                    if response.status_code == 200:

                        st.success(
                            "Apps Script campaign triggered successfully!"
                        )

                    else:

                        st.error(
                            f"Campaign error: HTTP {response.status_code}"
                        )

                except Exception as error:

                    st.error(
                        f"Request failed: {error}"
                    )


# =========================================================
# 7. CHATBOT KNOWLEDGE INSTRUCTION
# =========================================================

knowledge_text = st.session_state.knowledge_text

system_instruction = f"""
You are an official AI Assistant for the IIT Guwahati School of Business.

Your job is to answer prospect inquiries about the Executive AI Workshops,
curriculum, registration, fees, schedules and related information.

IMPORTANT RULES:

1. Use the provided knowledge base as your primary source of truth.
2. Never invent or assume missing workshop details.
3. If information is unavailable, politely say that you do not have
   that information and direct the prospect to the provided contact.
4. Be professional, helpful and conversational.
5. Give clear and concise answers.
6. Do not contradict the information in the knowledge base.

--- KNOWLEDGE BASE ---

{knowledge_text}

--- END KNOWLEDGE BASE ---
"""


# =========================================================
# 8. CHAT INTERFACE
# =========================================================

st.divider()

st.subheader("💬 Chat with our AI Assistant")

if not knowledge_text.strip():

    st.warning(
        "The knowledge base is currently empty. "
        "Please ask the administrator to add workshop information."
    )


# Display conversation history

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# Process new prompt

if prompt := st.chat_input(
    "Ask about our AI Executive Workshops..."
):

    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)


    # Prepare Gemini conversation history

    history_contents = []

    for message in st.session_state.messages:

        role = (
            "user"
            if message["role"] == "user"
            else "model"
        )

        history_contents.append(
            types.Content(
                role=role,
                parts=[
                    types.Part.from_text(
                        text=message["content"]
                    )
                ]
            )
        )


    # Gemini generation configuration

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=0.3
    )


    # Generate streaming response

    with st.chat_message("assistant"):

        message_placeholder = st.empty()

        full_response = ""

        try:

            response = client.models.generate_content_stream(
                model="gemini-3.5-flash",
                contents=history_contents,
                config=config
            )

            for chunk in response:

                if chunk.text:

                    full_response += chunk.text

                    message_placeholder.markdown(
                        full_response + "▌"
                    )


            if not full_response:

                full_response = (
                    "I was unable to process that specific query. "
                    "Please try rephrasing."
                )

            message_placeholder.markdown(full_response)


        except Exception as error:

            full_response = (
                "I am experiencing temporary connection issues. "
                "Please try again shortly."
            )

            message_placeholder.markdown(full_response)

            with st.expander("Technical error details"):
                st.code(str(error))


    st.session_state.messages.append({
        "role": "assistant",
        "content": full_response
    })

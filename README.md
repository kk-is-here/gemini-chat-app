# IIT Guwahati School of Business - AI Chatbot & Admin System

An AI chatbot and admin management dashboard built with Streamlit and the Google Gemini API (`gemini-3.5-flash`).

## Features

- **Conversational AI Chatbot:** Answers user queries about AI workshops, schedules, pricing, and curriculum using context loaded from `knowledge.txt`.
- **Admin Control Panel:** Non-technical administrators can edit `knowledge.txt` directly from the Streamlit UI and commit changes to GitHub via `PyGithub`.
- **Automated Deployments:** Saving changes in the Admin Panel automatically updates GitHub, triggering re-deployments across cloud hosting environments.
- **Outreach Campaign Webhook:** Integrated trigger button to fire Google Apps Script email prospecting workflows.

## Environment Secrets Required

Configure the following secrets in Streamlit Cloud (`.streamlit/secrets.toml`):

```toml
GEMINI_API_KEY = "your-gemini-api-key"
GITHUB_TOKEN = "your-github-personal-access-token"
REPO_NAME = "kk-is-here/gemini-chat-app"
APPS_SCRIPT_URL = "[https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/exec](https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/exec)"
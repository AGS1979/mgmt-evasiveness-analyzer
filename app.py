# 🚀 Streamlit Config and Imports
import streamlit as st
st.set_page_config(page_title="Aranca | Mgmt Tone Analyzer", layout="wide")

import requests
import pandas as pd
import re
import os
from openai import OpenAI
from datetime import datetime, timedelta
import io
import base64
import matplotlib.pyplot as plt
from streamlit_oauth import OAuth2Component

# --- API KEYS ---
client_id = st.secrets["oauth"]["client_id"]
client_secret = st.secrets["oauth"]["client_secret"]
FMP_API_KEY = st.secrets["fmp"]["api_key"]
DEEPSEEK_API_KEY = st.secrets["deepseek"]["api_key"]

# --- Google OAuth Setup ---
redirect_uri = "https://evasiveness-analyzer.streamlit.app"
scope = "openid email profile"

# Correct usage for streamlit-oauth==0.1.5 (DO NOT pass redirect_uri in constructor)
oauth2 = OAuth2Component(
    client_id=client_id,
    client_secret=client_secret,
    authorize_endpoint="https://accounts.google.com/o/oauth2/v2/auth",
    token_endpoint="https://oauth2.googleapis.com/token",
    revoke_endpoint="https://oauth2.googleapis.com/revoke"
)

# --- Login Button ---
result = oauth2.authorize_button(
    "Login with Google",
    redirect_uri=redirect_uri,  # passed here, not in constructor
    scope=scope,
    key="google_login"
)

if result and "token" in result:
    access_token = result["token"]["access_token"]

    # Get user info
    user_info = oauth2.get_user_info(
        "https://openidconnect.googleapis.com/v1/userinfo",
        access_token
    )

    user_email = user_info["email"]
    st.success(f"✅ Logged in as {user_email}")

    # --- Whitelisted Emails ---
    WHITELISTED_EMAILS = {
        "avinashg.singh@aranca.com",
        "ujjal.roy@aranca.com",
        "rohit.dhawan@aranca.com",
        "avi104@yahoo.co.in",
        "antoine.mauger@anker.com",
        "witek.sobieszek@anker.com"
    }

    if user_email.lower() not in WHITELISTED_EMAILS:
        st.error("❌ Access Denied. Email not authorized.")
        st.stop()
else:
    st.warning("⚠️ Please login to continue.")
    st.stop()


# --- Logo and CSS Styling ---
def get_base64_logo(path="logo.png"):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

logo_base64 = get_base64_logo()

st.markdown(f"""
<style>
    html, body, .main {{
        background-color: #ffffff;
        color: #010101;
    }}
    .stButton > button {{
        background-color: #010101;
        color: white;
        border-radius: 8px;
        font-weight: bold;
        transition: all 0.3s ease;
    }}
    .stButton > button:hover {{
        background-color: #2196F3 !important;
        color: white !important;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }}
    .stTextInput input::placeholder {{
        color: #999 !important;
    }}

    /* Dark gray styling for text, number, and password inputs */
    input, select, textarea {{
        background-color: #010101 !important;  /* dark gray */
        color: white !important;              /* white text */
        border: 1px solid #010101 !important;
        border-radius: 8px !important;
    }}

    /* Make placeholder text slightly lighter */
    input::placeholder {{
        color: #aaa !important;
    }}


    label, .stTextInput label {{
        color: #222 !important;
        font-size: 1.2rem !important;
        font-weight: 600 !important;
        display: inline-flex !important;
        align-items: center !important;
        gap: 10px;
    }}
    .streamlit-expanderHeader:hover {{
        color: #2196F3 !important;
        background-color: #f5f5f5 !important;
        cursor: pointer;
    }}
    .custom-footer {{
        position: fixed;
        bottom: 15px;
        width: 100%;
        text-align: center;
        color: #010101;
        font-size: 0.85em;
    }}
</style>

<style>
/* Apply consistent dark gray to all major input containers */
div[data-baseweb="input"] input,
div[data-baseweb="input"] > div, 
div[data-baseweb="select"] > div,
div[data-baseweb="textarea"] textarea {{
    background-color: #010101 !important; /* consistent dark gray */
    color: white !important;
    border: 1px solid #010101 !important;
    border-radius: 8px !important;
    font-weight: 500;
}}

/* Dropdown icon color (selectbox caret) */
div[data-baseweb="select"] svg {{
    color: white !important;
}}

/* Password toggle eye icon */
button[aria-label="Show password"], 
button[aria-label="Hide password"] {{
    color: white !important;
}}

/* Fix placeholder color */
input::placeholder {{
    color: #ddd !important;
}}

/* Align all label styling */
label, .stTextInput label {{
    color: #222 !important;
    font-size: 1.2rem !important;
    font-weight: 600 !important;
    display: inline-flex !important;
    align-items: center !important;
    gap: 10px;
}}
</style>


<style>
/* Match number_input stepper (the +/- buttons) to the gray input box */
div[data-baseweb="input"] [aria-label="Increment"],
div[data-baseweb="input"] [aria-label="Decrement"] {{
    background-color: #010101 !important;
    color: white !important;
    border-left: 1px solid #888 !important;
}}

/* Match selectbox background (entire dropdown) */
div[data-baseweb="select"] > div {{
    background-color: #010101 !important;
    color: white !important;
    border: 1px solid #010101 !important;
    border-radius: 8px !important;
}}

/* Match the dropdown arrow */
div[data-baseweb="select"] svg {{
    color: white !important;
}}
</style>

<style>
/* Common gray for all base containers */
div[data-baseweb="input"],
div[data-baseweb="select"],
div[data-baseweb="textarea"] {{
    background-color: #010101 !important;
    border-radius: 8px !important;
    border: 1px solid #010101 !important;
    color: white !important;
}}

/* Inner input boxes */
div[data-baseweb="input"] input,
div[data-baseweb="textarea"] textarea {{
    background-color: #010101 !important;
    color: white !important;
    font-weight: 500 !important;
}}

/* Select dropdown text */
div[data-baseweb="select"] > div {{
    background-color: #010101 !important;
    color: white !important;
}}

/* Fix the +/- buttons for number input */
div[data-baseweb="input"] > div > div[role="button"] {{
    background-color: #010101 !important;
    color: white !important;
    border-left: 1px solid #888 !important;
}}

/* Dropdown caret icon */
div[data-baseweb="select"] svg {{
    color: white !important;
}}

/* Password toggle buttons */
button[aria-label="Show password"],
button[aria-label="Hide password"] {{
    color: white !important;
    background-color: #010101 !important;
}}

/* Placeholder text */
input::placeholder {{
    color: #ddd !important;
}}

/* Label consistency */
label, .stTextInput label {{
    color: #010101 !important;
    font-size: 1.2rem !important;
    font-weight: 600 !important;
}}

div[data-baseweb="input"] > div > div:last-child {{
    background-color: #010101 !important;
    border-left: 1px solid #010101 !important;
    border-top-right-radius: 8px !important;
    border-bottom-right-radius: 8px !important;
}}

</style>




<div style="display: flex; flex-direction: column; align-items: center; margin-bottom: 20px;">
    <img src="data:image/png;base64,{logo_base64}" style="height: 40px; max-width: 240px; margin-bottom: 10px;" />
    <h1 style="margin: 0; font-size: 2.4rem; color: #010101;">Management Tone Analyzer</h1>
    <p style="margin: 6px 0 0 0; font-size: 1.1rem; color: #010101;">AI-Powered Evasiveness Detection from Earnings Calls</p>
</div>
""", unsafe_allow_html=True)

# --- Inputs ---
st.subheader("🔍 Single Quarter Analysis")
company_name = st.text_input("Company Name (e.g., Boeing)")
year = st.number_input("Year", min_value=2005, max_value=2050, value=2024)
quarter = st.selectbox("Quarter", [1, 2, 3, 4])

if st.button("🚀 Run Analysis"):
    if not company_name:
        st.error("Please enter company name.")
        st.stop()

    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com/v1")

    def resolve_ticker(name):
        prompt = f"What is the FMP-compatible ticker for this company: '{name}'? Return only the ticker symbol."
        res = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        return res.choices[0].message.content.strip().upper()

    def fetch_transcript(ticker, year, quarter):
        url = f"https://financialmodelingprep.com/api/v3/earning_call_transcript/{ticker}?year={year}&quarter={quarter}&apikey={FMP_API_KEY}"
        r = requests.get(url)
        return r.json()[0] if r.status_code == 200 and r.json() else None

    def get_price(ticker, date_str):
        try:
            end_date = pd.to_datetime(date_str)
            start_date = end_date - timedelta(days=7)
            url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?from={start_date.strftime('%Y-%m-%d')}&to={end_date.strftime('%Y-%m-%d')}&apikey={FMP_API_KEY}"
            r = requests.get(url)
            data = r.json().get("historical", []) if r.status_code == 200 else []
            if not data:
                return None
            df = pd.DataFrame(data)
            df["date"] = pd.to_datetime(df["date"])
            df = df[df["date"] <= end_date]
            return df.sort_values("date", ascending=False).iloc[0]["close"]
        except:
            return None

    ticker = resolve_ticker(company_name)
    transcript = fetch_transcript(ticker, year, quarter)

    if not transcript:
        st.error("❌ Transcript not found.")
        st.stop()

    content = transcript["content"]
    date = transcript["date"]

    speaker_turns = [line.strip() for line in content.split("\n") if ":" in line and len(line.strip()) > 15]
    management_turns = [line for line in speaker_turns if not re.search(r'\b(operator|analyst|moderator|host|coordinator|caller)\b', line.split(":")[0], re.IGNORECASE)]
    total_statements = len(management_turns)

    responses = []
    batch_size = 20

    for i in range(0, total_statements, batch_size):
        batch = management_turns[i:i + batch_size]
        batch_prompt = f"""
        You are a forensic analyst specializing in executive communication.

        Below are statements made by company management during an earnings call. Each statement may respond to a question from an analyst.

        Your task is to identify **only those speaker turns that show evasiveness**. For each speaker turn, carefully read the full text and evaluate whether the speaker is:

        1. Avoiding or refusing to answer a direct question
        2. Providing vague or overly generalized statements without specifics
        3. Shifting blame, deflecting responsibility, or overstating confidence without justification
        4. Contradicting earlier disclosed facts or using ambiguous qualifiers

        For each evasive case, return:
        ---
        Response: The **most relevant 2–3 consecutive sentences** that reflect the evasiveness (not random fragments)
        Category:
        - 2 = Somewhat evasive – vague or generic but at least partially addresses the topic
        - 3 = Clearly evasive – refuses to answer, contradicts info, or uses avoidance tactics
        Reason: A **specific and concise explanation** of why the excerpt is evasive. Mention what information was avoided, what ambiguity exists, or what signals a lack of transparency.

        Output format should be:
        ---
        Response: "..."
        Category: 2
        Reason: ...

        If no part of the speaker turn is evasive, skip it.

        Statements:
        {chr(10).join([f"{j+1}. {line}" for j, line in enumerate(batch)])}
        """



        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "You are an expert earnings call analyst."},
                    {"role": "user", "content": batch_prompt}
                ],
                temperature=0
            )
            result_text = response.choices[0].message.content.strip()
            matches = re.findall(r'Response:\s*"(.*?)"\s*Category:\s*([23])\s*Reason:\s*(.*?)(?=\n\n|---|\Z)', result_text, re.DOTALL)
            responses.extend(matches)
        except Exception as e:
            st.warning(f"⚠️ Error: {e}")
            continue

    df = pd.DataFrame(columns=["Statement", "Category", "Reason"])
    score = 0
    if responses:
        df = pd.DataFrame(responses, columns=["Statement", "Category", "Reason"])
        df["Category"] = df["Category"].astype(int)
        score = round(df["Category"].map({2: 1, 3: 2}).sum() / (total_statements * 2) * 10, 2)

    price = get_price(ticker, date)
    summary = pd.DataFrame([{
        "Company": company_name,
        "Ticker": ticker,
        "Year": year,
        "Quarter": quarter,
        "Transcript Date": date,
        "Evasiveness Score": score,
        "Share Price": price
    }])
    st.dataframe(summary)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        summary.to_excel(writer, index=False, sheet_name="Summary")
        if not df.empty:
            df.to_excel(writer, index=False, sheet_name="Evasive Statements")
        writer._save()

    st.download_button("📥 Download Report", output.getvalue(), file_name=f"{ticker}_Q{quarter}_{year}.xlsx")

    if not df.empty:
        st.subheader("🧠 Evasive Statements")
        st.dataframe(df)

# --- Merging Section ---
st.markdown("---")
st.header("📈 Merge and Visualize Scores")
uploaded = st.file_uploader("Upload XLSX Reports", type=["xlsx"], accept_multiple_files=True)

if uploaded:
    merged = pd.concat([pd.read_excel(f, sheet_name="Summary") for f in uploaded], ignore_index=True)
    merged["Transcript Date"] = pd.to_datetime(merged["Transcript Date"])
    merged.sort_values("Transcript Date", inplace=True)

    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.plot(merged["Transcript Date"], merged["Evasiveness Score"], color="red", marker="o", label="Score")
    ax2 = ax1.twinx()
    ax2.plot(merged["Transcript Date"], merged["Share Price"], color="blue", marker="x", label="Price")
    ax1.set_ylabel("Evasiveness Score", color="red")
    ax2.set_ylabel("Share Price", color="blue")
    fig.tight_layout()
    st.pyplot(fig)

    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="xlsxwriter") as writer:
        merged.to_excel(writer, index=False, sheet_name="Merged")
        writer._save()
    st.download_button("📥 Download Merged Excel", out.getvalue(), file_name="merged_evasiveness.xlsx")

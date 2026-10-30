import streamlit as st
import pandas as pd
import json
import time
from google import genai
from google.genai import types

# ==========================================
# 1. PAGE SETUP & CORPORATE STYLING
# ==========================================
st.set_page_config(layout="wide", page_title="DILG HGDG Assessment Tool")

custom_styling = """
    <style>
    /* Corporate Purple Accents */
    :root {
        --primary-purple: #4B0082; /* Indigo / Corporate Purple */
        --secondary-purple: #6A5ACD;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: var(--primary-purple) !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Buttons */
    .stButton>button {
        background-color: var(--primary-purple) !important;
        color: white !important;
        border: none !important;
        border-radius: 4px !important;
        font-weight: 600 !important;
    }
    
    .stButton>button:hover {
        background-color: var(--secondary-purple) !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 3px solid var(--primary-purple);
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: var(--primary-purple) !important;
    }
    
    /* Print styling */
    @media print {
        [data-testid="stSidebar"] { display: none !important; }
        header { display: none !important; }
        footer { display: none !important; }
        .main .block-container { max-width: 100% !important; padding-top: 0 !important; }
    }
    </style>
"""
st.markdown(custom_styling, unsafe_allow_html=True)

st.title("HGDG Planning Tool")
st.write("Automated Program and Project Gender Analysis Tool")

# ==========================================
# 2. ENRICHED SECTOR GUIDELINES (GEWE PERMANENTLY INTEGRATED)
# ==========================================
sector_guidelines = {
    "General / Multi-Sector": "Evaluate using standard Expanded Box 7. Check for cross-cutting GEWE impact indicators.",
    "Agriculture, Fisheries and Forestry": "GEWE (E-11) Focus: Track average income of small-scale producers by sex, and the number of women farmers/fisher folks awarded with instruments of recognition or land free patents.",
    "Infrastructure": "GEWE (E-17) Focus: Track the percentage of employed women in the infrastructure sector, and proportion of women with convenient access to safe drinking water, electricity, and public transport.",
    "Disaster Risk Reduction and Management (DRRM-CCA)": "GEWE (D-10) Focus: Track the ratio of female to male persons affected by a disaster who received assistance, and the incidence of GBV/VAW in times of natural disasters.",
    "Access to Justice": "GEWE (B-6) Focus: Track the extent of recovery and reintegration of women/children survivors of GBV, and the attrition level of VAWC-related cases.",
    "Formal Labor": "GEWE (E-14) Focus: Track the Labor Force Participation Rate by sex, gender gap in wages, and incidence of gender-based violence in the workplace.",
    "Informal Economy": "GEWE (E-15) Focus: Track the share of women in informal non-agriculture employment, and the proportion of formal loans granted to women entrepreneurs.",
    "MSMEs, Trade and Industry": "GEWE (E-12) Focus: Track the proportion of firms owned by women by size, and average monthly income of women in business and entrepreneurship.",
    "Tourism": "GEWE (E-13) Focus: Track the prevalence of GBV against women tourists/workers, and the proportion of women workers reporting specific improvements in situations.",
    "Health": "GEWE (A-2) Focus: Track maternal mortality ratio, unmet need for family planning, and coverage of essential health services for disadvantaged populations.",
    "Education": "GEWE (A-1) Focus: Track completion and cohort survival rates by sex, and the proportion of reported cases of discrimination against female students/faculty resolved.",
    "Women in Bureaucracy, Politics and Governance": "GEWE (C-8) Focus: Track the proportion of seats occupied by women in local and national governing boards and decision-making bodies."
}

# ==========================================
# 3. USER INPUT (SIDEBAR)
# ==========================================
with st.sidebar:
    st.header("Project Input")
    
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except KeyError:
        st.error("System Error: API Key is missing from Streamlit Cloud Secrets. Please add it in the App Settings.")
        st.stop()
    
    selected_sector = st.selectbox(
        "Select HGDG Sector",
        options=list(sector_guidelines.keys())
    )
    
    project_title = st.text_input("Project Title", placeholder="e.g., Rural Water Supply")
    project_text = st.text_area("Paste Project Proposal Text Here", height=300)
    
    st.subheader("Additional Context")
    reference_text = st.text_area("Paste Additional Local Memos (Optional)", height=100)
    
    analyze_btn = st.button("Generate Personalized HGDG Checklist")

# ==========================================
# 4. AI LOGIC & REPORT GENERATION
# ==========================================
if analyze_btn:
    if not api_key or not project_text:
        st.error("Please ensure the API Key is set and paste a project proposal.")
        st.stop()
        
    with st.spinner("Analyzing proposal and generating personalized GEWE assessment..."):
        try:
            client = genai.Client(api_key=api_key)
            active_sector_rules = sector_guidelines[selected_sector]
            
            final_prompt = f"""
            You are an expert evaluator for the Department of the Interior and Local Government (DILG).
            Evaluate the provided local government project proposal using the Harmonized Gender and Development Guidelines (HGDG) Expanded Box 7.
            
            CRITICAL INSTRUCTION FOR GEWE INTEGRATION:
            You must actively evaluate the proposal's monitoring and evaluation framework against the Gender Equality and Women's Empowerment (GEWE) Indicators.
            Specifically, check if the proposal contains measurable targets that align with the GEWE Impact, Outcome 1, and Outcome 2 indicators for the selected sector.
            
            Sector Specific HGDG & GEWE Rules to Apply:
            {active_sector_rules}
            
            PERSONALIZATION INSTRUCTION:
            The 'result_comment' for each element MUST be highly personalized to the provided text. 
            Do NOT use generic phrases. You must directly name the specific location, the exact target beneficiaries, and the specific facilities/services mentioned in the proposal. Ensure your evaluation standards align with strict LGU monitoring systems like Katarungang Pambarangay compliance and the Full Disclosure Policy Portal.
            
            Additional Context:
            {reference_text}
            
            Project Proposal:
            {project_text}
            
            You MUST output your evaluation in valid JSON format with this EXACT structure:
            {{
              "elements": [
                {{
                  "element_number": 1,
                  "element_name": "Involvement of women and men in project conceptualization and design",
                  "response": "Yes / Partly yes / No",
                  "score": 2.0,
                  "result_comment": "Highly personalized justification..."
                }}
              ],
              "total_score": 18.5,
              "interpretation": "Gender-responsive"
            }}
            """
            
            # --- AUTO-RETRY LOOP & 3.8-FLASH MODEL ---
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = client.models.generate_content(
                        model='gemini-3.8-flash',
                        contents=final_prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type='application/json',
                        ),
                    )
                    break 
                except Exception as api_e:
                    if "503" in str(api_e) and attempt < max_retries - 1:
                        time.sleep(5) 
                        continue
                    else:
                        raise api_e 
            # --------------------------------
            
            data = json.loads(response.text)
            
            # --- RENDER THE REPORT ---
            st.success(f"Analysis Complete for: **{selected_sector}**")
            st.divider()
            
            st.subheader(f"Evaluation Report: {project_title}")
            st.write(f"**Sector Evaluated:** {selected_sector}")
            st.write("---")
            
            st.markdown("### Summary Checklist for the Assessment of Proposed Projects")
            df = pd.DataFrame(data["elements"])
            df = df[["element_number", "element_name", "response", "score", "result_comment"]]
            df.columns = ["No.", "Element or Requirement", "Response", "Score", "Result / Comments"]
            
            st.table(df)
            
            st.write("---")
            st.markdown("### Summary of Scores")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric(label="Total GAD Score (Max 20)", value=data["total_score"])
            with col2:
                st.metric(label="Interpretation", value=data["interpretation"])

            score = float(data["total_score"])
            if score < 4.0:
                attribution = "0%"
            elif 4.0 <= score <= 7.9:
                attribution = "25%"
            elif 8.0 <= score <= 14.9:
                attribution = "50%"
            elif 15.0 <= score <= 19.9:
                attribution = "75%"
            else:
                attribution = "100%"
                
            st.info(f"**GAD Budget Attribution:** {attribution} of the total project cost.")
            
        except Exception as e:
            st.error(f"An error occurred: {e}. Please ensure your API key is correct and try again.")
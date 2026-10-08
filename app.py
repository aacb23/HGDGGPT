import os
import json
import streamlit as st
import pandas as pd
from openai import OpenAI

# ==========================================
# 1. PAGE SETUP & PRINT STYLING
# ==========================================
st.set_page_config(layout="wide", page_title="HGDG Assessment Tool")

hide_elements_during_print = """
<style>
@media print {
    [data-testid="stSidebar"] { display: none !important; }
    header { display: none !important; }
    footer { display: none !important; }
    .main .block-container {
        max-width: 100% !important;
        padding-top: 0 !important;
    }
}
</style>
"""
st.markdown(hide_elements_during_print, unsafe_allow_html=True)

st.title("HGDG Project Design Checklist (Expanded Box 7)")
st.write("AI-Powered Assessment Tool for Local Government Units")

# ==========================================
# 2. SECTOR GUIDELINES DICTIONARY
# ==========================================
sector_guidelines = {
    "General / Multi-Sector": "Evaluate using the standard Expanded Box 7 guidelines.",
    "Agriculture and Agrarian Reform": "Focus on access to agricultural inputs (seeds, credit, land titles) for women. Verify if extension services target female farmers.",
    "Natural Resource Management": "Focus on women's access to and control over forest, water, and marine resources, and participation in environmental management.",
    "Infrastructure": "Focus strictly on physical welfare, access to the facility, and employment generated. Verify mitigating strategies for displacement.",
    "Private Sector Development": "Evaluate support for women-owned enterprises, access to non-loan resources, and market linkages.",
    "Education": "Assess school participation rates by sex, gender-sensitive curricula, and female leadership in the education sector.",
    "Health": "Focus on maternal health, reproductive health services, and the gender-sensitive delivery of quality health programs.",
    "Housing and Settlement": "Evaluate women's access to housing units, deeds/titles, and participation in homeowner associations.",
    "Women in Areas under Armed Conflict": "Assess gender-responsive services in refugee camps, security from violence, and participation in peace negotiations.",
    "Justice": "Focus on women's access to legal services, handling of violence against women (VAW) cases, and gender-sensitivity of legal personnel.",
    "Information and Communication Technologies (ICT)": "Assess women's access to ICT training, tech employment, and gender-responsive digital content.",
    "Microfinance": "Evaluate women's access to loans, financial literacy training, and actual control over loan usage.",
    "Labor and Employment": "Focus on equal opportunity employment, workplace safety, anti-sexual harassment mechanisms, and leadership roles.",
    "Child Labor": "Assess interventions targeting girl and boy child laborers, rehabilitation, and education access.",
    "Migration": "Evaluate protection mechanisms for female migrants, safe remittance channels, and reintegration programs.",
    "Funding Facilities": "Assess the integration of GAD criteria in the evaluation and selection of projects for facility funding.",
    "Disaster Risk Reduction and Management (DRRM)": "Focus on gender-specific vulnerabilities, women's participation in DRRM councils, and gender-responsive relief.",
    "Energy": "Evaluate women's access to energy resources, participation in rural electrification, and related livelihood impacts.",
    "Fisheries": "Assess women's roles in pre- and post-harvest fishing activities, access to fishing tech, and coastal resource management.",
    "Tourism": "Focus on women's employment in tourism, protection from exploitation, and support for women-led cultural enterprises.",
    "Development Planning": "Assess the integration of gender analysis into local/regional development plans and GAD budget allocations."
}

# ==========================================
# 3. HGDG ELEMENTS
# ==========================================
HGDG_ELEMENTS = [
    "Involvement of women and men in project conceptualization and design",
    "Collection and use of sex-disaggregated data and gender-related information",
    "Conduct of gender analysis to identify gender issues and inequalities",
    "Use of gender analysis in project objectives, strategies, activities, and indicators",
    "Gender-responsive project implementation arrangements and mechanisms",
    "Provision of resources for gender-responsive project implementation",
    "Gender-responsive monitoring and evaluation mechanisms",
    "Participation of women and men in project monitoring and evaluation",
    "Use of gender-responsive indicators and targets",
    "Sustainability of gender-responsive project results and benefits",
]

# ==========================================
# 4. SIDEBAR INPUT
# ==========================================
with st.sidebar:
    st.header("Project Input")

    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        value=os.getenv("OPENAI_API_KEY", ""),
        help="You can also set OPENAI_API_KEY as an environment variable."
    )

    model = st.selectbox(
        "AI Model",
        options=["gpt-5.6-luna", "gpt-5.6-sol"],
        index=0,
        help="Luna is the faster/lower-cost option; Sol is the stronger reasoning option."
    )

    selected_sector = st.selectbox(
        "Select HGDG Sector",
        options=list(sector_guidelines.keys())
    )

    project_title = st.text_input("Project Title")
    project_text = st.text_area(
        "Paste Project Proposal Text Here",
        height=250
    )

    st.subheader("Additional Context")
    reference_text = st.text_area(
        "Paste Additional Local Memos/Ordinances (Optional)",
        height=150
    )

    analyze_btn = st.button(
        "Generate HGDG Checklist",
        type="primary",
        use_container_width=True
    )

# ==========================================
# 5. OPENAI ASSESSMENT
# ==========================================
if analyze_btn:
    if not api_key:
        st.error("Please enter your OpenAI API Key or set the OPENAI_API_KEY environment variable.")
        st.stop()

    if not project_text.strip():
        st.error("Please paste a project proposal.")
        st.stop()

    client = OpenAI(api_key=api_key)
    active_sector_rules = sector_guidelines[selected_sector]

    elements_text = "\n".join(
        f"{i + 1}. {name}" for i, name in enumerate(HGDG_ELEMENTS)
    )

    system_prompt = """
You are an expert evaluator assisting a Philippine local government unit
in assessing project proposals using the Harmonized Gender and Development
Guidelines (HGDG), Expanded Box 7.

Your job is to assess ONLY what is supported by the project proposal and
additional context supplied by the user. Do not invent facts, activities,
consultations, data, beneficiaries, or safeguards that are not stated.

For each of the 10 HGDG elements:
- response must be exactly one of: "Yes", "Partly Yes", "No"
- score must be:
  - Yes = 2.0
  - Partly Yes = 1.0
  - No = 0.0
- result_comment must briefly explain the score using evidence from the
  supplied material.
- If evidence is insufficient, do not assume compliance; score conservatively.

Calculate total_score as the sum of the 10 scores.
Interpret the overall result consistently with the total score.
"""

    user_prompt = f"""
HGDG SECTOR:
{selected_sector}

SECTOR-SPECIFIC GUIDANCE:
{active_sector_rules}

THE 10 ELEMENTS TO ASSESS:
{elements_text}

ADDITIONAL LOCAL CONTEXT:
{reference_text if reference_text.strip() else "None provided."}

PROJECT TITLE:
{project_title if project_title.strip() else "Untitled Project"}

PROJECT PROPOSAL:
{project_text}
"""

    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "elements": {
                "type": "array",
                "minItems": 10,
                "maxItems": 10,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "element_number": {"type": "integer"},
                        "element_name": {"type": "string"},
                        "response": {
                            "type": "string",
                            "enum": ["Yes", "Partly Yes", "No"]
                        },
                        "score": {
                            "type": "number",
                            "enum": [0, 1, 2]
                        },
                        "result_comment": {"type": "string"}
                    },
                    "required": [
                        "element_number",
                        "element_name",
                        "response",
                        "score",
                        "result_comment"
                    ]
                }
            },
            "total_score": {
                "type": "number",
                "minimum": 0,
                "maximum": 20
            },
            "interpretation": {"type": "string"}
        },
        "required": ["elements", "total_score", "interpretation"]
    }

    with st.spinner("Analyzing proposal with OpenAI..."):
        try:
            response = client.responses.create(
                model=model,
                instructions=system_prompt,
                input=user_prompt,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "hgdg_assessment",
                        "strict": True,
                        "schema": schema
                    }
                }
            )

            data = json.loads(response.output_text)

            # ==========================================
            # 6. RENDER REPORT
            # ==========================================
            st.success(f"Analysis Complete for: **{selected_sector}**")
            st.divider()

            st.subheader(
                f"Evaluation Report: {project_title or 'Untitled Project'}"
            )
            st.write(f"**Sector Evaluated:** {selected_sector}")

            st.markdown("### Summary Checklist for the Assessment of Proposed Projects")

            df = pd.DataFrame(data["elements"])
            df = df[
                ["element_number", "element_name", "response",
                 "score", "result_comment"]
            ]
            df.columns = [
                "No.",
                "Element or Requirement",
                "Response",
                "Score",
                "Result / Comments"
            ]

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

            st.markdown("### Summary of Scores")

            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    label="Total GAD Score (Max 20)",
                    value=data["total_score"]
                )

            with col2:
                st.metric(
                    label="Interpretation",
                    value=data["interpretation"]
                )

            score = float(data["total_score"])

            if score < 4.0:
                attribution = "0%"
            elif score <= 7.9:
                attribution = "25%"
            elif score <= 14.9:
                attribution = "50%"
            elif score <= 19.9:
                attribution = "75%"
            else:
                attribution = "100%"

            st.info(
                f"**GAD Budget Attribution:** {attribution} "
                "of the total project cost."
            )

            with st.expander("View AI Assessment JSON"):
                st.json(data)

        except Exception as e:
            st.error(
                f"An error occurred while generating the assessment: {e}"
            )
            st.info(
                "Check that your OpenAI API key is valid and that the "
                "selected model is available to your API project."
            )

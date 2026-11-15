"""Home page of the Credit Risk app. Run with: streamlit run app/streamlit_app.py"""

import streamlit as st

st.set_page_config(page_title="Credit Risk Default Prediction", page_icon="💳", layout="wide")

st.title("Credit Risk Default Prediction")
st.markdown(
    """
    Predicting the probability that a Lending Club loan defaults, using XGBoost and SHAP.

    Use the pages in the sidebar:
    - **Overview**: portfolio KPIs and default rates
    - **Explore**: slice default rates by grade, purpose, term and more
    - **Score an Applicant**: enter details and get a probability of default with an explanation
    """
)

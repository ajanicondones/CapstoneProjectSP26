import streamlit as st
import plotly.express as px
import pandas as pd

st.title("Health & Climate Dashboard")

# Sample data until backend is ready
data = {
    "Category": ["Cardiovascular", "Respiratory", "Mental Health", "Diabetes"],
    "Score": [78, 65, 82, 70]
}

df = pd.DataFrame(data)

st.subheader("Health Metrics by Category")
fig = px.bar(df, x="Category", y="Score", color="Category")
st.plotly_chart(fig)
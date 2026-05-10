import streamlit as st
import pandas as pd
import plotly.express as px
import requests

st.set_page_config(page_title="Health Dashboard", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login():
    st.title("Health Dashboard Login")
    user = st.text_input("Username")
    pw = st.text_input("Password", type="password")
    if st.button("Login"):
        if user == "admin" and pw == "admin":
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Wrong credentials")

if not st.session_state.logged_in:
    login()
    st.stop()

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

BACKEND_URL = "http://127.0.0.1:8000"

INDICATORS = [
    "Life expectancy at birth (years)",
    "Healthy life expectancy (HALE) at birth (years)",
    "Neonatal mortality rate (per 1000 live births)",
    "Under-five mortality rate (per 1000 live births)",
    "Maternal mortality ratio (per 100 000 live births)",
    "Adolescent birth rate (per 1000 women aged 15-19 years)",
    "Adolescent birth rate (per 1000 women aged 10-14 years)",
    "Incidence of malaria (per 1000 population at risk)",
    "Incidence of tuberculosis (per 100 000 population per year)",
    "HIV incidence (per 1000 uninfected population)",
]

def get_y_label(indicator):
    if "per 1000" in indicator:
        return "Rate (per 1,000)"
    elif "per 100 000" in indicator:
        return "Rate (per 100,000)"
    elif "years" in indicator.lower():
        return "Years"
    else:
        return "Value"

@st.cache_data
def load_csv():
    raw = pd.read_csv("WHO_Data.csv")
    raw = raw[["IndicatorName", "Location", "Year", "NumericValue"]].dropna()
    raw = raw[raw["IndicatorName"].isin(INDICATORS)]
    raw["Year"] = raw["Year"].astype(str).str.extract(r'(\d{4})')[0]
    raw["Year"] = pd.to_numeric(raw["Year"], errors="coerce")
    raw = raw.dropna(subset=["Year"])
    raw["Year"] = raw["Year"].astype(int)
    raw["NumericValue"] = pd.to_numeric(raw["NumericValue"], errors="coerce")
    return raw.dropna(subset=["NumericValue"])

def load_data():
    try:
        resp = requests.get(f"{BACKEND_URL}/data", timeout=3)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            raise ValueError("Empty")
        df = pd.DataFrame(data)
        df = df[df["IndicatorName"].isin(INDICATORS)]
        df["Year"] = df["Year"].astype(str).str.extract(r'(\d{4})')[0]
        df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
        df = df.dropna(subset=["Year"])
        df["Year"] = df["Year"].astype(int)
        df["NumericValue"] = pd.to_numeric(df["NumericValue"], errors="coerce")
        return df.dropna(subset=["NumericValue"])
    except Exception:
        return load_csv()

df_full = load_data()

st.title("WHO Health Dashboard")

st.sidebar.markdown("### Filters")
indicators = sorted(df_full["IndicatorName"].unique())
selected_indicator = st.sidebar.selectbox("Select Indicator", indicators)

st.sidebar.markdown("---")
df_export = df_full[df_full["IndicatorName"] == selected_indicator].copy()
st.sidebar.download_button(
    "Export",
    df_export.to_csv(index=False),
    "health_data.csv",
    "text/csv"
)

df = df_full[df_full["IndicatorName"] == selected_indicator].copy()
st.caption(f"Showing: {selected_indicator} | {len(df):,} rows")

df_agg = df.groupby(["Location", "Year"], as_index=False)["NumericValue"].mean()

top10 = (
    df_agg.groupby("Location")["NumericValue"]
    .mean()
    .sort_values(ascending=False)
    .head(10)
    .reset_index()
)
top10["Rank"] = range(1, 11)

y_label = get_y_label(selected_indicator)

st.subheader("Top 10 Countries by Average Value")
fig1 = px.bar(
    top10,
    x="Location", y="NumericValue", text="Rank", color="NumericValue",
    color_continuous_scale="Blues",
    title=f"Top 10 Countries — {selected_indicator}",
    labels={"NumericValue": y_label, "Location": "Country"},
)
fig1.update_traces(textposition="outside")
fig1.update_layout(
    showlegend=False,
    xaxis_tickangle=-30,
    xaxis={"categoryorder": "total descending"},
    yaxis=dict(tickformat=".2f", title=y_label)
)
st.plotly_chart(fig1, use_container_width=True)

st.subheader("Trend Over Time (Top 5 Countries)")
top5_locations = top10["Location"].head(5).tolist()
df_trend = df_agg[df_agg["Location"].isin(top5_locations)].copy()
fig2 = px.line(
    df_trend,
    x="Year", y="NumericValue", color="Location", markers=True,
    title=f"Trend — {selected_indicator} (Top 5 Countries)",
    labels={"NumericValue": y_label, "Year": "Year"},
)
fig2.update_layout(
    xaxis=dict(type="category"),
    legend_title="Country",
    yaxis=dict(tickformat=".2f", title=y_label)
)
st.plotly_chart(fig2, use_container_width=True)

st.subheader("Country Comparison — Single Year")
year_selected = st.selectbox("Select Year", sorted(df_agg["Year"].unique(), reverse=True))
df_year_top = (
    df_agg[df_agg["Year"] == year_selected]
    .groupby("Location")["NumericValue"]
    .mean()
    .sort_values(ascending=False)
    .head(8)
    .reset_index()
)
if df_year_top.empty:
    st.warning(f"No data for {year_selected}. Try a different year.")
else:
    fig3 = px.bar(
        df_year_top,
        x="Location", y="NumericValue", color="NumericValue",
        color_continuous_scale="Teal",
        title=f"Top 8 Countries in {year_selected} — {selected_indicator}",
        labels={"NumericValue": y_label, "Location": "Country"},
    )
    fig3.update_layout(
        showlegend=False,
        xaxis_tickangle=-30,
        xaxis={"categoryorder": "total descending"},
        yaxis=dict(tickformat=".2f", title=y_label)
    )
    st.plotly_chart(fig3, use_container_width=True)

st.subheader("Dataset Preview")
st.dataframe(df_agg, use_container_width=True)
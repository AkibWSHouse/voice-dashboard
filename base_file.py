import streamlit as st
import pandas as pd
import plotly.express as px
from audiorecorder import audiorecorder
import speech_recognition as sr
import tempfile
from datetime import datetime, timedelta
import dateparser  # new import

st.set_page_config(page_title="Fashion Retail Dashboard", layout="wide")
st.title("🛍️ Fashion Retail Sales Dashboard")

@st.cache_data
def load_data():
    df = pd.read_csv("C:/Users/akib.mahmood/Desktop/Fashion_Retail_Sales.csv")
    df['Date Purchase'] = pd.to_datetime(df['Date Purchase'], format="%d-%m-%Y", errors='coerce')
    df['Review Rating'] = pd.to_numeric(df['Review Rating'], errors='coerce')
    return df

df = load_data()

# --- Voice recorder + transcription ---
def get_transcribed_text():
    audio = audiorecorder("🔴 Click to record", "⏺️ Recording... Speak now!")
    if len(audio) > 0:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
            audio.export(temp_audio_file.name, format="wav")
            st.audio(temp_audio_file.name)

            recognizer = sr.Recognizer()
            with sr.AudioFile(temp_audio_file.name) as source:
                audio_data = recognizer.record(source)
                try:
                    text = recognizer.recognize_google(audio_data).lower()
                    return text
                except sr.UnknownValueError:
                    st.warning("😕 Could not understand the audio.")
                except sr.RequestError:
                    st.error("🚫 Could not connect to Google Speech API.")
    return ""

# Initialize filters in session state
if 'selected_items' not in st.session_state:
    st.session_state.selected_items = sorted(df["Item Purchased"].dropna().unique())
if 'selected_payments' not in st.session_state:
    st.session_state.selected_payments = sorted(df["Payment Method"].dropna().unique())
if 'date_range' not in st.session_state:
    st.session_state.date_range = [df["Date Purchase"].min(), df["Date Purchase"].max()]

# Sidebar UI for filters
with st.sidebar:
    st.header("🔍 Filters")

    # Voice input section
    st.subheader("🎤 Voice Filter / Command")
    recognized_text = get_transcribed_text()
    if recognized_text:
        st.info(f"Recognized: **{recognized_text}**")

        # Reset filters command
        if "reset" in recognized_text:
            st.session_state.selected_items = sorted(df["Item Purchased"].dropna().unique())
            st.session_state.selected_payments = sorted(df["Payment Method"].dropna().unique())
            st.session_state.date_range = [df["Date Purchase"].min(), df["Date Purchase"].max()]
            st.success("Filters reset!")

        # Show pie chart command (example)
        elif "pie chart" in recognized_text:
            st.session_state.show_pie = True  # Use this flag later if needed

        else:
            # Filter by Item Purchased
            items = [item for item in df["Item Purchased"].dropna().unique() if item.lower() in recognized_text]
            if items:
                st.session_state.selected_items = items
                st.success(f"Filtered items: {', '.join(items)}")

            # Filter by Payment Method
            payments = [p for p in df["Payment Method"].dropna().unique() if p.lower() in recognized_text]
            if payments:
                st.session_state.selected_payments = payments
                st.success(f"Filtered payment methods: {', '.join(payments)}")

            # Improved date parsing with dateparser and relative dates
            recognized_text_lower = recognized_text.lower()
            min_date = df["Date Purchase"].min()
            max_date = df["Date Purchase"].max()

            if "last 6 months" in recognized_text_lower:
                end_date = max_date
                start_date = end_date - timedelta(days=6*30)  # approx 6 months
                st.session_state.date_range = [start_date, end_date]
                st.success(f"Filtered date range: Last 6 months ({start_date.strftime('%d-%m-%Y')} to {end_date.strftime('%d-%m-%Y')})")

            elif "last year" in recognized_text_lower:
                end_date = max_date
                start_date = end_date - timedelta(days=365)
                st.session_state.date_range = [start_date, end_date]
                st.success(f"Filtered date range: Last year ({start_date.strftime('%d-%m-%Y')} to {end_date.strftime('%d-%m-%Y')})")

            elif "this year" in recognized_text_lower:
                now = datetime.now()
                start_date = datetime(now.year, 1, 1)
                end_date = datetime(now.year, 12, 31)
                st.session_state.date_range = [start_date, end_date]
                st.success(f"Filtered date range: This year ({start_date.strftime('%d-%m-%Y')} to {end_date.strftime('%d-%m-%Y')})")

            else:
                # Try parsing a date from the entire recognized text
                parsed_date = dateparser.parse(recognized_text_lower)
                if parsed_date:
                    # Check if user said only a year (e.g. "2023")
                    if parsed_date.month == 1 and parsed_date.day == 1 and any(str(year) in recognized_text_lower for year in range(1900, 2100)):
                        start_date = datetime(parsed_date.year, 1, 1)
                        end_date = datetime(parsed_date.year, 12, 31)
                        st.session_state.date_range = [start_date, end_date]
                        st.success(f"Filtered date range: Year {parsed_date.year}")
                    else:
                        # Single day filter
                        st.session_state.date_range = [parsed_date, parsed_date]
                        st.success(f"Filtered date: {parsed_date.strftime('%d-%m-%Y')}")

    # Show current selected filters with multiselect for manual override
    st.markdown("### 🛠 Manual Adjust Filters")
    all_items = sorted(df["Item Purchased"].dropna().unique())
    st.session_state.selected_items = st.multiselect(
        "Filter by Item Purchased", options=all_items, default=st.session_state.selected_items)

    all_payments = sorted(df["Payment Method"].dropna().unique())
    st.session_state.selected_payments = st.multiselect(
        "Filter by Payment Method", options=all_payments, default=st.session_state.selected_payments)

    st.markdown("### 📅 Date Range")
    min_date = df["Date Purchase"].min()
    max_date = df["Date Purchase"].max()

    if st.button("🧹 Reset Date Filter"):
        st.session_state.date_range = [min_date, max_date]

    st.session_state.date_range = st.date_input(
        "Select a date range", st.session_state.date_range, min_value=min_date, max_value=max_date)

# Apply filters to dataframe
df_filtered = df[
    (df["Item Purchased"].isin(st.session_state.selected_items)) &
    (df["Payment Method"].isin(st.session_state.selected_payments)) &
    (df["Date Purchase"] >= pd.to_datetime(st.session_state.date_range[0])) &
    (df["Date Purchase"] <= pd.to_datetime(st.session_state.date_range[1]))
].dropna(subset=["Purchase Amount (USD)", "Date Purchase"])

# Dashboard main area
if df_filtered.empty:
    st.warning("⚠️ No data available for the selected filters.")
else:
    st.markdown("### 📌 Key Metrics")
    total_sales = df_filtered["Purchase Amount (USD)"].sum()
    avg_rating = df_filtered["Review Rating"].mean()
    num_transactions = df_filtered.shape[0]
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("💰 Total Sales", f"${total_sales:,.2f}")
    kpi2.metric("⭐ Avg Rating", f"{avg_rating:.2f}")
    kpi3.metric("🛍️ Transactions", f"{num_transactions}")

    # Show raw data
    with st.expander("📄 View Filtered Data"):
        st.dataframe(df_filtered)

    # Visualizations
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Avg Review Ratings per Item")
        avg_rating_df = df_filtered.groupby("Item Purchased")["Review Rating"].mean().reset_index()
        fig1 = px.bar(
            avg_rating_df.sort_values("Review Rating", ascending=False),
            x="Item Purchased", y="Review Rating",
            color="Review Rating", color_continuous_scale="viridis"
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.subheader("💳 Payment Method Distribution")
        payment_counts = df_filtered["Payment Method"].value_counts().reset_index()
        payment_counts.columns = ["Payment Method", "Count"]
        fig2 = px.pie(
            payment_counts, names="Payment Method", values="Count",
            title="Payment Method Breakdown",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("📈 Total Sales Over Time")
    sales_by_date = df_filtered.groupby("Date Purchase")["Purchase Amount (USD)"].sum().reset_index()
    fig3 = px.line(
        sales_by_date, x="Date Purchase", y="Purchase Amount (USD)",
        markers=True, title="Total Sales Over Time",
        color_discrete_sequence=["steelblue"]
    )
    st.plotly_chart(fig3, use_container_width=True)

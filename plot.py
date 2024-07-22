import streamlit as st
import pandas as pd
import plotly.express as px
import country_converter as coco

st.set_page_config(layout="wide", page_title="Population Changes Dashboard")

@st.cache_data
def load_data(file):
    xlsx = pd.ExcelFile(file)
    signals_df = pd.read_excel(xlsx, 'MAU Signals')
    devices_df = pd.read_excel(xlsx, 'MAU Devices')
    return signals_df, devices_df

def preprocess_data(df):
    # Check if we have multiple months or just one
    if len(df.columns) > 2:  # More than 'Country' and one month
        df_melted = df.melt(id_vars=['Country'], var_name='Month', value_name='Value')
    else:
        df_melted = df.rename(columns={df.columns[1]: 'Value'})
        df_melted['Month'] = df.columns[1]  # Use the column name as the month
    
    # Separate global and international data
    global_data = df_melted[df_melted['Country'].isin(['International', 'Global'])]
    df_melted = df_melted[~df_melted['Country'].isin(['International', 'Global'])]
    
    # Convert country names to ISO3 codes
    cc = coco.CountryConverter()
    df_melted['iso3'] = cc.convert(df_melted['Country'], to='ISO3')
    
    # Remove rows where ISO3 conversion failed
    df_melted = df_melted.dropna(subset=['iso3'])
    
    # Ensure 'Value' column is numeric
    df_melted['Value'] = pd.to_numeric(df_melted['Value'].astype(str).str.replace(',', ''), errors='coerce')
    
    return df_melted, global_data

st.title("📊 Population Changes Dashboard")

uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx")

if uploaded_file is not None:
    signals_df, devices_df = load_data(uploaded_file)
    
    signals_melted, signals_global = preprocess_data(signals_df)
    devices_melted, devices_global = preprocess_data(devices_df)

    st.sidebar.header("📋 Controls")
    data_type = st.sidebar.radio("Select Data Type:", ("MAU Signals", "MAU Devices"))
    
    df = signals_melted if data_type == "MAU Signals" else devices_melted
    global_df = signals_global if data_type == "MAU Signals" else devices_global
    
    months = df['Month'].unique()
    if len(months) > 1:
        selected_month = st.sidebar.selectbox("Select Month:", months, index=len(months)-1)
    else:
        selected_month = months[0]
        st.info(f"Data available only for: {selected_month}")

    st.header(f"{data_type} - {selected_month}")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("🗺️ Global Distribution")
        fig_map = px.choropleth(
            df,
            locations="iso3",
            color="Value",
            hover_name="Country",
            color_continuous_scale=px.colors.sequential.Viridis,
            projection="natural earth"
        )
        fig_map.update_layout(height=500)
        st.plotly_chart(fig_map, use_container_width=True)

    with col2:
        st.subheader("📈 Top 10 Countries")
        top_10 = df.nlargest(10, 'Value')
        fig_bar = px.bar(
            top_10,
            x='Value',
            y='Country',
            orientation='h',
            color='Value',
            color_continuous_scale=px.colors.sequential.Viridis
        )
        fig_bar.update_layout(height=500)
        st.plotly_chart(fig_bar, use_container_width=True)

    if len(months) > 1:
        st.header("📉 Trends Over Time")
        countries = df['Country'].unique()
        selected_countries = st.multiselect("Select Countries for Trend Analysis:", countries, default=countries[:5])

        trend_data = df[df['Country'].isin(selected_countries)]
        fig_trend = px.line(
            trend_data,
            x='Month',
            y='Value',
            color='Country',
            line_shape='spline',
            render_mode='svg'
        )
        fig_trend.update_layout(height=500)
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("Trend analysis is not available for single-month data.")

    st.header("🔢 Raw Data (Excluding Global/International)")
    st.dataframe(df.sort_values('Value', ascending=False))

    # Global and International data analysis
    st.header("🌐 Global and International Data Analysis")
    if not global_df.empty:
        if len(months) > 1:
            fig_global = px.line(
                global_df,
                x='Month',
                y='Value',
                color='Country',
                line_shape='spline',
                render_mode='svg'
            )
            fig_global.update_layout(height=400)
            st.plotly_chart(fig_global, use_container_width=True)
        else:
            st.info("Trend analysis for Global/International data is not available for single-month data.")
        
        st.subheader("Global and International Raw Data")
        st.dataframe(global_df.sort_values('Value', ascending=False))
    else:
        st.info("No Global or International data available in the uploaded file.")

else:
    st.info("👆 Upload an Excel file to get started!")
    st.markdown("""
    The Excel file should have two sheets:
    1. MAU Signals
    2. MAU Devices
    
    Each sheet should have the following format:
    | Country | Month1 | Month2 | ... |
    |---------|--------|--------|-----|
    | CountryA| Value1 | Value2 | ... |
    | CountryB| Value1 | Value2 | ... |
    
    Note: If you only have data for one month, the format should be:
    | Country | MonthName |
    |---------|-----------|
    | CountryA| Value1    |
    | CountryB| Value2    |
    """)
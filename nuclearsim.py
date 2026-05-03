import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Grid Capacity & Dual-Reactor Model", layout="wide")

st.title("⚡ Grid Capacity & Nuclear Planning Model")
st.markdown("Model the deployment of **LINGLONG-1 SMRs** alongside **Large Scale Reactors**.")

# --- SIDEBAR: SETTINGS ---
st.sidebar.header("1. Baseline Settings")
base_capacity = st.sidebar.slider("Starting 2026 Capacity (MW)", 40000, 80000, 62000, 500)
buffer_pct = st.sidebar.slider("Peak Demand Buffer (%)", 10, 60, 39, 1) / 100.0

st.sidebar.markdown("---")
st.sidebar.header("2. Nuclear Operating Params")
capacity_factor = st.sidebar.slider(
    "Nuclear Capacity Factor (%)", 
    min_value=50, max_value=100, value=90, step=1,
    help="Nuclear plants run almost continuously. 90% is standard."
) / 100.0

st.sidebar.markdown("---")
st.sidebar.subheader("☢️ Reactor 1: SMR")
st.sidebar.markdown("* **Model:** LINGLONG-1\n* **Net Capacity:** 100 MWe")
smr_capacity = 100

st.sidebar.subheader("☢️ Reactor 2: Large PWR")
large_reactor_name = st.sidebar.text_input("Reactor Name", "Hualong One")
large_capacity = st.sidebar.number_input("Net Capacity (MWe)", value=1200, step=100)

# --- DATA SETUP ---
years = list(range(2026, 2037))
default_energy = [
    267629, 274843, 281699, 288344, 291519, 
    298101, 305141, 312214, 319522, 323605, 326119 
]

if 'df_model_v3' not in st.session_state:
    st.session_state.df_model_v3 = pd.DataFrame({
        "Year": years,
        "Forecasted Energy (GWh)": default_energy,
        "Linglong Units Added": [0] * len(years),
        "Large Reactor Added": [0] * len(years)
    })

# --- MAIN LAYOUT ---
# Adjusted ratio from [1.2, 2] to [1.4, 2] to give the table slightly more room
col1, col2 = st.columns([1.4, 2])

with col1:
    st.subheader("📊 Input Deployment Plan")
    st.markdown("Add units per year to see the grid impact.")
    
    # Editable DataFrame with SHORT headers to prevent horizontal scrolling
    edited_df = st.data_editor(
        st.session_state.df_model_v3,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Year": st.column_config.NumberColumn(
                "Year", disabled=True, format="%d", width="small"
            ),
            "Forecasted Energy (GWh)": st.column_config.NumberColumn(
                "Demand (GWh)", step=1000, width="medium"
            ),
            "Linglong Units Added": st.column_config.NumberColumn(
                "SMRs (+)", 
                help="Number of 100 MW Linglong-1 units added this year", 
                min_value=0, step=1, width="small"
            ),
            "Large Reactor Added": st.column_config.NumberColumn(
                "Large (+)", 
                help=f"Number of {large_capacity} MW {large_reactor_name} units added this year", 
                min_value=0, step=1, width="small"
            )
        }
    )

# --- CORE CALCULATIONS ---
df = edited_df.copy()

# Demand
df["Average Demand (MW)"] = (df["Forecasted Energy (GWh)"] * 1000) / 8760
df["Peak Demand (MW)"] = df["Average Demand (MW)"] * (1 + buffer_pct)

# Cumulative Plants
df["Cum_Linglong"] = df["Linglong Units Added"].cumsum()
df["Cum_Large"] = df["Large Reactor Added"].cumsum()

# Capacities (MW)
df["Linglong_MW"] = df["Cum_Linglong"] * smr_capacity
df["Large_MW"] = df["Cum_Large"] * large_capacity
df["Total_Nuclear_MW"] = df["Linglong_MW"] + df["Large_MW"]
df["Base_MW"] = base_capacity
df["Total_System_MW"] = df["Base_MW"] + df["Total_Nuclear_MW"]
df["Gap_MW"] = df["Total_System_MW"] - df["Peak Demand (MW)"]

# Generation (GWh) -> MW * 8760 * CF / 1000
df["Linglong_GWh"] = (df["Linglong_MW"] * 8760 * capacity_factor) / 1000
df["Large_GWh"] = (df["Large_MW"] * 8760 * capacity_factor) / 1000
df["Total_Nuclear_GWh"] = df["Linglong_GWh"] + df["Large_GWh"]

# Percentages
df["Nuclear_Pct_Energy"] = (df["Total_Nuclear_GWh"] / df["Forecasted Energy (GWh)"]) * 100
df["Nuclear_Pct_Peak"] = (df["Total_Nuclear_MW"] / df["Peak Demand (MW)"]) * 100

with col2:
    st.subheader("📈 Capacity vs. Demand Projection")
    fig1 = go.Figure()

    # Base Capacity (Bottom Layer)
    fig1.add_trace(go.Scatter(
        x=df["Year"], y=df["Base_MW"],
        mode='lines', name='Base Grid Capacity',
        stackgroup='capacity', fillcolor='rgba(46, 204, 113, 0.2)', line=dict(color='#2ecc71', width=1),
        hovertemplate="Base Capacity: %{y:,.0f} MW<extra></extra>"
    ))

    # Large Reactor Capacity (Middle Layer)
    cd_large = list(zip(df["Cum_Large"], df["Large_GWh"]))
    fig1.add_trace(go.Scatter(
        x=df["Year"], y=df["Large_MW"],
        mode='lines', name=f'{large_reactor_name}',
        stackgroup='capacity', fillcolor='rgba(52, 152, 219, 0.7)', line=dict(color='#3498db', width=1),
        customdata=cd_large,
        hovertemplate=(
            f"<b>{large_reactor_name} Contribution:</b><br>"
            "Active Plants: %{customdata[0]} units<br>"
            "Capacity Share: %{y:,.0f} MW<br>"
            "Power Generated: %{customdata[1]:,.0f} GWh<extra></extra>"
        )
    ))

    # Linglong Capacity (Top Layer)
    cd_linglong = list(zip(df["Cum_Linglong"], df["Linglong_GWh"]))
    fig1.add_trace(go.Scatter(
        x=df["Year"], y=df["Linglong_MW"],
        mode='lines', name='Linglong-1 SMR',
        stackgroup='capacity', fillcolor='rgba(243, 156, 18, 0.8)', line=dict(color='#f39c12', width=1),
        customdata=cd_linglong,
        hovertemplate=(
            "<b>Linglong-1 Contribution:</b><br>"
            "Active Plants: %{customdata[0]} units<br>"
            "Capacity Share: %{y:,.0f} MW<br>"
            "Power Generated: %{customdata[1]:,.0f} GWh<extra></extra>"
        )
    ))

    # Peak Demand Line
    fig1.add_trace(go.Scatter(
        x=df["Year"], y=df["Peak Demand (MW)"],
        mode='lines+markers', name='Forecasted Peak Demand',
        line=dict(color='#e74c3c', width=3),
        hovertemplate="Peak Demand: %{y:,.0f} MW<extra></extra>"
    ))

    # Gap/Surplus Bars at the bottom
    colors = ['#9b59b6' if val >= 0 else '#e74c3c' for val in df["Gap_MW"]]
    fig1.add_trace(go.Bar(
        x=df["Year"], y=df["Gap_MW"],
        name='Capacity Gap', marker_color=colors, opacity=0.4,
        hovertemplate="Gap: %{y:,.0f} MW<extra></extra>"
    ))

    fig1.update_layout(
        height=450, margin=dict(l=20, r=20, t=10, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis=dict(title='Megawatts (MW)', range=[0, max(df["Total_System_MW"].max() + 5000, 80000)]),
        hovermode="x unified"
    )
    st.plotly_chart(fig1, use_container_width=True)

    # --- CHART 2: NUCLEAR PERCENTAGES ---
    st.subheader("⚛️ Total Nuclear Contribution (%)")
    fig2 = go.Figure()

    fig2.add_trace(go.Scatter(
        x=df["Year"], y=df["Nuclear_Pct_Energy"],
        mode='lines+markers', name='% of Total Energy (GWh)',
        line=dict(color='#8e44ad', width=3),
        hovertemplate="Energy Met: %{y:.1f}%<extra></extra>"
    ))
    
    fig2.add_trace(go.Scatter(
        x=df["Year"], y=df["Nuclear_Pct_Peak"],
        mode='lines+markers', name='% of Peak Demand (MW)',
        line=dict(color='#2980b9', width=3, dash='dot'),
        hovertemplate="Peak Demand Met: %{y:.1f}%<extra></extra>"
    ))

    fig2.update_layout(
        height=250, margin=dict(l=20, r=20, t=10, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis=dict(title='Percentage (%)', ticksuffix="%"),
        hovermode="x unified"
    )
    st.plotly_chart(fig2, use_container_width=True)
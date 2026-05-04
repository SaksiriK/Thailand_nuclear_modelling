
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ==========================================
# --- INITIALIZATION FUNCTIONS ---
# ==========================================

def initialize_pdp_data():
    """
    Initialize standard PDP data based on the Draft PDP 2024 baseline.
    The draft points to ~54,546 MW Peak Demand and ~112,391 MW Contracted Capacity by 2037.
    We extrapolate these figures out to 2056.
    """
    years = list(range(2026, 2057)) # Extended to 2056
    
    # 2026 starting point based on Draft PDP 2024 trajectory
    base_peak_mw = 36000 
    base_capacity_mw = 56000
    
    # Growth rates assumed from the 2024-2037 trends
    demand_growth_rate = 1.025 # 2.5% annual growth
    capacity_growth_rate = 1.018 # Slower capacity growth to show emerging gap
    
    data = []
    for i, year in enumerate(years):
        current_peak = base_peak_mw * (demand_growth_rate ** i)
        current_capacity = base_capacity_mw * (capacity_growth_rate ** i)
        
        data.append({
            "Year": year,
            "PDP Contracted Peak (MW)": round(current_peak, 2),
            "Contracted Capacity (MW)": round(current_capacity, 2)
        })
        
    return pd.DataFrame(data)

def initialize_deployment_data():
    """
    Initialize empty deployment schedule for Chinese reactor models.
    Updated with official CNNC Export Technologies.
    """
    years = list(range(2026, 2057))
    df = pd.DataFrame({"Year": years})
    df["HPR1000 (1200 MW)"] = 0
    df["ACP100 (100 MW)"] = 0
    df["ACP600 (600 MW)"] = 0
    df["HTR (210 MW)"] = 0
    return df

# ==========================================
# --- A) LOGIN COMPONENT ---
# ==========================================

def check_password():
    """Returns `True` if the user had the correct password."""
    def password_entered():
        if st.session_state["password"] == "nuclear2026":
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input(
            "Enter password to access the model:", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        st.text_input(
            "Enter password to access the model:", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        return True

# ==========================================
# --- B) TAB DEFINITIONS ---
# ==========================================

def render_tab_intro():
    st.header("Model Overview & Strategic Context")
    st.markdown("""
    ### Project Background
    This tool models Thailand's power grid capacity deficit through **2056** and simulates how deploying advanced Chinese nuclear reactors can close the gap. 
    
    **Why the Draft PDP 2024?**
    Unlike older versions, the **Draft Power Development Plan (PDP) 2024** explicitly identifies **Small Modular Reactors (SMRs)** as a necessary modern technology to hit Thailand's 2050 Carbon Neutrality goals. It adjusts for post-COVID economic realities, noting a projected peak demand of ~54,546 MW and total system capacity of ~112,391 MW by 2037. This model uses these realistic baseline trends and extrapolates them to 2056.
    
    **Why Chinese Technology?**
    China is rapidly pushing the frontiers of nuclear technology. They are moving heavily towards **modular construction** to drastically reduce build times and capital costs. 
    *   As of 2026, China operates 58 reactors with 33 more under construction.
    *   They are pioneers in Generation-IV technologies, such as the TMSR-LF1 (thorium molten salt) and the HTGR hybrid models.
    *   For more information on their recent breakthroughs, read [China's Advanced Nuclear Efforts Are Pushing Frontiers](https://www.powermag.com/chinas-advanced-nuclear-efforts-are-pushing-frontiers/).
    *   For more information on Chinese nuclear power plant types for export, read [China National Nuclear Corporation Overseas Ltd. (CNOS)](https://en.cnos.cn/czec_en/index/index.html).

    **Deployment Timelines & Lead Times**
    When planning your reactor deployment in the model, keep in mind the typical construction periods ("First Concrete to Grid Connection") for these specific CNNC models:
    *   **ACP100 (Linglong One SMR):** ~48 months (4 years) 
    *   **HPR1000 (Hualong One PWR):** 56 - 60 months (~4.5 to 5 years)
    *   **ACP600 (Medium PWR):** 50 - 54 months (~4.5 years)
    *   **HTR (High-Temperature Gas-Cooled Reactor):** 50 - 60 months (~4.5 to 5 years)
    
    > 💡 **Strategic Planning Note:** The times above represent *physical construction* only. An additional **2 to 3 years** should be factored into your timeline *prior* to construction for site licensing, environmental impact assessments (EIA), and public hearings in Thailand. 
    
    Use the tabs above to adjust the baseline demand, plan your reactor deployment, and view the resulting capacity projections.
    """)

def render_tab_pdp():
    st.header("Baseline Power Development Plan Data")
    st.markdown("Modify the expected **PDP Contracted Peak (MW)** below. The model automatically recalculates Average Demand (via 39% buffer) and Energy Requirements on the Dashboard.")
    
    st.session_state.pdp_df = st.data_editor(
        st.session_state.pdp_df,
        width="content", 
        hide_index=True,
        num_rows="fixed",
        column_config={
            "Year": st.column_config.NumberColumn(width="small", format="%d", disabled=True),
            "PDP Contracted Peak (MW)": st.column_config.NumberColumn(width="medium", format="%.1f"),
            "Contracted Capacity (MW)": st.column_config.NumberColumn(width="medium", format="%.1f")
        }
    )

def render_tab_deployment():
    st.header("Nuclear Deployment Plan")
    st.markdown("""
    Enter the number of **units** coming online in a given year. 
    Hover over the column headers to see the specific technology type and MW rating.
    """)
    
    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("🚀 Load Suggested Plan to Reach 50% Nuclear"):
            try:
                scenario_df = pd.read_csv(r"deployment_plan_50.csv")
                st.session_state.deployment_df = scenario_df
                st.success("50% Nuclear Scenario Loaded! Check Tab D for results.")
                st.rerun() 
            except FileNotFoundError:
                st.error("Could not find the file at E:\\thailand_energy_model\\data\\deployment_plan_50.csv")
    
    st.divider() 

    # Layout for Tab C: Data Editor on left, Graph on right
    col_table, col_chart = st.columns([1, 1.8])

    with col_table:
        st.session_state.deployment_df = st.data_editor(
            st.session_state.deployment_df,
            width="content", 
            hide_index=True,
            num_rows="fixed",
            column_config={
                "Year": st.column_config.NumberColumn(width="small", format="%d", disabled=True),
                "HPR1000 (1200 MW)": st.column_config.NumberColumn("HPR1000 (+)", help="Large Generation III+ PWR - 1200 MW", width="small"),
                "ACP100 (100 MW)": st.column_config.NumberColumn("ACP100 (+)", help="Small Modular Reactor (SMR) - 100 MW", width="small"),
                "ACP600 (600 MW)": st.column_config.NumberColumn("ACP600 (+)", help="Medium PWR - 600 MW", width="small"),
                "HTR (210 MW)": st.column_config.NumberColumn("HTR (+)", help="High-Temperature Gas-Cooled Reactor - 210 MW", width="small")
            }
        )

    with col_chart:
        # Convert units added in each year into Capacity (MW)
        deploy_df = st.session_state.deployment_df
        hpr_mw = deploy_df["HPR1000 (1200 MW)"] * 1200
        acp100_mw = deploy_df["ACP100 (100 MW)"] * 100
        acp600_mw = deploy_df["ACP600 (600 MW)"] * 600
        htr_mw = deploy_df["HTR (210 MW)"] * 210
        
        fig_added = go.Figure()
        
        fig_added.add_trace(go.Bar(x=deploy_df["Year"], y=hpr_mw, name='HPR1000 (1200 MW)', marker_color='#1f77b4'))
        fig_added.add_trace(go.Bar(x=deploy_df["Year"], y=acp100_mw, name='ACP100 (100 MW)', marker_color='#ff7f0e'))
        fig_added.add_trace(go.Bar(x=deploy_df["Year"], y=acp600_mw, name='ACP600 (600 MW)', marker_color='#2ca02c'))
        fig_added.add_trace(go.Bar(x=deploy_df["Year"], y=htr_mw, name='HTR (210 MW)', marker_color='#d62728'))
        
        fig_added.update_layout(
            barmode='stack', 
            title="Annual Nuclear Capacity Added (MW)",
            xaxis_title="Year", 
            yaxis_title="Capacity Added (MW)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), 
            hovermode="x unified", 
            height=500,
            margin=dict(l=0, r=0, t=40, b=0)
        )
        st.plotly_chart(fig_added, width="stretch")

def render_tab_dashboard():
    st.header("Capacity vs. Demand Projection")
    
    calc_df = st.session_state.pdp_df.copy()
    
    # Base computations
    calc_df["Average Demand (MW)"] = calc_df["PDP Contracted Peak (MW)"] / 1.39
    calc_df["Annual Energy Demand (GWh)"] = (calc_df["Average Demand (MW)"] * 8760) / 1000
    
    # Nuclear computations
    deploy_df = st.session_state.deployment_df.copy()
    calc_df["HPR1000 Capacity"] = deploy_df["HPR1000 (1200 MW)"].cumsum() * 1200
    calc_df["ACP100 Capacity"] = deploy_df["ACP100 (100 MW)"].cumsum() * 100
    calc_df["ACP600 Capacity"] = deploy_df["ACP600 (600 MW)"].cumsum() * 600
    calc_df["HTR Capacity"] = deploy_df["HTR (210 MW)"].cumsum() * 210
    
    calc_df["Total Nuclear Added (MW)"] = (
        calc_df["HPR1000 Capacity"] + 
        calc_df["ACP100 Capacity"] + 
        calc_df["ACP600 Capacity"] + 
        calc_df["HTR Capacity"]
    )
    calc_df["Total Grid Capacity (MW)"] = calc_df["Contracted Capacity (MW)"] + calc_df["Total Nuclear Added (MW)"]
    
    calc_df["Nuclear Percentage (%)"] = np.where(
        calc_df["Total Grid Capacity (MW)"] > 0,
        (calc_df["Total Nuclear Added (MW)"] / calc_df["Total Grid Capacity (MW)"]) * 100,
        0
    )
    
    # --- GAP COMPUTATION ---
    fixed_2026_cap = calc_df.loc[calc_df["Year"] == 2026, "Contracted Capacity (MW)"].values[0]
    calc_df["Current 2026 Capacity (MW)"] = fixed_2026_cap
    calc_df["Capacity Gap (MW)"] = calc_df["PDP Contracted Peak (MW)"] - calc_df["Current 2026 Capacity (MW)"]
    calc_df["Capacity Gap (MW)"] = calc_df["Capacity Gap (MW)"].clip(lower=0) 
    
    # --- CARBON SAVINGS COMPUTATION ---
    # Assuming standard Thailand Grid Emission Factor: ~0.43 kg CO2 per kWh = 430 tonnes CO2 per GWh
    # Annual Nuclear Energy (GWh) = Total Nuclear Added (MW) * 8760 hours / 1000 * 0.9 (Capacity Factor)
    calc_df["Nuclear Energy Generated (GWh)"] = (calc_df["Total Nuclear Added (MW)"] * 8760 * 0.9) / 1000
    calc_df["Annual CO2 Saved (Million Tonnes)"] = (calc_df["Nuclear Energy Generated (GWh)"] * 430) / 1000000
    calc_df["Cumulative CO2 Saved (Million Tonnes)"] = calc_df["Annual CO2 Saved (Million Tonnes)"].cumsum()
    
    crossover_years = calc_df[calc_df["Nuclear Percentage (%)"] >= 50]["Year"].values
    crossover_year = crossover_years[0] if len(crossover_years) > 0 else None
    
    # Grid Metrics
    st.subheader("Grid Integration Metrics")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(label="Total Nuclear Deployed by 2056", value=f"{calc_df['Total Nuclear Added (MW)'].iloc[-1]:,.0f} MW")
    col2.metric(label="Final Nuclear Share (2056)", value=f"{calc_df['Nuclear Percentage (%)'].iloc[-1]:.1f}%")
    
    if crossover_year:
        col3.metric(label="🎯 50% Milestone Reached In:", value=str(crossover_year))
    else:
        col3.metric(label="🎯 50% Milestone:", value="Not Reached")
        
    col4.metric(label="Max Capacity Gap (in 2056)", value=f"{calc_df['Capacity Gap (MW)'].iloc[-1]:,.0f} MW", delta="- Needs to be filled", delta_color="inverse")

    # Carbon Metrics
    st.subheader("Environmental Impact Metrics")
    c_col1, c_col2, c_col3 = st.columns(3)
    c_col1.metric(label="Total Clean Energy Generated (2056)", value=f"{calc_df['Nuclear Energy Generated (GWh)'].iloc[-1]:,.0f} GWh/yr")
    c_col2.metric(label="Annual CO2 Saved (in 2056)", value=f"{calc_df['Annual CO2 Saved (Million Tonnes)'].iloc[-1]:.2f} M Tonnes")
    c_col3.metric(label="Cumulative CO2 Saved (2026-2056)", value=f"{calc_df['Cumulative CO2 Saved (Million Tonnes)'].iloc[-1]:,.1f} M Tonnes", delta="Net Reduction", delta_color="normal")

    st.divider()

    # ==========================================
    # --- PRIMARY CHART ---
    # ==========================================
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=calc_df["Year"], y=calc_df["PDP Contracted Peak (MW)"],
        mode='lines', name='Contracted Peak Demand (MW)',
        line=dict(color='red', width=3, dash='dash')
    ))
    
    fig.add_trace(go.Scatter(
        x=calc_df["Year"], y=calc_df["Average Demand (MW)"],
        mode='lines', name='Calculated Average Demand (MW)',
        line=dict(color='orange', width=2, dash='dot')
    ))

    fig.add_trace(go.Bar(
        x=calc_df["Year"], y=calc_df["Contracted Capacity (MW)"],
        name='Baseline Contracted Capacity', marker_color='#d3d3d3', hovertemplate="Baseline: %{y:,.0f} MW<extra></extra>"
    ))

    fig.add_trace(go.Bar(x=calc_df["Year"], y=calc_df["HPR1000 Capacity"], name='HPR1000 (1200 MW)', marker_color='#1f77b4'))
    fig.add_trace(go.Bar(x=calc_df["Year"], y=calc_df["ACP100 Capacity"], name='ACP100 (100 MW)', marker_color='#ff7f0e'))
    fig.add_trace(go.Bar(x=calc_df["Year"], y=calc_df["ACP600 Capacity"], name='ACP600 (600 MW)', marker_color='#2ca02c'))
    fig.add_trace(go.Bar(x=calc_df["Year"], y=calc_df["HTR Capacity"], name='HTR (210 MW)', marker_color='#d62728'))

    fig.add_trace(go.Scatter(
        x=calc_df["Year"], y=calc_df["Nuclear Percentage (%)"],
        mode='lines+markers+text', name='Nuclear Share (%)', yaxis='y2', 
        text=calc_df["Nuclear Percentage (%)"].round(1).astype(str) + "%", 
        textposition="top center", textfont=dict(color="#4B0082", size=10, weight="bold"),
        marker=dict(size=6, color='#4B0082'), line=dict(color='#4B0082', width=2, dash='dot'),
        hovertemplate="Year: %{x}<br>Nuclear Share: %{y:.1f}%<extra></extra>"
    ))

    fig.update_layout(
        barmode='stack', title="Primary View: Closing the Capacity Gap with Nuclear",
        xaxis_title="Year", yaxis_title="Capacity / Demand (MW)",
        yaxis2=dict(
            title=dict(text="Nuclear Share (%)", font=dict(color="#4B0082")), 
            tickfont=dict(color="#4B0082"), 
            overlaying="y", side="right", range=[0, 100], showgrid=False
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), hovermode="x unified", height=600
    )
    st.plotly_chart(fig, width="stretch")
    
    st.divider()
    
    # ==========================================
    # --- SECONDARY CHART (CARBON & GAP) ---
    # ==========================================
    col_gap, col_carbon = st.columns(2)

    with col_gap:
        st.subheader("The Expanding Capacity Gap")
        st.markdown("If no new power is built after 2026.")
        fig_gap = go.Figure()

        fig_gap.add_trace(go.Scatter(
            x=calc_df["Year"], y=calc_df["Current 2026 Capacity (MW)"],
            mode='lines', name='Current 2026 Capacity',
            line=dict(color='gray', width=3)
        ))

        fig_gap.add_trace(go.Scatter(
            x=calc_df["Year"], y=calc_df["PDP Contracted Peak (MW)"],
            mode='lines', name='Projected Peak Demand',
            line=dict(color='red', width=3),
            fill='tonexty', fillcolor='rgba(255, 0, 0, 0.2)' 
        ))

        fig_gap.update_layout(
            xaxis_title="Year", yaxis_title="Megawatts (MW)",
            hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02),
            height=400, margin=dict(l=0, r=0, t=30, b=0)
        )
        st.plotly_chart(fig_gap, width="stretch")

    with col_carbon:
        st.subheader("Cumulative Carbon Footprint Reduction")
        st.markdown("Assuming ~0.43 kg CO2/kWh displaced by clean nuclear.")
        fig_carbon = go.Figure()

        fig_carbon.add_trace(go.Scatter(
            x=calc_df["Year"], y=calc_df["Cumulative CO2 Saved (Million Tonnes)"],
            mode='lines', name='Cumulative CO2 Saved',
            line=dict(color='#2ca02c', width=4),
            fill='tozeroy', fillcolor='rgba(44, 160, 44, 0.2)'
        ))

        fig_carbon.update_layout(
            xaxis_title="Year", yaxis_title="Million Tonnes CO2",
            hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02),
            height=400, margin=dict(l=0, r=0, t=30, b=0)
        )
        st.plotly_chart(fig_carbon, width="stretch")

    # ==========================================
    # --- DATA TABLE ---
    # ==========================================
    with st.expander("View Complete Year-by-Year Data Table"):
        display_cols = [
            "Year", "PDP Contracted Peak (MW)", "Current 2026 Capacity (MW)", 
            "Total Grid Capacity (MW)", "Total Nuclear Added (MW)", 
            "Nuclear Percentage (%)", "Cumulative CO2 Saved (Million Tonnes)"
        ]
        
        st.dataframe(calc_df[display_cols].style.format({
            "PDP Contracted Peak (MW)": "{:,.0f}",
            "Current 2026 Capacity (MW)": "{:,.0f}",
            "Total Grid Capacity (MW)": "{:,.0f}",
            "Total Nuclear Added (MW)": "{:,.0f}",
            "Nuclear Percentage (%)": "{:.1f}%",
            "Cumulative CO2 Saved (Million Tonnes)": "{:,.2f}"
        }), width="stretch")

# ==========================================
# --- C) MAIN EXECUTION ---
# ==========================================

def main():
    st.set_page_config(page_title="Thailand Nuclear Deployment Model", layout="wide")
    
    if not check_password():
        st.stop()
        
    # --- AGGRESSIVE CACHE FIX ---
    if "pdp_df" in st.session_state:
        if "PDP Contracted Peak (MW)" not in st.session_state.pdp_df.columns or "Contracted Capacity (MW)" not in st.session_state.pdp_df.columns:
            del st.session_state["pdp_df"]
            
    if "pdp_df" not in st.session_state:
        st.session_state.pdp_df = initialize_pdp_data()

    if "deployment_df" not in st.session_state:
        st.session_state.deployment_df = initialize_deployment_data()
        
    st.title("🇹🇭 Thailand Grid Capacity & Nuclear Deployment Model")

    tab1, tab2, tab3, tab4 = st.tabs([
        "a) Model Explanation", 
        "b) Demand Table (PDP 2024 Draft)", 
        "c) Nuclear Input Deployment", 
        "d) Capacity vs. Demand Projection"
    ])
    
    with tab1:
        render_tab_intro()
    with tab2:
        render_tab_pdp()
    with tab3:
        render_tab_deployment()
    with tab4:
        render_tab_dashboard()

if __name__ == "__main__":
    main()

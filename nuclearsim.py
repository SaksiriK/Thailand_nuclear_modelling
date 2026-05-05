import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ==========================================
# --- INITIALIZATION FUNCTIONS ---
# ==========================================

def initialize_pdp_data():
    """
    Initializes ONLY the Demand forecast. 
    We assume no new non-nuclear plants are built.
    """
    years = list(range(2026, 2057)) # Extended to 2056
    
    base_peak_mw = 36000 
    demand_growth_rate = 1.025 # 2.5% annual growth
    
    data = []
    for i, year in enumerate(years):
        current_peak = base_peak_mw * (demand_growth_rate ** i)
        
        data.append({
            "Year": year,
            "Peak Demand (MW)": round(current_peak, 2)
        })
        
    return pd.DataFrame(data)

def initialize_deployment_data():
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
    def password_entered():
        if st.session_state["password"] == "nuclear2026":
            st.session_state["password_correct"] = True
            del st.session_state["password"]  
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input(
            "**🔒 Enter password to access the model:**", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        st.text_input(
            "**🔒 Enter password to access the model:**", type="password", on_change=password_entered, key="password"
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
    
    :red[Use the tabs above to adjust the baseline demand, plan your reactor deployment, and view the resulting capacity projections.]
    """)

def render_tab_pdp():
    st.header("Demand Forecast vs. Frozen Capacity Gap")
    st.markdown("Assume no new non-nuclear plants are built after 2026. Modify your **Peak Demand (MW)** forecast on the left, and watch the Capacity Gap expand on the right.")
    
    # User input for the frozen 2026 capacity
    if "base_capacity" not in st.session_state:
        st.session_state.base_capacity = 56000.0
        
    st.session_state.base_capacity = st.number_input(
        "⚡ Current Grid Capacity in 2026 (MW) - Assuming NO new plants are built:",
        value=st.session_state.base_capacity,
        step=1000.0,
        format="%.1f"
    )
    
    st.divider()
    
    col1, col2 = st.columns([1, 2.5])
    
    with col1:
        st.subheader("1. Projected Peak Demand")
        st.session_state.pdp_df = st.data_editor(
            st.session_state.pdp_df,
            width="stretch",
            hide_index=True,
            num_rows="fixed",
            column_config={
                "Year": st.column_config.NumberColumn(format="%d", disabled=True),
                "Peak Demand (MW)": st.column_config.NumberColumn(format="%.1f")
            }
        )
        
    with col2:
        st.subheader("2. The Expanding Capacity Gap")
        
        gap_df = st.session_state.pdp_df.copy()
        
        # Safety for cache
        if "Peak Demand (MW)" not in gap_df.columns and "PDP Contracted Peak (MW)" in gap_df.columns:
            gap_df = gap_df.rename(columns={"PDP Contracted Peak (MW)": "Peak Demand (MW)"})
            
        gap_df["Frozen Capacity"] = st.session_state.base_capacity
        gap_df["Gap"] = (gap_df["Peak Demand (MW)"] - gap_df["Frozen Capacity"]).clip(lower=0)
        
        fig_gap = go.Figure()

        fig_gap.add_trace(go.Scatter(
            x=gap_df["Year"], y=gap_df["Frozen Capacity"],
            mode='lines', name='Frozen 2026 Capacity',
            line=dict(color='gray', width=3)
        ))

        fig_gap.add_trace(go.Scatter(
            x=gap_df["Year"], y=gap_df["Peak Demand (MW)"],
            mode='lines', name='Projected Peak Demand',
            line=dict(color='red', width=3),
            fill='tonexty', fillcolor='rgba(255, 0, 0, 0.2)' 
        ))

        fig_gap.add_trace(go.Scatter(
            x=gap_df["Year"], y=gap_df["Gap"],
            mode='lines+markers', name='Calculated Capacity Gap (MW)',
            line=dict(color='orange', width=2, dash='dashdot'),
            hovertemplate="Unmet Gap: %{y:,.0f} MW<extra></extra>"
        ))

        fig_gap.update_layout(
            xaxis_title="Year",
            yaxis_title="Megawatts (MW)",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=500,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        st.plotly_chart(fig_gap, width="stretch")

def render_tab_deployment():
    st.header("Nuclear Deployment Plan")
    st.markdown("""
    Enter the number of **units** coming online in a given year. 
    Hover over the column headers to see the specific technology type and MW rating.
    """)
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("Load a Pre-built Scenario:")
        
        scenario_choice = st.selectbox(
            "Select Deployment Strategy:",
            ["-- Select a Scenario --", "Aggressive Mix (50% Target)", "SMR Focus (Small Reactors)", "Heavy Baseload (Large Reactors)"]
        )
        
        if st.button("🚀 Load Scenario"):
            file_map = {
                "Aggressive Mix (50% Target)": "deployment_plan_50.csv",
                "SMR Focus (Small Reactors)": "deployment_plan_smr.csv",
                "Heavy Baseload (Large Reactors)": "deployment_plan_baseload.csv"
            }
            
            if scenario_choice in file_map:
                try:
                    file_name = file_map[scenario_choice]
                    scenario_df = pd.read_csv(file_name)
                    st.session_state.deployment_df = scenario_df
                    st.success(f"'{scenario_choice}' Loaded! Check Tab D for results.")
                    st.rerun() 
                except FileNotFoundError:
                    st.error(f"Could not find '{file_name}'. Make sure you uploaded it to GitHub!")
            else:
                st.warning("Please select a scenario from the dropdown first.")
    
    st.divider() 

    # Split into Table and Chart columns
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
    st.header("Total Grid Solution & Environmental Impact")
    
    calc_df = st.session_state.pdp_df.copy()
    
    # Force rename if the browser cache is holding onto the old name
    if "Peak Demand (MW)" not in calc_df.columns and "PDP Contracted Peak (MW)" in calc_df.columns:
        calc_df = calc_df.rename(columns={"PDP Contracted Peak (MW)": "Peak Demand (MW)"})
    
    # Bring in the frozen capacity from Tab B
    if "base_capacity" not in st.session_state:
        st.session_state.base_capacity = 56000.0
    calc_df["Baseline Capacity (MW)"] = st.session_state.base_capacity
    
    # Base computations
    calc_df["Average Demand (MW)"] = calc_df["Peak Demand (MW)"] / 1.39
    calc_df["Annual Energy Demand (GWh)"] = (calc_df["Average Demand (MW)"] * 8760) / 1000
    calc_df["Capacity Gap (MW)"] = (calc_df["Peak Demand (MW)"] - calc_df["Baseline Capacity (MW)"]).clip(lower=0) 
    
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
    
    # Total Grid is now just the flat 2026 capacity + Nuclear Additions
    calc_df["Total Grid Capacity (MW)"] = calc_df["Baseline Capacity (MW)"] + calc_df["Total Nuclear Added (MW)"]
    
    # Percentage computation
    calc_df["Nuclear Percentage (%)"] = np.where(
        calc_df["Total Grid Capacity (MW)"] > 0,
        (calc_df["Total Nuclear Added (MW)"] / calc_df["Total Grid Capacity (MW)"]) * 100,
        0
    )
    
    # --- CARBON SAVINGS COMPUTATION ---
    # Assuming standard Thailand Grid Emission Factor: ~0.43 kg CO2 per kWh = 430 tonnes CO2 per GWh
    # Annual Nuclear Energy (GWh) = Total Nuclear Added (MW) * 8760 hours / 1000 * 0.9 (Capacity Factor)
    calc_df["Nuclear Energy Generated (GWh)"] = (calc_df["Total Nuclear Added (MW)"] * 8760 * 0.9) / 1000
    calc_df["Annual CO2 Saved (Million Tonnes)"] = (calc_df["Nuclear Energy Generated (GWh)"] * 430) / 1000000
    calc_df["Cumulative CO2 Saved (Million Tonnes)"] = calc_df["Annual CO2 Saved (Million Tonnes)"].cumsum()
    
    crossover_years = calc_df[calc_df["Nuclear Percentage (%)"] >= 50]["Year"].values
    crossover_year = crossover_years[0] if len(crossover_years) > 0 else None
    
    # --- METRICS ---
    st.subheader("Grid Integration Metrics")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(label="Total Nuclear Deployed", value=f"{calc_df['Total Nuclear Added (MW)'].iloc[-1]:,.0f} MW")
    col2.metric(label="Final Nuclear Share", value=f"{calc_df['Nuclear Percentage (%)'].iloc[-1]:.1f}%")
    
    if crossover_year:
        col3.metric(label="🎯 50% Milestone:", value=str(crossover_year))
    else:
        col3.metric(label="🎯 50% Milestone:", value="Not Reached")
        
    col4.metric(label="Max Capacity Gap (in 2056)", value=f"{calc_df['Capacity Gap (MW)'].iloc[-1]:,.0f} MW")

    st.subheader("Environmental Impact Metrics")
    c_col1, c_col2, c_col3 = st.columns(3)
    c_col1.metric(label="Total Clean Energy Generated (2056)", value=f"{calc_df['Nuclear Energy Generated (GWh)'].iloc[-1]:,.0f} GWh/yr")
    c_col2.metric(label="Annual CO2 Saved (in 2056)", value=f"{calc_df['Annual CO2 Saved (Million Tonnes)'].iloc[-1]:.2f} M Tonnes")
    c_col3.metric(label="Cumulative CO2 Saved (2026-2056)", value=f"{calc_df['Cumulative CO2 Saved (Million Tonnes)'].iloc[-1]:,.1f} M Tonnes", delta="Net Reduction", delta_color="normal")

    st.divider()

    # ==========================================
    # --- PRIMARY CHART (Grid Capacity) ---
    # ==========================================
    fig = go.Figure()

    # Peak Demand Line
    fig.add_trace(go.Scatter(
        x=calc_df["Year"], y=calc_df["Peak Demand (MW)"],
        mode='lines', name='Projected Peak Demand (MW)',
        line=dict(color='red', width=3, dash='dash')
    ))
    
    # Baseline Capacity (Now purely a flat block)
    fig.add_trace(go.Bar(
        x=calc_df["Year"], y=calc_df["Baseline Capacity (MW)"],
        name='Frozen 2026 Grid Capacity', marker_color='#d3d3d3', hovertemplate="Baseline: %{y:,.0f} MW<extra></extra>"
    ))

    # Stacked Nuclear Capacities
    fig.add_trace(go.Bar(x=calc_df["Year"], y=calc_df["HPR1000 Capacity"], name='HPR1000 (1200 MW)', marker_color='#1f77b4'))
    fig.add_trace(go.Bar(x=calc_df["Year"], y=calc_df["ACP100 Capacity"], name='ACP100 (100 MW)', marker_color='#ff7f0e'))
    fig.add_trace(go.Bar(x=calc_df["Year"], y=calc_df["ACP600 Capacity"], name='ACP600 (600 MW)', marker_color='#2ca02c'))
    fig.add_trace(go.Bar(x=calc_df["Year"], y=calc_df["HTR Capacity"], name='HTR (210 MW)', marker_color='#d62728'))

    # Percentage Line
    fig.add_trace(go.Scatter(
        x=calc_df["Year"], y=calc_df["Nuclear Percentage (%)"],
        mode='lines+markers+text', name='Nuclear Share (%)', yaxis='y2', 
        text=calc_df["Nuclear Percentage (%)"].round(1).astype(str) + "%", 
        textposition="top center", textfont=dict(color="#4B0082", size=10, weight="bold"),
        marker=dict(size=6, color='#4B0082'), line=dict(color='#4B0082', width=2, dash='dot'),
        hovertemplate="Year: %{x}<br>Nuclear Share: %{y:.1f}%<extra></extra>"
    ))

    fig.update_layout(
        barmode='stack', title="Filling the Capacity Gap with Nuclear Power",
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
    # --- SECONDARY CHART (CARBON FOOTPRINT) ---
    # ==========================================
    st.subheader("Cumulative Carbon Footprint Reduction")
    st.markdown("Assuming ~0.43 kg CO2/kWh displaced by clean nuclear energy generation.")
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
            "Year", "Peak Demand (MW)", "Baseline Capacity (MW)", 
            "Capacity Gap (MW)", "Total Grid Capacity (MW)", 
            "Total Nuclear Added (MW)", "Nuclear Percentage (%)",
            "Cumulative CO2 Saved (Million Tonnes)"
        ]
        
        st.dataframe(calc_df[display_cols].style.format({
            "Peak Demand (MW)": "{:,.0f}",
            "Baseline Capacity (MW)": "{:,.0f}",
            "Capacity Gap (MW)": "{:,.0f}",
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
    
    # --- TITLE PLACED HERE (BOLDED) ---
    st.title("**🇹🇭 Thailand Grid Capacity & Nuclear Deployment Model**")
    
    if not check_password():
        st.stop()
        
    # --- SAFETY CATCH FOR CACHE ---
    if "pdp_df" not in st.session_state:
        st.session_state.pdp_df = initialize_pdp_data()
    else:
        if "PDP Contracted Peak (MW)" in st.session_state.pdp_df.columns:
            st.session_state.pdp_df.rename(columns={"PDP Contracted Peak (MW)": "Peak Demand (MW)"}, inplace=True)
        if "Contracted Capacity (MW)" in st.session_state.pdp_df.columns:
            st.session_state.pdp_df = st.session_state.pdp_df.drop(columns=["Contracted Capacity (MW)"])

    if "deployment_df" not in st.session_state:
        st.session_state.deployment_df = initialize_deployment_data()

    tab1, tab2, tab3, tab4 = st.tabs([
        "a) Model Explanation", 
        "b) Demand Forecast & Gap Analysis", 
        "c) Nuclear Input Deployment", 
        "d) Dashboard: Grid Solution"
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
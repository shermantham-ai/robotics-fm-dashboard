import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Robotics FM Financial Dashboard", page_icon="🤖", layout="wide")

st.title("🤖 Robotics FM - Financial Impact Dashboard")
st.markdown("**Estimate costs & ROI for both clients and service providers**")

st.sidebar.header("📊 Scenario Setup")
view_mode = st.sidebar.radio("Perspective", ["🏢 Client (Building Owner)", "🏭 Service Provider"], index=0)

def calc_client(sqft, days, wage, robot, pricing):
    specs = {"Small Vacuum": (15000, 18000, 550, 0.7), "Medium Scrubber": (30000, 35000, 850, 0.75), "Large Industrial": (60000, 65000, 1200, 0.8)}
    cov, capex_p, raas_p, eff = specs[robot]
    robots = max(1, int(sqft / (cov * eff)))
    weekly_hrs = (sqft / 1000) * 1.0 * days
    annual_labor = weekly_hrs * (wage * 1.4) * 52
    replaceable = annual_labor * 0.65
    if pricing == "RaaS": annual_robot = raas_p * robots * 12; capex = 0
    else: annual_robot = capex_p * robots * 0.15; capex = capex_p * robots
    savings = replaceable - annual_robot
    payback = (capex / savings * 12) if savings > 0 and pricing == "CapEx" else (1 if savings > 0 else float('inf'))
    return {"robots": robots, "labor": annual_labor, "robot": annual_robot, "savings": savings, "capex": capex, "payback": payback, "y1": savings, "y2": savings*1.04, "y3": savings*1.08}

def calc_provider(units, robot, model, yrs):
    specs = {"Small Vacuum": (12000, 550, 50), "Medium Scrubber": (24000, 850, 80), "Large Industrial": (45000, 1200, 120)}
    cogs, raas, maint = specs[robot]
    if model == "RaaS":
        rev = raas * units * 12 * yrs
        costs = cogs * units + (maint * units * 12 * yrs)
        margin = ((raas - maint) / raas) * 100
    else:
        rev = (cogs * 1.3 * units) + (maint * units * 12 * 3)
        costs = cogs * units
        margin = ((cogs * 1.3 - cogs) / (cogs * 1.3)) * 100
    return {"rev": rev, "costs": costs, "profit": rev - costs, "margin": margin, "cogs": cogs, "maint": maint}

if view_mode == "🏢 Client (Building Owner)":
    st.header("Client Financial Analysis")
    c1, c2 = st.columns(2)
    with c1:
        sqft = st.number_input("Building Size (sq ft)", 10000, 1000000, 100000, 10000)
        days = st.number_input("Cleaning Days/Week", 1, 7, 5)
        wage = st.number_input("Hourly Wage ($)", 10.0, 40.0, 17.27, 0.5)
    with c2:
        robot = st.selectbox("Robot Type", ["Small Vacuum", "Medium Scrubber", "Large Industrial"])
        pricing = st.radio("Pricing Model", ["RaaS", "CapEx"])
    
    m = calc_client(sqft, days, wage, robot, pricing)
    st.markdown("### 💰 Key Metrics")
    cols = st.columns(4)
    cols[0].metric("Robots Needed", m["robots"])
    cols[1].metric("Annual Labor Cost", f"${m['labor']:,.0f}")
    cols[2].metric("Annual Robot Cost", f"${m['robot']:,.0f}")
    cols[3].metric("Annual Savings", f"${m['savings']:,.0f}", delta_color="normal" if m["savings"]>0 else "inverse")
    
    if m["payback"] != float("inf"):
        st.success(f"✅ Payback: {m['payback']:.1f} months")
    else:
        st.warning("⚠️ Negative ROI with current inputs")
    
    fig = go.Figure()
    fig.add_trace(go.Bar(x=["Year 1", "Year 2", "Year 3"], y=[m["y1"], m["y2"], m["y3"]], marker_color=["#00cc96" if s>0 else "#ef553b" for s in [m["y1"], m["y2"], m["y3"]]]))
    fig.update_layout(title="3-Year Savings Projection", height=300)
    st.plotly_chart(fig, use_container_width=True)

else:
    st.header("Service Provider Financial Analysis")
    c1, c2 = st.columns(2)
    with c1:
        units = st.number_input("Robots Deployed", 1, 1000, 50, 10)
        robot = st.selectbox("Robot Type", ["Small Vacuum", "Medium Scrubber", "Large Industrial"])
        yrs = st.slider("Contract Length (Years)", 1, 5, 3)
    with c2:
        model = st.radio("Business Model", ["RaaS", "CapEx"])
    
    m = calc_provider(units, robot, model, yrs)
    st.markdown("### 💰 Key Metrics")
    cols = st.columns(4)
    cols[0].metric("Total Contract Value", f"${m['rev']:,.0f}")
    cols[1].metric("Total Costs", f"${m['costs']:,.0f}")
    cols[2].metric("Gross Profit", f"${m['profit']:,.0f}")
    cols[3].metric("Gross Margin", f"{m['margin']:.1f}%")
    
    months = list(range(1, yrs*12+1))
    cum_rev = [m["rev"]/len(months)*i for i in months]
    cum_cost = [m["costs"]/len(months)*i for i in months]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=months, y=cum_rev, name="Cumulative Revenue", line=dict(color="#00cc96")))
    fig.add_trace(go.Scatter(x=months, y=cum_cost, name="Cumulative Costs", line=dict(color="#ef553b")))
    fig.update_layout(title=f"{yrs}-Year Cash Flow", height=350)
    st.plotly_chart(fig, use_container_width=True)

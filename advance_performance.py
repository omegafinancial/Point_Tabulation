import streamlit as st
import pandas as pd
import plotly.express as px

# ---- STREAMLIT PAGE CONFIG ----
st.set_page_config(
    page_title="Employee Performance Dashboard",
    layout="wide",
    page_icon="📊"
)

# ---- STYLING FOR BETTER UI ----
st.markdown("""
    <style>
        .big-font { font-size:20px !important; }
        .st-emotion-cache-16txtl3 { padding: 1rem !important; }
        .st-emotion-cache-1outpf7 { border: 1px solid #ddd; border-radius: 10px; padding: 10px; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# ---- DASHBOARD TITLE ----
st.title("📊 Employee Performance Analysis Dashboard")

# ---- FILE UPLOAD FEATURE ----
uploaded_file = st.file_uploader("📂 Upload a CSV file", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip()
    df["Sum of Amount ( Actual Value )(In INR)"] = pd.to_numeric(df["Sum of Amount ( Actual Value )(In INR)"], errors="coerce")

    st.success("✅ File uploaded successfully!")

    # ---- SIDEBAR FILTER ----
    st.sidebar.header("🔍 Filter Data")
    owners = df["Owner"].dropna().unique()
    selected_owners = st.sidebar.multiselect("Select Owners", options=owners, default=owners)

    filtered_df = df[df["Owner"].isin(selected_owners)] if selected_owners else df

    # ---- BUSINESS POINTS CALCULATION ----
    points_rules = {
            "MUTUAL FUND ( DEBT)": 6 / 100000,
            "MUTUAL FUND ( EQUITY )": 30 / 100000,
            "MUTUAL FUND SIP ( DEBT )": 120 / 100000,
            "MUTUAL FUND SIP (EQUITY)": 800 / 100000,
            "PORTFOLIO MANAGEMENT SERVICES": 50 / 100000,
            "LIFE INSURANCE": 400 / 100000,
            "GENERAL INSURANCE": 0 / 100000,
            "HEALTH INSURANCE": 350 / 100000,
            "ARN TRANSFER-EQUITY": 0.35*30 / 100000,
            "ARN TRANSFER-DEBT": 0.35*6 / 100000
        }

    filtered_df["Business Points"] = filtered_df["Product or Service"].map(points_rules) * filtered_df["Sum of Amount ( Actual Value )(In INR)"]
    business_points_data = filtered_df.groupby("Owner")["Business Points"].sum().reset_index().fillna(0)
    business_points_data["Rank"] = business_points_data["Business Points"].rank(method='dense', ascending=False).astype(int)
    business_points_data = business_points_data.sort_values(by="Rank")

    # ---- TOTAL BUSINESS POINTS & NET AMOUNT ----
    total_business_points = business_points_data["Business Points"].sum()
    total_net_amount = filtered_df["Sum of Amount ( Actual Value )(In INR)"].sum()

    # ---- DISPLAY SELECTED OWNER(S) RANK POSITION ----
    rank_info = []
    for owner in selected_owners:
        owner_rank_row = business_points_data[business_points_data["Owner"] == owner]
        if not owner_rank_row.empty:
            rank_val = int(owner_rank_row["Rank"].values[0])
            rank_info.append(f"{owner}: Rank {rank_val}")
    rank_display = " | ".join(rank_info) if rank_info else "No rank available"

    st.markdown(f"""
        <div style="display: flex; justify-content: space-between; 
                    align-items: center; padding: 20px; margin-bottom: 20px; 
                    background-color: #f1f3f6; border-radius: 15px; 
                    border: 2px solid #ccc; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); 
                    font-size: 24px; font-weight: bold; color: #333;">
            <div>🏆 <span style="color:#ff5733;">Rank Position:</span> {rank_display}</div>
            <div>💼 Total Business Points: <span style="color:#007bff;">{total_business_points:,.2f}</span></div>
            <div>💰 Net Amount: <span style="color:#28a745;">₹{total_net_amount:,.2f}</span></div>
        </div>
    """, unsafe_allow_html=True)

    # ---- AMOUNT CATEGORIZATION ----
    amount_categories = filtered_df.groupby("Product or Service")["Sum of Amount ( Actual Value )(In INR)"].sum().reset_index()
    st.write(f"### 💰 Amount Categorization")
    st.dataframe(amount_categories)

    # ---- CHARTS WITHOUT X-AXIS LABELS ----
    fig1 = px.bar(amount_categories, x="Product or Service", y="Sum of Amount ( Actual Value )(In INR)",
                  title="💰 Amount Categorization", text="Sum of Amount ( Actual Value )(In INR)")
    fig1.update_traces(texttemplate='%{text:.2s}', textposition='outside')
    fig1.update_layout(xaxis_title="", xaxis_showticklabels=False)

    fig2 = px.bar(business_points_data, x="Owner", y="Business Points",
                  title="🏆 Business Points Ranking", text="Business Points", color="Owner")
    fig2.update_traces(texttemplate='%{text:.2s}', textposition='outside')
    fig2.update_layout(xaxis_title="", xaxis_showticklabels=False)

    col1, col2 = st.columns(2)
    col1.plotly_chart(fig1)
    col2.plotly_chart(fig2)

    # ---- AUM & SIP CATEGORIZATION ----
    def categorize_aum_sip(data):
        aum_df = data[data["Product or Service"].str.contains("EQUITY|DEBT|PMS|PORTFOLIO MANAGEMENT SERVICES|ARN TRANSFER-EQUITY|ARN TRANSFER-DEBT", case=False, na=False) &
                      ~data["Product or Service"].str.contains("SIP", case=False, na=False)]
        sip_df = data[data["Product or Service"].str.contains("SIP", case=False, na=False)]
        aum = aum_df.groupby("Owner")["Sum of Amount ( Actual Value )(In INR)"].sum().reset_index().rename(
            columns={"Sum of Amount ( Actual Value )(In INR)": "AUM Amount"})
        sip = sip_df.groupby("Owner")["Sum of Amount ( Actual Value )(In INR)"].sum().reset_index().rename(
            columns={"Sum of Amount ( Actual Value )(In INR)": "SIP Amount"})
        return pd.merge(aum, sip, on="Owner", how="outer").fillna(0)

    aum_sip_data = categorize_aum_sip(filtered_df)
    st.write("### 💰 AUM & SIP Distribution")
    st.dataframe(aum_sip_data)

    fig3 = px.bar(aum_sip_data, x="Owner", y=["AUM Amount", "SIP Amount"],
                  title="💰 AUM & SIP Distribution", barmode="group", text_auto=True)
    fig3.update_layout(xaxis_title="", xaxis_showticklabels=False)
    st.plotly_chart(fig3)

    # ---- PERFORMANCE METRICS ----
    def calculate_performance_metrics(data):
        perf = data.groupby("Owner").agg({
            "Sum of Amount ( Actual Value )(In INR)": "sum",
            "Number of CLIENT TYPE": "sum",
            "Number of meetings": "sum",
            "Activation": "sum",
            "Specific Task": "sum"
        }).reset_index()
        deals = data.groupby("Owner").size().reset_index(name="Number of Deals")
        return pd.merge(perf, deals, on="Owner", how="left")

    performance_metrics_data = calculate_performance_metrics(filtered_df)
    st.write("### 📈 Performance Metrics")
    st.dataframe(performance_metrics_data)

    # ---- FINAL STRUCTURED MATRIX ----
    def create_final_matrix(aum_sip_data, perf_data, bp_data):
        final = pd.merge(aum_sip_data, perf_data, on="Owner", how="left")
        final = pd.merge(final, bp_data, on="Owner", how="left").fillna(0)
        final = final.rename(columns={
            "Owner": "CANDIDATE",
            "Number of meetings": "Client Meeting",
            "Number of CLIENT TYPE": "New Client Addition",
            "AUM Amount": "AUM",
            "SIP Amount": "SIP"
        })
        final.insert(0, "SL NO", range(1, len(final) + 1))
        return final

    final_matrix = create_final_matrix(aum_sip_data, performance_metrics_data, business_points_data)
    st.write("### 📊 Final Structured Matrix")
    st.dataframe(final_matrix)

else:
    st.warning("⚠ Please upload a CSV file to proceed.")
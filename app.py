import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Lender Portfolio Review", layout="wide")

schools = pd.read_csv("schools.csv")
candidates = pd.read_csv("candidates.csv")

st.sidebar.title("Filters")
regions = ["All"] + sorted(schools["region"].unique().tolist())
region = st.sidebar.selectbox("Region", regions)
tiers = ["All"] + sorted(schools["risk_tier"].unique().tolist())
tier = st.sidebar.selectbox("Risk Tier", tiers)

filtered = schools.copy()
if region != "All":
    filtered = filtered[filtered["region"] == region]
if tier != "All":
    filtered = filtered[filtered["risk_tier"] == tier]

school_names = ["All"] + sorted(filtered["school_name"].tolist())
school_filter = st.sidebar.selectbox("School", school_names)
if school_filter != "All":
    filtered = filtered[filtered["school_name"] == school_filter]

st.title("Lender Portfolio Review")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Approved Schools", int((schools["lender_status"] == "Approved").sum()))
c2.metric("Under Review", int((schools["lender_status"] == "Under Review").sum()))
c3.metric("Avg Quality Score", f"{schools['quality_score'].mean():.1f}")
c4.metric("Avg Confidence Score", f"{schools['confidence_score'].mean():.1f}")

st.markdown("---")
st.subheader("School Overview")

display_cols = ["school_name", "region", "risk_tier", "lender_status",
                "quality_score", "confidence_score", "completion_rate", "withdrawal_rate"]

def color_status(val):
    colors = {"Approved": "background-color:#d4edda", "Under Review": "background-color:#fff3cd",
               "Suspended": "background-color:#f8d7da"}
    return colors.get(val, "")

def color_tier(val):
    colors = {"Low": "background-color:#d4edda", "Medium": "background-color:#fff3cd",
               "High": "background-color:#f8d7da"}
    return colors.get(val, "")

styled = (
    filtered[display_cols]
    .rename(columns={"school_name": "School", "region": "Region", "risk_tier": "Risk Tier",
                     "lender_status": "Status", "quality_score": "Quality",
                     "confidence_score": "Confidence", "completion_rate": "Completion",
                     "withdrawal_rate": "Withdrawal"})
    .style.applymap(color_status, subset=["Status"])
    .applymap(color_tier, subset=["Risk Tier"])
    .format({"Completion": "{:.0%}", "Withdrawal": "{:.0%}"})
)
st.dataframe(styled, use_container_width=True, hide_index=True)

st.markdown("---")
st.subheader("Quality vs. Confidence")
fig = px.scatter(
    filtered, x="quality_score", y="confidence_score",
    color="risk_tier", hover_name="school_name",
    color_discrete_map={"Low": "#2ecc71", "Medium": "#f39c12", "High": "#e74c3c"},
    labels={"quality_score": "Quality Score", "confidence_score": "Confidence Score", "risk_tier": "Risk Tier"},
    height=350
)
fig.update_traces(marker=dict(size=10))
fig.update_layout(margin=dict(t=20, b=20))
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.subheader("School Detail")

detail_options = filtered["school_name"].tolist()
if not detail_options:
    st.info("No schools match the current filters.")
else:
    selected_school_name = st.selectbox("Select a school", detail_options, key="detail_school")
    row = schools[schools["school_name"] == selected_school_name].iloc[0]

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**School:** {row['school_name']}")
        st.markdown(f"**Region:** {row['region']}")
        st.markdown(f"**Lender Status:** {row['lender_status']}")
        st.markdown(f"**Risk Tier:** {row['risk_tier']}")
    with col2:
        st.markdown(f"**Quality Score:** {row['quality_score']}")
        st.markdown(f"**Confidence Score:** {row['confidence_score']}")
        st.markdown(f"**Completion Rate:** {row['completion_rate']:.0%}")
        st.markdown(f"**Withdrawal Rate:** {row['withdrawal_rate']:.0%}")

    col3, col4 = st.columns(2)
    with col3:
        st.markdown(f"**Avg Attendance:** {row['avg_attendance']:.0%}")
        st.markdown(f"**Stalled %:** {row['stalled_pct']:.0%}")
    with col4:
        st.markdown(f"**Data Freshness (days):** {row['freshness_days']}")
        st.markdown(f"**Open Issues:** {row['open_issues']}")

    issue_data = {"Metric": ["Data Freshness (days)", "Open Issues", "Stalled Learners"],
                  "Value": [row["freshness_days"], row["open_issues"], f"{row['stalled_pct']:.0%}"]}
    st.table(pd.DataFrame(issue_data))

    st.info(f"**AI Summary:** {row['ai_summary']}")

    st.markdown("---")
    st.subheader("Candidate Review")

    school_candidates = candidates[candidates["school_id"] == row["school_id"]]
    if school_candidates.empty:
        st.write("No candidates found for this school.")
    else:
        cand_names = school_candidates["candidate_name"].tolist()
        selected_cand_name = st.selectbox("Select a candidate", cand_names)
        cand = school_candidates[school_candidates["candidate_name"] == selected_cand_name].iloc[0]

        col5, col6 = st.columns(2)
        with col5:
            st.markdown(f"**Name:** {cand['candidate_name']}")
            st.markdown(f"**Program Stage:** {cand['program_stage']}")
            st.markdown(f"**Attendance Consistency:** {cand['attendance_consistency']}")
            st.markdown(f"**Training Hours:** {cand['training_hours']}")
        with col6:
            st.markdown(f"**Days Since Last Activity:** {cand['days_since_last_activity']}")
            st.markdown(f"**Credit Band:** {cand['credit_band']}")
            st.markdown(f"**Requested Amount:** ${cand['requested_amount']:,}")
            if cand["data_flag"] != "None":
                st.markdown(f"**Data Flag:** ⚠️ {cand['data_flag']}")

        decision = cand["recommended_decision"]
        badge_color = {"Approve": "🟢", "Review": "🟡", "Hold": "🔴"}.get(decision, "⚪")
        st.markdown(f"### {badge_color} Recommended Decision: **{decision}**")
        st.markdown(f"> {cand['decision_reason']}")

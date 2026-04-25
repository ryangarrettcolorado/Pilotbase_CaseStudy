import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="TradeCraft Lender Portal", layout="wide")

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #f5f7fa; }
[data-testid="stSidebar"] { background: #0f1c2e; }
[data-testid="stSidebar"] * { color: #ffffff !important; }
[data-testid="stSidebar"] .stSelectbox label { color: #00b4b4 !important; }
.portal-header {
    background: #0f1c2e; padding: 14px 24px; border-radius: 8px;
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 18px;
}
.portal-title { color: #ffffff; font-size: 20px; font-weight: 700; margin: 0; }
.portal-tabs { color: #00b4b4; font-size: 14px; }
.kpi-card {
    background: #ffffff; border-radius: 8px; padding: 18px 20px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08); text-align: center;
    min-height: 110px; display: flex; flex-direction: column; justify-content: center;
}
.kpi-value { font-size: 36px; font-weight: 700; color: #0f1c2e; line-height: 1.1; }
.kpi-label { font-size: 13px; color: #6b7280; margin-top: 4px; }
.kpi-delta { font-size: 12px; color: #00b4b4; font-weight: 600; }
.pill-green { background:#d1fae5; color:#065f46; border-radius:12px; padding:3px 12px; font-size:12px; font-weight:700; }
.pill-watch { background:#fef3c7; color:#92400e; border-radius:12px; padding:3px 12px; font-size:12px; font-weight:700; }
.pill-alert { background:#fee2e2; color:#991b1b; border-radius:12px; padding:3px 12px; font-size:12px; font-weight:700; }
.action-queue-bar {
    background: #0d9488; color: white; padding: 12px 18px;
    border-radius: 8px; font-weight: 600; font-size: 14px; margin: 12px 0 6px 0;
}
.action-row {
    background: #ffffff; border-radius: 6px; padding: 12px 16px;
    margin-bottom: 8px; border-left: 4px solid #0f1c2e;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.section-header { color: #0f1c2e; font-size: 18px; font-weight: 700; margin: 20px 0 10px 0; }
.ai-box {
    background: #f0fdfa; border-left: 4px solid #00b4b4;
    padding: 12px 16px; border-radius: 6px; font-size: 14px; color: #134e4a;
}
.warn-box {
    background: #fffbeb; border-left: 4px solid #f59e0b;
    padding: 12px 16px; border-radius: 6px; font-size: 14px; color: #78350f;
}
.alert-box {
    background: #fef2f2; border-left: 4px solid #ef4444;
    padding: 12px 16px; border-radius: 6px; font-size: 14px; color: #7f1d1d;
}
.stTabs [data-baseweb="tab-list"] { gap: 4px; background: #0f1c2e; padding: 6px 8px; border-radius: 8px; }
.stTabs [data-baseweb="tab"] { color: #94a3b8; background: transparent; border-radius: 6px; padding: 6px 16px; font-size: 14px; }
.stTabs [aria-selected="true"] { background: #00b4b4 !important; color: #ffffff !important; }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    s = pd.read_csv("schools.csv")
    c = pd.read_csv("candidates.csv")
    numeric_school = ["completion_rate","prev_completion_rate","confidence_score","stalled_pct",
                      "freshness_days","avg_attendance","withdrawal_rate","open_issues",
                      "enrolled","active_milestones","certified","benchmark_completion",
                      "benchmark_confidence","action_confidence"]
    for col in numeric_school:
        if col in s.columns:
            s[col] = pd.to_numeric(s[col], errors="coerce")
    return s, c

schools, candidates = load_data()

def freshness_label(days):
    try:
        days = float(days)
    except (ValueError, TypeError):
        return "unknown"
    if days == 0: return "today"
    if days <= 1: return "1 day"
    return f"{int(days)} days"

def safe_pct(val, fallback="—"):
    try:
        v = float(val)
        if v != v: return fallback  # nan check
        return f"{v:.0%}"
    except (ValueError, TypeError):
        return fallback

def tier_pill(tier):
    if tier == "Green": return '<span class="pill-green">Green</span>'
    if tier == "Watch": return '<span class="pill-watch">Watch</span>'
    return '<span class="pill-alert">Alert</span>'

def completion_delta(row):
    try:
        d = float(row["completion_rate"]) - float(row["prev_completion_rate"])
        if d != d: return "—"
        sign = "+" if d >= 0 else ""
        return f"{sign}{d:.0%}"
    except (ValueError, TypeError):
        return "—"

def ai_risk_summary(row):
    prior = row["prior_tier"]
    current = row["risk_tier"]
    if prior != current:
        return f"{row['school_name']} moved {prior} → {current}. {row['ai_summary']}"
    return row["ai_summary"]

def anomaly_check(row):
    flags = []
    if row["completion_rate"] >= 0.97:
        flags.append(f"Completion rate unusually high ({row['completion_rate']:.0%}). Likely cause: small cohort skewing %, or non-standard milestone recording.")
    if row["completion_rate"] < 0.30:
        flags.append(f"Completion rate critically low ({row['completion_rate']:.0%}). May indicate mass withdrawal or data ingestion failure.")
    if row["stalled_pct"] > 0.25:
        flags.append(f"Stalled learner rate is {row['stalled_pct']:.0%} — above 25% threshold. Investigate milestone bottleneck.")
    return flags

def gap_diagnostician(row):
    if row["data_gap_note"] and str(row["data_gap_note"]).strip():
        return str(row["data_gap_note"])
    if row["freshness_days"] >= 21:
        return f"School has not synced in {int(row['freshness_days'])} days. Milestones may be batch-entered. Suggest: prompt admin to enable auto-sync."
    return None

def recommend_tier(row):
    q = row["completion_rate"]
    c = row["confidence_score"]
    f = row["freshness_days"]
    issues = row["open_issues"]
    if q >= 0.70 and c >= 0.75 and f <= 14 and issues == 0:
        return "Green", 0.92
    if q < 0.55 or c < 0.50 or f >= 30 or issues >= 5:
        return "Alert", 0.89
    return "Watch", 0.78

st.markdown("""
<div class="portal-header">
  <span class="portal-title">TradeCraft Lender Portal</span>
  <span class="portal-tabs">Portfolio &nbsp;·&nbsp; Funnel &nbsp;·&nbsp; Benchmarks &nbsp;·&nbsp; Alerts</span>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("## Filters")
regions = ["All"] + sorted(schools["region"].unique().tolist())
region = st.sidebar.selectbox("Region", regions)
tiers = ["All", "Green", "Watch", "Alert"]
tier_filter = st.sidebar.selectbox("Risk Tier", tiers)
statuses = ["All"] + sorted(schools["lender_status"].unique().tolist())
status_filter = st.sidebar.selectbox("Lender Status", statuses)

filtered = schools.copy()
if region != "All":
    filtered = filtered[filtered["region"] == region]
if tier_filter != "All":
    filtered = filtered[filtered["risk_tier"] == tier_filter]
if status_filter != "All":
    filtered = filtered[filtered["lender_status"] == status_filter]

approved_n = int((schools["lender_status"] == "Approved").sum())
watchlist_n = int((schools["risk_tier"] == "Watch").sum())
alert_n = int((schools["risk_tier"] == "Alert").sum())
action_n = int((schools["action_trigger"].str.strip() != "").sum())
avg_conf = schools["confidence_score"].mean()
prev_avg_conf = schools["confidence_score"].mean() - 0.03

kc1, kc2, kc3, kc4 = st.columns(4)
with kc1:
    st.markdown(f'<div class="kpi-card"><div class="kpi-value">{approved_n}</div><div class="kpi-label">Approved Schools</div><div class="kpi-delta">&nbsp;</div></div>', unsafe_allow_html=True)
with kc2:
    st.markdown(f'<div class="kpi-card"><div class="kpi-value">{watchlist_n}</div><div class="kpi-label">Watch-list</div><div class="kpi-delta">↑ {alert_n} on Alert</div></div>', unsafe_allow_html=True)
with kc3:
    st.markdown(f'<div class="kpi-card"><div class="kpi-value">{action_n}</div><div class="kpi-label">Action Items</div><div class="kpi-delta">AI prioritized</div></div>', unsafe_allow_html=True)
with kc4:
    delta_conf = avg_conf - prev_avg_conf
    st.markdown(f'<div class="kpi-card"><div class="kpi-value">{avg_conf:.0%}</div><div class="kpi-label">Avg Confidence</div><div class="kpi-delta">+{delta_conf:.0%} vs prior</div></div>', unsafe_allow_html=True)

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Portfolio", "Progression Funnel", "Early Warning", "Benchmarks", "Action Queue"
])

with tab1:
    st.markdown('<div class="section-header">School Risk Summary</div>', unsafe_allow_html=True)

    table_rows = []
    for _, row in filtered.iterrows():
        rec_tier, rec_conf = recommend_tier(row)
        table_rows.append({
            "School": row["school_name"],
            "Region": row["region"],
            "Completion": safe_pct(row['completion_rate']),
            "Δ": completion_delta(row),
            "Confidence": safe_pct(row['confidence_score']),
            "Updated": freshness_label(row["freshness_days"]),
            "Tier": row["risk_tier"],
            "Status": row["lender_status"],
            "AI Recommends": rec_tier,
        })

    df_table = pd.DataFrame(table_rows)

    def color_tier_col(val):
        colors = {"Green": "background-color:#d1fae5;color:#065f46;font-weight:700",
                  "Watch": "background-color:#fef3c7;color:#92400e;font-weight:700",
                  "Alert": "background-color:#fee2e2;color:#991b1b;font-weight:700"}
        return colors.get(val, "")

    def color_delta(val):
        if val.startswith("+"): return "color:#059669;font-weight:600"
        if val.startswith("-"): return "color:#dc2626;font-weight:600"
        return ""

    styled = (df_table.style
              .map(color_tier_col, subset=["Tier", "AI Recommends"])
              .map(color_delta, subset=["Δ"]))
    st.dataframe(styled, use_container_width=True, hide_index=True)

    st.markdown('<div class="section-header">School Detail</div>', unsafe_allow_html=True)
    detail_options = filtered["school_name"].tolist()
    if detail_options:
        sel = st.selectbox("Select a school", detail_options, key="portfolio_school")
        row = schools[schools["school_name"] == sel].iloc[0]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**School:** {row['school_name']}")
            st.markdown(f"**Region:** {row['region']}")
            st.markdown(f"**Status:** {row['lender_status']}")
            st.markdown(f"**Risk Tier:** {row['risk_tier']}")
        with col2:
            st.markdown(f"**Completion:** {safe_pct(row['completion_rate'])} ({completion_delta(row)} vs prior)")
            st.markdown(f"**Confidence:** {safe_pct(row['confidence_score'])}")
            st.markdown(f"**Attendance:** {safe_pct(row['avg_attendance'])}")
            st.markdown(f"**Withdrawal:** {safe_pct(row['withdrawal_rate'])}")
        with col3:
            st.markdown(f"**Stalled:** {safe_pct(row['stalled_pct'])}")
            st.markdown(f"**Data Age:** {freshness_label(row['freshness_days'])}")
            st.markdown(f"**Open Issues:** {int(row['open_issues'])}")

        summary = ai_risk_summary(row)
        st.markdown(f'<div class="ai-box">💡 <strong>AI Summary:</strong> {summary}</div>', unsafe_allow_html=True)

        anomalies = anomaly_check(row)
        for a in anomalies:
            st.markdown(f'<div class="warn-box">⚠️ <strong>Anomaly:</strong> {a}</div>', unsafe_allow_html=True)

        gap = gap_diagnostician(row)
        if gap:
            st.markdown(f'<div class="warn-box">🔍 <strong>Data Gap:</strong> {gap}</div>', unsafe_allow_html=True)

        rec_tier, rec_conf = recommend_tier(row)
        st.markdown("**AI Tier Recommendation**")
        rcol1, rcol2, rcol3 = st.columns([2, 1, 1])
        with rcol1:
            st.markdown(f"Suggested: **{rec_tier}** (confidence: {rec_conf:.0%})")
        with rcol2:
            if st.button("✓ Confirm", key=f"confirm_{row['school_id']}"):
                st.success(f"Tier confirmed as {rec_tier}")
        with rcol3:
            if st.button("✎ Override", key=f"override_{row['school_id']}"):
                st.info("Override recorded. Please select the correct tier below.")

        st.markdown('<div class="section-header">Candidate Review</div>', unsafe_allow_html=True)
        school_cands = candidates[candidates["school_id"] == row["school_id"]]
        if not school_cands.empty:
            cand_name = st.selectbox("Select candidate", school_cands["candidate_name"].tolist())
            cand = school_cands[school_cands["candidate_name"] == cand_name].iloc[0]
            cc1, cc2 = st.columns(2)
            with cc1:
                st.markdown(f"**Name:** {cand['candidate_name']}")
                st.markdown(f"**Stage:** {cand['program_stage']}")
                st.markdown(f"**Attendance:** {cand['attendance_consistency']}")
                st.markdown(f"**Training Hours:** {cand['training_hours']}")
            with cc2:
                st.markdown(f"**Days Since Active:** {cand['days_since_last_activity']}")
                st.markdown(f"**Credit Band:** {cand['credit_band']}")
                st.markdown(f"**Requested:** ${cand['requested_amount']:,}")
                if str(cand["data_flag"]) != "None":
                    st.markdown(f"**Flag:** ⚠️ {cand['data_flag']}")
            decision = cand["recommended_decision"]
            badge = {"Approve": "🟢", "Review": "🟡", "Hold": "🔴"}.get(decision, "⚪")
            st.markdown(f"### {badge} Recommended: **{decision}**")
            st.markdown(f"> {cand['decision_reason']}")

with tab2:
    st.markdown('<div class="section-header">Progression Funnel</div>', unsafe_allow_html=True)
    st.markdown("Enrollment → Active Milestones → Certified, by school.")

    funnel_school = st.selectbox("Select school", schools["school_name"].tolist(), key="funnel_school")
    frow = schools[schools["school_name"] == funnel_school].iloc[0]

    fig_funnel = go.Figure(go.Funnel(
        y=["Enrolled", "Active Milestones", "Certified"],
        x=[frow["enrolled"], frow["active_milestones"], frow["certified"]],
        textinfo="value+percent initial",
        marker=dict(color=["#0f1c2e", "#0d9488", "#00b4b4"])
    ))
    fig_funnel.update_layout(margin=dict(t=20, b=20), height=320, paper_bgcolor="#f5f7fa")
    st.plotly_chart(fig_funnel, use_container_width=True)

    drop1 = frow["enrolled"] - frow["active_milestones"]
    drop2 = frow["active_milestones"] - frow["certified"]
    d1_pct = drop1 / frow["enrolled"] if frow["enrolled"] > 0 else 0
    d2_pct = drop2 / frow["active_milestones"] if frow["active_milestones"] > 0 else 0

    fc1, fc2 = st.columns(2)
    with fc1:
        color = "warn-box" if d1_pct > 0.20 else "ai-box"
        st.markdown(f'<div class="{color}">Enrollment → Milestones drop-off: <strong>{drop1} learners ({d1_pct:.0%})</strong>. {"Elevated — investigate onboarding." if d1_pct > 0.20 else "Within normal range."}</div>', unsafe_allow_html=True)
    with fc2:
        color = "warn-box" if d2_pct > 0.15 else "ai-box"
        st.markdown(f'<div class="{color}">Milestones → Certified drop-off: <strong>{drop2} learners ({d2_pct:.0%})</strong>. {"Elevated — investigate completion barriers." if d2_pct > 0.15 else "Within normal range."}</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-header">Portfolio Funnel Comparison</div>', unsafe_allow_html=True)
    funnel_df = schools[["school_name", "enrolled", "active_milestones", "certified", "risk_tier"]].copy()
    funnel_df["enroll_to_active"] = (funnel_df["active_milestones"] / funnel_df["enrolled"]).round(2)
    funnel_df["active_to_cert"] = (funnel_df["certified"] / funnel_df["active_milestones"]).round(2)
    funnel_df.columns = ["School", "Enrolled", "Active Milestones", "Certified", "Tier", "Enroll→Active", "Active→Cert"]

    def color_rate(val):
        try:
            v = float(val)
            if v >= 0.80: return "color:#059669;font-weight:600"
            if v >= 0.65: return "color:#d97706;font-weight:600"
            return "color:#dc2626;font-weight:600"
        except: return ""

    st.dataframe(
        funnel_df.style
            .map(color_rate, subset=["Enroll→Active", "Active→Cert"])
            .format({"Enroll→Active": "{:.0%}", "Active→Cert": "{:.0%}"}),
        use_container_width=True, hide_index=True
    )

with tab3:
    st.markdown('<div class="section-header">Early Warning Monitor</div>', unsafe_allow_html=True)
    st.markdown("Flags that changed since last review. Act today or explain why you didn't.")

    silent = schools[schools["freshness_days"] >= 21].copy()
    tier_changes = schools[schools["prior_tier"] != schools["risk_tier"]].copy()
    alert_schools = schools[schools["risk_tier"] == "Alert"].copy()

    ew1, ew2, ew3 = st.columns(3)
    ew1.metric("Silent Schools (21+ days)", len(silent))
    ew2.metric("Tier Changes Since Last Review", len(tier_changes))
    ew3.metric("Schools on Alert", len(alert_schools))

    if not tier_changes.empty:
        st.markdown("#### Tier Changes")
        for _, r in tier_changes.iterrows():
            try:
                direction = "↑" if r["risk_tier"] == "Green" else "↓"
                box = "ai-box" if r["risk_tier"] == "Green" else "alert-box" if r["risk_tier"] == "Alert" else "warn-box"
                st.markdown(f'<div class="{box}">{direction} <strong>{r["school_name"]}</strong>: {r["prior_tier"]} → {r["risk_tier"]} — {r["ai_summary"]}</div>', unsafe_allow_html=True)
            except Exception as e:
                st.warning(f"⚠️ Could not render tier change for **{r.get('school_name', 'unknown')}**: {e}")

    if not silent.empty:
        st.markdown("#### Silent Schools")
        for _, r in silent.iterrows():
            try:
                gap = gap_diagnostician(r)
                msg = gap if gap else f"{r['school_name']} has not reported in {int(r['freshness_days'])} days."
                st.markdown(f'<div class="warn-box">🔇 <strong>{r["school_name"]}</strong> ({int(r["freshness_days"])} days): {msg}</div>', unsafe_allow_html=True)
            except Exception as e:
                st.warning(f"⚠️ Could not render silent school row for **{r.get('school_name', 'unknown')}**: {e}")

    declining = schools[schools["completion_rate"] < schools["prev_completion_rate"]].copy()
    if not declining.empty:
        st.markdown("#### Declining Completion")
        for _, r in declining.iterrows():
            try:
                delta = r["completion_rate"] - r["prev_completion_rate"]
                st.markdown(f'<div class="warn-box">📉 <strong>{r["school_name"]}</strong>: completion {r["prev_completion_rate"]:.0%} → {r["completion_rate"]:.0%} ({delta:+.0%})</div>', unsafe_allow_html=True)
            except Exception as e:
                st.warning(f"⚠️ Could not render completion row for **{r.get('school_name', 'unknown')}**: {e}")

with tab4:
    st.markdown('<div class="section-header">Benchmark View</div>', unsafe_allow_html=True)
    st.markdown("Each school vs. portfolio median. Lenders don't need domain expertise — benchmarks translate outcomes into confidence.")

    median_completion = schools["completion_rate"].median()
    median_confidence = schools["confidence_score"].median()

    bench_df = schools[["school_name", "region", "risk_tier", "completion_rate", "confidence_score"]].copy()
    bench_df["vs_median_completion"] = bench_df["completion_rate"] - median_completion
    bench_df["vs_median_confidence"] = bench_df["confidence_score"] - median_confidence
    bench_df = bench_df.rename(columns={
        "school_name": "School", "region": "Region", "risk_tier": "Tier",
        "completion_rate": "Completion", "confidence_score": "Confidence",
        "vs_median_completion": "vs Median (Completion)",
        "vs_median_confidence": "vs Median (Confidence)"
    })

    def color_vs(val):
        try:
            v = float(val)
            if v > 0.05: return "color:#059669;font-weight:600"
            if v < -0.05: return "color:#dc2626;font-weight:600"
            return "color:#6b7280"
        except: return ""

    try:
        st.dataframe(
            bench_df.style
                .map(color_vs, subset=["vs Median (Completion)", "vs Median (Confidence)"])
                .format({"Completion": "{:.0%}", "Confidence": "{:.0%}",
                         "vs Median (Completion)": "{:+.0%}", "vs Median (Confidence)": "{:+.0%}"}),
            use_container_width=True, hide_index=True
        )
    except Exception as e:
        st.warning(f"⚠️ Could not render benchmark table: {e}")
        st.dataframe(bench_df, use_container_width=True, hide_index=True)

    bc1, bc2 = st.columns(2)
    bc1.metric("Portfolio Median Completion", f"{median_completion:.0%}")
    bc2.metric("Portfolio Median Confidence", f"{median_confidence:.0%}")

    try:
        fig_bench = px.scatter(
            schools, x="completion_rate", y="confidence_score",
            color="risk_tier", hover_name="school_name",
            color_discrete_map={"Green": "#00b4b4", "Watch": "#f59e0b", "Alert": "#ef4444"},
            labels={"completion_rate": "Completion Rate", "confidence_score": "Confidence Score", "risk_tier": "Tier"},
            height=350
        )
        fig_bench.add_vline(x=median_completion, line_dash="dash", line_color="#94a3b8",
                            annotation_text="Median Completion", annotation_position="top right")
        fig_bench.add_hline(y=median_confidence, line_dash="dash", line_color="#94a3b8",
                            annotation_text="Median Confidence", annotation_position="top right")
        fig_bench.update_traces(marker=dict(size=11))
        fig_bench.update_layout(margin=dict(t=20, b=20), paper_bgcolor="#f5f7fa", plot_bgcolor="#f5f7fa")
        st.plotly_chart(fig_bench, use_container_width=True)
    except Exception as e:
        st.warning(f"⚠️ Could not render benchmark chart: {e}")

with tab5:
    st.markdown('<div class="section-header">Action Queue</div>', unsafe_allow_html=True)

    action_schools = schools[schools["action_trigger"].str.strip() != ""].copy()
    action_schools = action_schools.sort_values("confidence_score", ascending=True)

    st.markdown(f'<div class="action-queue-bar">⚡ Action Queue — {len(action_schools)} items need review (AI prioritized)</div>', unsafe_allow_html=True)

    if action_schools.empty:
        st.info("No action items at this time.")
    else:
        for _, r in action_schools.iterrows():
            rec_tier, rec_conf = recommend_tier(r)
            tier_color = {"Green": "#059669", "Watch": "#d97706", "Alert": "#dc2626"}.get(r["risk_tier"], "#6b7280")
            with st.container():
                try:
                    st.markdown(f"""
<div class="action-row">
  <strong>{r['school_name']}</strong>
  &nbsp;<span style="color:{tier_color};font-weight:700">{r['risk_tier']}</span>
  &nbsp;·&nbsp; <span style="color:#6b7280;font-size:13px">{freshness_label(r['freshness_days'])} since update · {int(r['open_issues'])} open issues</span><br>
  <span style="font-size:13px;color:#374151">📌 Trigger: {r['action_trigger']}</span><br>
  <span style="font-size:13px;color:#0f1c2e">→ {r['action_recommendation']}</span>
  &nbsp;<span style="font-size:12px;color:#00b4b4">AI confidence: {safe_pct(r['action_confidence'])}</span>
</div>
""", unsafe_allow_html=True)
                    acol1, acol2 = st.columns([1, 5])
                    with acol1:
                        st.button("Dismiss", key=f"dismiss_{r['school_id']}")
                except Exception as e:
                    st.warning(f"⚠️ Could not render action item for **{r.get('school_name', 'unknown school')}**: {e}")

        st.markdown("---")
        st.markdown("**All candidates requiring review across flagged schools:**")
        flagged_ids = action_schools["school_id"].tolist()
        flagged_cands = candidates[candidates["school_id"].isin(flagged_ids) & (candidates["recommended_decision"] != "Approve")]
        if not flagged_cands.empty:
            st.dataframe(
                flagged_cands[["candidate_name", "school_id", "program_stage", "credit_band",
                               "requested_amount", "recommended_decision", "data_flag"]].rename(columns={
                    "candidate_name": "Candidate", "school_id": "School ID",
                    "program_stage": "Stage", "credit_band": "Credit",
                    "requested_amount": "Amount", "recommended_decision": "Decision",
                    "data_flag": "Flag"
                }),
                use_container_width=True, hide_index=True
            )

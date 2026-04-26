# =============================================================================
# TradeCraft Lender Portal — app.py
#
# PURPOSE:
#   A lender-facing dashboard that helps financing partners evaluate pilot
#   schools and loan candidates. The portal surfaces school quality signals,
#   data confidence scores, and AI-driven recommendations so lenders can make
#   faster, better-informed decisions without needing deep domain expertise.
#
# HOW TO RUN:
#   streamlit run app.py
#
# FILES REQUIRED (must be in the same folder):
#   schools.csv     — 12 pilot schools with quality and confidence metrics
#   candidates.csv  — 36 loan candidates, roughly 3 per school
# =============================================================================

import streamlit as st   # The web application framework
import pandas as pd       # Data loading and manipulation
import plotly.express as px          # Simple interactive charts
import plotly.graph_objects as go    # Advanced charts (funnel)

# ── Page configuration ────────────────────────────────────────────────────────
# Sets the browser tab title and uses the full screen width for the layout.
st.set_page_config(page_title="TradeCraft Lender Portal", layout="wide")

# ── Visual styling ────────────────────────────────────────────────────────────
# Custom CSS injected into the page to match TradeCraft brand colors
# (navy #0f1c2e and teal #00b4b4) and support both light and dark display modes.
# Key design decisions:
#   - Sidebar gets a dark navy background with light text for labels
#   - Selectbox dropdowns use a dark-on-light input field so selected values
#     remain readable regardless of system theme
#   - KPI cards use CSS variables that adapt automatically to light/dark mode
#   - Risk tier pills (Green/Watch/Alert) always use high-contrast colors
#   - Info boxes (ai-box, warn-box, alert-box) adapt their background/text
#     for dark mode so they remain legible
st.markdown("""
<style>
/* ── Sidebar shell ─────────────────────────────── */
[data-testid="stSidebar"] { background: #0f1c2e !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span:not([data-baseweb]),
[data-testid="stSidebar"] label { color: #cbd5e1 !important; }
[data-testid="stSidebar"] .stSelectbox > label { color: #00b4b4 !important; font-weight: 600; }
/* Selectbox input — keep native system colors so value is visible in both modes */
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: #1e3050 !important;
    border-color: #334d6e !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] [data-baseweb="select"] span,
[data-testid="stSidebar"] [data-baseweb="select"] div {
    color: #f1f5f9 !important;
}
/* ── Portal header ─────────────────────────────── */
.portal-header {
    background: #0f1c2e; padding: 14px 24px; border-radius: 8px;
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 18px;
}
.portal-title { color: #ffffff; font-size: 20px; font-weight: 700; margin: 0; }
.portal-tabs { color: #00b4b4; font-size: 14px; }
/* ── KPI cards — adaptive ──────────────────────── */
.kpi-card {
    background: var(--kpi-bg, #ffffff);
    border: 1px solid var(--kpi-border, #e5e7eb);
    border-radius: 8px; padding: 18px 20px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08); text-align: center;
    min-height: 110px; display: flex; flex-direction: column; justify-content: center;
}
.kpi-value { font-size: 36px; font-weight: 700; color: var(--kpi-val, #0f1c2e); line-height: 1.1; }
.kpi-label { font-size: 13px; color: #6b7280; margin-top: 4px; }
.kpi-delta { font-size: 12px; color: #00b4b4; font-weight: 600; }
/* Light mode overrides */
@media (prefers-color-scheme: light) {
    :root { --kpi-bg: #ffffff; --kpi-border: #e5e7eb; --kpi-val: #0f1c2e; }
}
/* Dark mode overrides */
@media (prefers-color-scheme: dark) {
    :root { --kpi-bg: #1e293b; --kpi-border: #334155; --kpi-val: #f1f5f9; }
    .kpi-label { color: #94a3b8; }
    .section-header { color: #e2e8f0 !important; }
    .action-row { background: #1e293b !important; border-left-color: #00b4b4; }
    .action-row span, .action-row strong { color: #e2e8f0 !important; }
}
/* ── Pills — always high-contrast ─────────────── */
.pill-green { background:#d1fae5; color:#065f46; border-radius:12px; padding:3px 12px; font-size:12px; font-weight:700; display:inline-block; }
.pill-watch { background:#fef3c7; color:#92400e; border-radius:12px; padding:3px 12px; font-size:12px; font-weight:700; display:inline-block; }
.pill-alert { background:#fee2e2; color:#991b1b; border-radius:12px; padding:3px 12px; font-size:12px; font-weight:700; display:inline-block; }
/* ── Action queue ──────────────────────────────── */
.action-queue-bar {
    background: #0d9488; color: #ffffff; padding: 12px 18px;
    border-radius: 8px; font-weight: 600; font-size: 14px; margin: 12px 0 6px 0;
}
.action-row {
    background: #ffffff; border-radius: 6px; padding: 12px 16px;
    margin-bottom: 8px; border-left: 4px solid #0f1c2e;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
/* ── Info boxes — adaptive ─────────────────────── */
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
@media (prefers-color-scheme: dark) {
    .ai-box   { background: #0d2e2b; color: #6ee7de; }
    .warn-box { background: #2d1f00; color: #fcd34d; }
    .alert-box{ background: #2d0a0a; color: #fca5a5; }
}
/* ── Tabs ──────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] { gap: 4px; background: #0f1c2e; padding: 6px 8px; border-radius: 8px; }
.stTabs [data-baseweb="tab"] { color: #94a3b8 !important; background: transparent; border-radius: 6px; padding: 6px 16px; font-size: 14px; }
.stTabs [aria-selected="true"] { background: #00b4b4 !important; color: #ffffff !important; }
</style>
""", unsafe_allow_html=True)

# ── Data loading ──────────────────────────────────────────────────────────────
# Loads both CSV files once and caches the result so the app doesn't re-read
# from disk on every user interaction. All numeric columns are explicitly cast
# to numbers — this prevents "nan" display errors that occur when CSV values
# are read as plain text. String columns that may be empty are filled with
# blank strings so they never render as "nan" in the UI.
@st.cache_data
def load_data():
    s = pd.read_csv("schools.csv")
    c = pd.read_csv("candidates.csv")

    # Columns that must be treated as numbers for calculations and formatting
    numeric_school = ["completion_rate","prev_completion_rate","confidence_score","stalled_pct",
                      "freshness_days","avg_attendance","withdrawal_rate","open_issues",
                      "enrolled","active_milestones","certified","benchmark_completion",
                      "benchmark_confidence","action_confidence"]
    for col in numeric_school:
        if col in s.columns:
            s[col] = pd.to_numeric(s[col], errors="coerce")

    # Text fields that may be empty in the CSV — replace missing values with
    # blank strings so they never appear as "nan" in the dashboard
    for col in ["data_gap_note","anomaly_flag","anomaly_note","action_trigger","action_recommendation"]:
        if col in s.columns:
            s[col] = s[col].fillna("").astype(str).str.strip()
    for col in ["data_flag","decision_reason"]:
        if col in c.columns:
            c[col] = c[col].fillna("").astype(str).str.strip()
    return s, c

schools, candidates = load_data()

# ── Helper functions ──────────────────────────────────────────────────────────

def freshness_label(days):
    """
    Converts a raw number of days into a human-readable label.
    Example: 0 → "today", 1 → "1 day", 14 → "14 days".
    Handles missing or non-numeric values gracefully.
    """
    try:
        days = float(days)
    except (ValueError, TypeError):
        return "unknown"
    if days == 0: return "today"
    if days <= 1: return "1 day"
    return f"{int(days)} days"

def safe_pct(val, fallback="—"):
    """
    Safely formats a decimal value (e.g. 0.74) as a percentage (e.g. "74%").
    Returns a dash if the value is missing, not a number, or unreadable.
    This prevents raw "nan%" from appearing anywhere in the UI.
    """
    try:
        v = float(val)
        if v != v: return fallback  # Catches NaN (not-a-number) values
        return f"{v:.0%}"
    except (ValueError, TypeError):
        return fallback

def tier_pill(tier):
    """
    Returns a color-coded HTML badge for a risk tier label.
    Green = low risk, Watch = caution, Alert = high risk / action required.
    """
    if tier == "Green": return '<span class="pill-green">Green</span>'
    if tier == "Watch": return '<span class="pill-watch">Watch</span>'
    return '<span class="pill-alert">Alert</span>'

def completion_delta(row):
    """
    Calculates how much a school's completion rate has changed since the
    prior review period. Returns a signed percentage string (e.g. "+11%"
    or "-6%"). A positive delta is good — more students are completing.
    """
    try:
        d = float(row["completion_rate"]) - float(row["prev_completion_rate"])
        if d != d: return "—"  # Catches NaN
        sign = "+" if d >= 0 else ""
        return f"{sign}{d:.0%}"
    except (ValueError, TypeError):
        return "—"

def ai_risk_summary(row):
    """
    AI Risk Change Summarizer — one of four rule-based AI features.

    Generates a plain-English summary of a school's current status. If the
    school's risk tier has changed since the last review (e.g. Watch → Green),
    the summary leads with that movement so lenders immediately understand
    what changed and why. No live AI service is called — the summary is
    pre-written in the data and assembled here by logic.
    """
    prior = str(row.get("prior_tier", "")).strip()
    current = str(row.get("risk_tier", "")).strip()
    summary = str(row.get("ai_summary", "")).strip()
    # Only prepend the movement prefix if the tier actually changed and the
    # summary doesn't already start with the school name (avoids duplication)
    if prior and current and prior != current and not summary.startswith(row["school_name"]):
        return f"{row['school_name']} moved {prior} → {current}. {summary}"
    return summary

def anomaly_check(row):
    """
    Anomaly Explainer — one of four rule-based AI features.

    Scans a school's metrics for values that fall outside plausible ranges
    and returns plain-English explanations for each flag. For example:
    - A 100% completion rate is suspicious and may indicate data problems
    - A stalled-learner rate above 25% suggests a bottleneck in the program

    These flags help lenders ask the right questions rather than just seeing
    a raw number they may not know how to interpret.
    """
    flags = []
    if row["completion_rate"] >= 0.97:
        flags.append(f"Completion rate unusually high ({row['completion_rate']:.0%}). Likely cause: small cohort skewing %, or non-standard milestone recording.")
    if row["completion_rate"] < 0.30:
        flags.append(f"Completion rate critically low ({row['completion_rate']:.0%}). May indicate mass withdrawal or data ingestion failure.")
    if row["stalled_pct"] > 0.25:
        flags.append(f"Stalled learner rate is {row['stalled_pct']:.0%} — above 25% threshold. Investigate milestone bottleneck.")
    return flags

def gap_diagnostician(row):
    """
    Data Gap Diagnostician — one of four rule-based AI features.

    Identifies schools that have gone silent (no data updates in 21+ days)
    and returns a plain-English explanation of what may have gone wrong,
    along with a suggested corrective action. This turns a vague "stale data"
    flag into an actionable ticket the lender or account manager can act on.
    Returns None if the school has no data gap concern.
    """
    # First check if a specific note is already recorded in the data
    note = str(row.get("data_gap_note", "") or "")
    if note.strip() and note.strip().lower() != "nan":
        return note.strip()
    # Fall back to a generated message based on freshness threshold (21 days)
    try:
        if float(row["freshness_days"]) >= 21:
            return f"School has not synced in {int(float(row['freshness_days']))} days. Milestones may be batch-entered. Suggest: prompt admin to enable auto-sync."
    except (ValueError, TypeError):
        pass
    return None

def recommend_tier(row):
    """
    Risk Tier Recommender — one of four rule-based AI features.

    Applies a rule-based scoring model to suggest whether a school should
    be classified as Green, Watch, or Alert. The lender sees this recommendation
    alongside their current tier and can Confirm or Override it.

    Rules (illustrative thresholds — would be calibrated from real data):
      Green:  completion >= 70%, confidence >= 75%, data < 14 days old, no open issues
      Alert:  completion < 55%, OR confidence < 50%, OR data 30+ days old, OR 5+ issues
      Watch:  everything else (mixed signals, needs monitoring)

    Returns the recommended tier label and a confidence score (0–1) indicating
    how certain the model is about the recommendation.
    """
    q = row["completion_rate"]      # How many students complete the program
    c = row["confidence_score"]     # How much we trust the data behind that number
    f = row["freshness_days"]       # How recently the school reported data
    issues = row["open_issues"]     # Number of unresolved data quality issues

    if q >= 0.70 and c >= 0.75 and f <= 14 and issues == 0:
        return "Green", 0.92   # Strong signal, high confidence
    if q < 0.55 or c < 0.50 or f >= 30 or issues >= 5:
        return "Alert", 0.89   # Clear risk signal
    return "Watch", 0.78       # Mixed — needs monitoring

# ── Portal header ─────────────────────────────────────────────────────────────
# Renders the branded top bar matching the TradeCraft presentation design.
# The tab names on the right are purely decorative here — the actual navigation
# is handled by Streamlit's st.tabs() below.
st.markdown("""
<div class="portal-header">
  <span class="portal-title">TradeCraft Lender Portal</span>
  <span class="portal-tabs">Portfolio &nbsp;·&nbsp; Funnel &nbsp;·&nbsp; Benchmarks &nbsp;·&nbsp; Alerts</span>
</div>
""", unsafe_allow_html=True)

# ── Sidebar filters ───────────────────────────────────────────────────────────
# Three dropdown filters let lenders narrow the school list by geography,
# risk level, or lending status. Selections flow through to the school table,
# scatter chart, and detail panel on the Portfolio tab.
st.sidebar.markdown('<p style="color:#00b4b4;font-size:13px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:8px">Filters</p>', unsafe_allow_html=True)
regions = ["All"] + sorted(schools["region"].unique().tolist())
region = st.sidebar.selectbox("Region", regions)
tiers = ["All", "Green", "Watch", "Alert"]
tier_filter = st.sidebar.selectbox("Risk Tier", tiers)
statuses = ["All"] + sorted(schools["lender_status"].unique().tolist())
status_filter = st.sidebar.selectbox("Lender Status", statuses)

# Apply the selected filters to create a narrowed view of the school data
filtered = schools.copy()
if region != "All":
    filtered = filtered[filtered["region"] == region]
if tier_filter != "All":
    filtered = filtered[filtered["risk_tier"] == tier_filter]
if status_filter != "All":
    filtered = filtered[filtered["lender_status"] == status_filter]

# ── KPI strip ─────────────────────────────────────────────────────────────────
# Four headline numbers at the top of the page answer the first question every
# lender asks when opening the portal: "Do I need to act on anything today?"
# Always calculated from the full portfolio (not the filtered view) so the
# numbers are consistent regardless of what filters are applied.
approved_n  = int((schools["lender_status"] == "Approved").sum())   # Schools cleared for lending
watchlist_n = int((schools["risk_tier"] == "Watch").sum())           # Schools needing monitoring
alert_n     = int((schools["risk_tier"] == "Alert").sum())           # Schools with active risk flags
action_n    = int((schools["action_trigger"].str.strip() != "").sum()) # AI-prioritized action items
avg_conf    = schools["confidence_score"].mean()                     # How much we trust the data overall
prev_avg_conf = schools["confidence_score"].mean() - 0.03           # Simulated prior-period value

kc1, kc2, kc3, kc4 = st.columns(4)
with kc1:
    # Total schools currently approved for active lending
    st.markdown(f'<div class="kpi-card"><div class="kpi-value">{approved_n}</div><div class="kpi-label">Approved Schools</div><div class="kpi-delta">&nbsp;</div></div>', unsafe_allow_html=True)
with kc2:
    # Schools on the watch-list, with a note of how many are at Alert severity
    st.markdown(f'<div class="kpi-card"><div class="kpi-value">{watchlist_n}</div><div class="kpi-label">Watch-list</div><div class="kpi-delta">↑ {alert_n} on Alert</div></div>', unsafe_allow_html=True)
with kc3:
    # Number of AI-prioritized items in the Action Queue requiring lender review
    st.markdown(f'<div class="kpi-card"><div class="kpi-value">{action_n}</div><div class="kpi-label">Action Items</div><div class="kpi-delta">AI prioritized</div></div>', unsafe_allow_html=True)
with kc4:
    # Average data confidence across all schools, with change vs. prior period
    delta_conf = avg_conf - prev_avg_conf
    st.markdown(f'<div class="kpi-card"><div class="kpi-value">{avg_conf:.0%}</div><div class="kpi-label">Avg Confidence</div><div class="kpi-delta">+{delta_conf:.0%} vs prior</div></div>', unsafe_allow_html=True)

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# ── Tab navigation ────────────────────────────────────────────────────────────
# Five views, each serving a distinct lender job-to-be-done:
#   Portfolio      — "What is the current status of my school portfolio?"
#   Funnel         — "Where are students dropping off within each school?"
#   Early Warning  — "What changed since my last visit that I need to act on?"
#   Benchmarks     — "How does each school compare to the rest of the portfolio?"
#   Action Queue   — "What specifically should I do today, in priority order?"
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Portfolio", "Progression Funnel", "Early Warning", "Benchmarks", "Action Queue"
])

# =============================================================================
# TAB 1 — PORTFOLIO
# The first screen a lender sees. Must answer "do I need to act today?" in
# under 10 seconds. Shows every school with completion trend, data freshness,
# confidence score, current tier, and AI-recommended tier side by side.
# =============================================================================
with tab1:
    st.markdown('<div class="section-header">School Risk Summary</div>', unsafe_allow_html=True)

    # Build the display table row by row, applying safe formatting to every
    # numeric field so missing data never causes a visible "nan" error
    table_rows = []
    for _, row in filtered.iterrows():
        rec_tier, rec_conf = recommend_tier(row)
        table_rows.append({
            "School":        row["school_name"],
            "Region":        row["region"],
            "Completion":    safe_pct(row['completion_rate']),
            "Δ":             completion_delta(row),       # Change vs. prior period
            "Confidence":    safe_pct(row['confidence_score']),
            "Updated":       freshness_label(row["freshness_days"]),  # Human-readable freshness
            "Tier":          row["risk_tier"],             # Current assigned tier
            "Status":        row["lender_status"],
            "AI Recommends": rec_tier,                    # Model's suggested tier
        })

    df_table = pd.DataFrame(table_rows)

    # Color-code the Tier and AI Recommends columns so risk level is visible
    # at a glance without the lender needing to read the label
    def color_tier_col(val):
        colors = {"Green": "background-color:#d1fae5;color:#065f46;font-weight:700",
                  "Watch": "background-color:#fef3c7;color:#92400e;font-weight:700",
                  "Alert": "background-color:#fee2e2;color:#991b1b;font-weight:700"}
        return colors.get(val, "")

    # Color-code the completion delta: green for improvement, red for decline
    def color_delta(val):
        if val.startswith("+"): return "color:#059669;font-weight:600"
        if val.startswith("-"): return "color:#dc2626;font-weight:600"
        return ""

    styled = (df_table.style
              .map(color_tier_col, subset=["Tier", "AI Recommends"])
              .map(color_delta, subset=["Δ"]))
    st.dataframe(styled, use_container_width=True, hide_index=True)

    # ── School detail panel ───────────────────────────────────────────────────
    # When a lender selects a school, this section shows all available metrics,
    # the AI summary, any anomaly flags, data gap warnings, and the AI tier
    # recommendation with Confirm / Override controls.
    st.markdown('<div class="section-header">School Detail</div>', unsafe_allow_html=True)
    detail_options = filtered["school_name"].tolist()
    if detail_options:
        sel = st.selectbox("Select a school", detail_options, key="portfolio_school")
        # Always pull from the full dataset so detail is never filtered out
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
            # Safe integer cast — open_issues may be NaN if data is missing
            open_iss = row['open_issues']
            open_str = str(int(open_iss)) if open_iss == open_iss else "—"
            st.markdown(f"**Open Issues:** {open_str}")

        # AI Risk Change Summarizer — plain-English narrative for this school
        summary = ai_risk_summary(row)
        st.markdown(f'<div class="ai-box">💡 <strong>AI Summary:</strong> {summary}</div>', unsafe_allow_html=True)

        # Anomaly Explainer — flags anything statistically implausible
        anomalies = anomaly_check(row)
        for a in anomalies:
            st.markdown(f'<div class="warn-box">⚠️ <strong>Anomaly:</strong> {a}</div>', unsafe_allow_html=True)

        # Data Gap Diagnostician — flags silent schools and suggests next steps
        gap = gap_diagnostician(row)
        if gap:
            st.markdown(f'<div class="warn-box">🔍 <strong>Data Gap:</strong> {gap}</div>', unsafe_allow_html=True)

        # Risk Tier Recommender — shows the model's suggestion with confidence
        # score; lender can Confirm to accept or Override to record a manual call
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

        # ── Candidate review panel ────────────────────────────────────────────
        # For the selected school, shows each loan candidate's profile, their
        # progression through the program, and the recommended lending decision
        # (Approve / Review / Hold) with a plain-English explanation.
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
                # Only show the data flag if it has a real value (not blank/nan)
                flag = str(cand.get("data_flag", "") or "")
                if flag.strip() and flag.strip().lower() not in ("none", "nan", ""):
                    st.markdown(f"**Flag:** ⚠️ {flag.strip()}")

            # Color-coded decision badge — lenders see the recommendation
            # immediately without needing to read the explanation first
            decision = cand["recommended_decision"]
            badge = {"Approve": "🟢", "Review": "🟡", "Hold": "🔴"}.get(decision, "⚪")
            st.markdown(f"### {badge} Recommended: **{decision}**")
            reason = str(cand.get('decision_reason', '') or '').strip()
            if reason and reason.lower() != 'nan':
                st.markdown(f"> {reason}")

# =============================================================================
# TAB 2 — PROGRESSION FUNNEL
# Shows how many students at a selected school are moving through each stage:
# Enrolled → Active Milestones → Certified. Drop-off at each stage is
# calculated and flagged if it exceeds normal thresholds. A portfolio-wide
# comparison table lets lenders benchmark funnel performance across schools.
# =============================================================================
with tab2:
    st.markdown('<div class="section-header">Progression Funnel</div>', unsafe_allow_html=True)
    st.markdown("Enrollment → Active Milestones → Certified, by school.")

    funnel_school = st.selectbox("Select school", schools["school_name"].tolist(), key="funnel_school")
    frow = schools[schools["school_name"] == funnel_school].iloc[0]

    # Funnel chart: each bar represents one stage of the student journey.
    # The width of each bar shows how many students remain at that stage.
    fig_funnel = go.Figure(go.Funnel(
        y=["Enrolled", "Active Milestones", "Certified"],
        x=[frow["enrolled"], frow["active_milestones"], frow["certified"]],
        textinfo="value+percent initial",   # Show count + % of original enrollment
        marker=dict(color=["#0f1c2e", "#0d9488", "#00b4b4"])   # Brand colors
    ))
    fig_funnel.update_layout(margin=dict(t=20, b=20), height=320, paper_bgcolor="#f5f7fa")
    st.plotly_chart(fig_funnel, use_container_width=True)

    # Calculate drop-off rates between each stage
    drop1 = frow["enrolled"] - frow["active_milestones"]   # Students who never hit a milestone
    drop2 = frow["active_milestones"] - frow["certified"]  # Students who stalled before certifying
    d1_pct = drop1 / frow["enrolled"] if frow["enrolled"] > 0 else 0
    d2_pct = drop2 / frow["active_milestones"] if frow["active_milestones"] > 0 else 0

    # Flag elevated drop-off rates with a warning box; normal rates get a
    # green info box so lenders can quickly see what's fine vs. concerning
    fc1, fc2 = st.columns(2)
    with fc1:
        color = "warn-box" if d1_pct > 0.20 else "ai-box"
        st.markdown(f'<div class="{color}">Enrollment → Milestones drop-off: <strong>{drop1} learners ({d1_pct:.0%})</strong>. {"Elevated — investigate onboarding." if d1_pct > 0.20 else "Within normal range."}</div>', unsafe_allow_html=True)
    with fc2:
        color = "warn-box" if d2_pct > 0.15 else "ai-box"
        st.markdown(f'<div class="{color}">Milestones → Certified drop-off: <strong>{drop2} learners ({d2_pct:.0%})</strong>. {"Elevated — investigate completion barriers." if d2_pct > 0.15 else "Within normal range."}</div>', unsafe_allow_html=True)

    # Portfolio-wide funnel comparison table — color-coded conversion rates
    st.markdown('<div class="section-header">Portfolio Funnel Comparison</div>', unsafe_allow_html=True)
    funnel_df = schools[["school_name", "enrolled", "active_milestones", "certified", "risk_tier"]].copy()
    funnel_df["enroll_to_active"] = (funnel_df["active_milestones"] / funnel_df["enrolled"]).round(2)
    funnel_df["active_to_cert"]   = (funnel_df["certified"] / funnel_df["active_milestones"]).round(2)
    funnel_df.columns = ["School", "Enrolled", "Active Milestones", "Certified", "Tier", "Enroll→Active", "Active→Cert"]

    def color_rate(val):
        # Green ≥ 80%, amber 65–79%, red < 65%
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

# =============================================================================
# TAB 3 — EARLY WARNING MONITOR
# The "daily habit" view. Shows only what changed since the last review:
# tier movements, schools that have gone silent (no data in 21+ days), and
# schools whose completion rate is declining. The goal is to surface only
# signal — not noise — so lenders don't miss critical changes in a large portfolio.
# =============================================================================
with tab3:
    st.markdown('<div class="section-header">Early Warning Monitor</div>', unsafe_allow_html=True)
    st.markdown("Flags that changed since last review. Act today or explain why you didn't.")

    # Identify the three categories of concern
    silent       = schools[schools["freshness_days"] >= 21].copy()                    # Schools that have gone quiet
    tier_changes = schools[schools["prior_tier"] != schools["risk_tier"]].copy()      # Schools that moved up or down a tier
    alert_schools= schools[schools["risk_tier"] == "Alert"].copy()                    # Schools currently at highest risk

    # Summary metrics at the top of the tab
    ew1, ew2, ew3 = st.columns(3)
    ew1.metric("Silent Schools (21+ days)", len(silent))
    ew2.metric("Tier Changes Since Last Review", len(tier_changes))
    ew3.metric("Schools on Alert", len(alert_schools))

    # Tier changes — each shown as an up/down movement with the AI summary
    if not tier_changes.empty:
        st.markdown("#### Tier Changes")
        for _, r in tier_changes.iterrows():
            try:
                direction = "↑" if r["risk_tier"] == "Green" else "↓"
                # Box color reflects the new tier, not the old one
                box = "ai-box" if r["risk_tier"] == "Green" else "alert-box" if r["risk_tier"] == "Alert" else "warn-box"
                st.markdown(f'<div class="{box}">{direction} <strong>{r["school_name"]}</strong>: {r["prior_tier"]} → {r["risk_tier"]} — {r["ai_summary"]}</div>', unsafe_allow_html=True)
            except Exception as e:
                st.warning(f"⚠️ Could not render tier change for **{r.get('school_name', 'unknown')}**: {e}")

    # Silent schools — schools that have stopped reporting data
    if not silent.empty:
        st.markdown("#### Silent Schools")
        for _, r in silent.iterrows():
            try:
                gap = gap_diagnostician(r)
                msg = gap if gap else f"{r['school_name']} has not reported in {int(r['freshness_days'])} days."
                st.markdown(f'<div class="warn-box">🔇 <strong>{r["school_name"]}</strong> ({int(r["freshness_days"])} days): {msg}</div>', unsafe_allow_html=True)
            except Exception as e:
                st.warning(f"⚠️ Could not render silent school row for **{r.get('school_name', 'unknown')}**: {e}")

    # Declining completion — schools whose completion rate has dropped since last period
    declining = schools[schools["completion_rate"] < schools["prev_completion_rate"]].copy()
    if not declining.empty:
        st.markdown("#### Declining Completion")
        for _, r in declining.iterrows():
            try:
                delta = r["completion_rate"] - r["prev_completion_rate"]
                st.markdown(f'<div class="warn-box">📉 <strong>{r["school_name"]}</strong>: completion {r["prev_completion_rate"]:.0%} → {r["completion_rate"]:.0%} ({delta:+.0%})</div>', unsafe_allow_html=True)
            except Exception as e:
                st.warning(f"⚠️ Could not render completion row for **{r.get('school_name', 'unknown')}**: {e}")

# =============================================================================
# TAB 4 — BENCHMARK VIEW
# Shows each school's completion and confidence scores relative to the portfolio
# median. Lenders don't naturally understand what a "68% completion rate" means
# in the context of vocational training — benchmarks translate raw numbers
# into a relative signal without requiring domain expertise.
# =============================================================================
with tab4:
    st.markdown('<div class="section-header">Benchmark View</div>', unsafe_allow_html=True)
    st.markdown("Each school vs. portfolio median. Lenders don't need domain expertise — benchmarks translate outcomes into confidence.")

    # Calculate portfolio-wide medians to use as the comparison baseline
    median_completion = schools["completion_rate"].median()
    median_confidence = schools["confidence_score"].median()

    # Build the benchmark table — each school gets a +/- vs. median column
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
        # Green if more than 5 pts above median, red if more than 5 pts below
        try:
            v = float(val)
            if v > 0.05:  return "color:#059669;font-weight:600"
            if v < -0.05: return "color:#dc2626;font-weight:600"
            return "color:#6b7280"
        except: return ""

    # Wrap in try/except — if styling fails (e.g. type conflict), fall back
    # to plain unstyled table rather than crashing the entire tab
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

    # Scatter plot — each dot is a school. The dashed lines show the portfolio
    # median for each axis. Schools in the upper-right quadrant (high completion,
    # high confidence) are the strongest lending candidates.
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

# =============================================================================
# TAB 5 — ACTION QUEUE
# The lender's to-do list, AI-prioritized. Each item shows which school needs
# attention, why it was flagged, what action is recommended, and how confident
# the model is in that recommendation. Schools are sorted by lowest confidence
# score first — the most uncertain situations rise to the top.
# Also shows all non-Approve candidate decisions at flagged schools so the
# lender can see which individual loans are affected.
# =============================================================================
with tab5:
    st.markdown('<div class="section-header">Action Queue</div>', unsafe_allow_html=True)

    # Filter to schools that have a non-empty action trigger, sorted by
    # lowest confidence first (most uncertain = most urgent to review)
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
                # Each action card shows: school name, current tier, data age,
                # open issues, the specific trigger reason, the recommended action,
                # and the model's confidence score for that recommendation.
                # Wrapped in try/except so a single malformed row shows a warning
                # instead of crashing the entire tab.
                try:
                    st.markdown(f"""
<div class="action-row">
  <strong>{r['school_name']}</strong>
  &nbsp;<span style="color:{tier_color};font-weight:700">{r['risk_tier']}</span>
  &nbsp;·&nbsp; <span style="color:#6b7280;font-size:13px">{freshness_label(r['freshness_days'])} since update · {int(r['open_issues']) if r['open_issues']==r['open_issues'] else 0} open issues</span><br>
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

        # Pull only the candidates at flagged schools who are not already Approved
        # — these are the individual loan decisions the lender needs to evaluate
        flagged_ids = action_schools["school_id"].tolist()
        flagged_cands = candidates[candidates["school_id"].isin(flagged_ids) & (candidates["recommended_decision"] != "Approve")]
        if not flagged_cands.empty:
            st.dataframe(
                flagged_cands[["candidate_name", "school_id", "program_stage", "credit_band",
                               "requested_amount", "recommended_decision", "data_flag"]]
                .fillna("").replace("nan", "")   # Ensure no raw "nan" values appear in the table
                .rename(columns={
                    "candidate_name": "Candidate", "school_id": "School ID",
                    "program_stage": "Stage", "credit_band": "Credit",
                    "requested_amount": "Amount", "recommended_decision": "Decision",
                    "data_flag": "Flag"
                }),
                use_container_width=True, hide_index=True
            )

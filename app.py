import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

import live_metrics
import metrics

DB_PATH = Path(__file__).parent / "data" / "kestrel_ops.db"

st.set_page_config(
    page_title="Kestrel | Control Tower",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# DESIGN SYSTEM
# -----------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

    :root {
        --ink: #101828;
        --muted: #667085;
        --line: #E4E7EC;
        --surface: #FFFFFF;
        --canvas: #F7F8FA;
        --accent: #175CD3;
        --accent-soft: #EFF4FF;
        --danger: #D92D20;
        --danger-soft: #FEF3F2;
        --warn: #B54708;
        --warn-soft: #FFFAEB;
        --success: #027A48;
        --success-soft: #ECFDF3;
    }

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
        color: var(--ink);
    }

    .stApp {
        background: var(--canvas);
    }

    [data-testid="stHeader"] {
        background: rgba(247,248,250,.92);
    }

    [data-testid="stSidebar"] {
        background: #FFFFFF;
        border-right: 1px solid var(--line);
    }

    [data-testid="stSidebar"] * {
        font-family: 'DM Sans', sans-serif;
    }

    h1, h2, h3 {
        font-family: 'Space Grotesk', sans-serif !important;
        letter-spacing: -0.025em;
    }

    h1 {
        font-size: 2.15rem !important;
        margin-bottom: .15rem !important;
    }

    h2 {
        font-size: 1.35rem !important;
        margin-top: 1.4rem !important;
    }

    h3 {
        font-size: 1rem !important;
    }

    .hero {
        background: linear-gradient(135deg, #101828 0%, #182230 100%);
        border-radius: 18px;
        padding: 28px 30px;
        color: white;
        margin-bottom: 18px;
        box-shadow: 0 10px 30px rgba(16,24,40,.10);
    }

    .hero-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 28px;
        font-weight: 700;
        letter-spacing: -.035em;
    }

    .hero-sub {
        color: #D0D5DD;
        font-size: 14px;
        margin-top: 5px;
    }

    .hero-pill {
        display: inline-block;
        margin-top: 18px;
        padding: 5px 10px;
        border: 1px solid rgba(255,255,255,.16);
        border-radius: 999px;
        color: #EAECF0;
        font-size: 12px;
    }

    .kpi {
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 18px 18px 16px;
        min-height: 118px;
        box-shadow: 0 2px 8px rgba(16,24,40,.03);
    }

    .kpi-label {
        color: var(--muted);
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: .055em;
    }

    .kpi-value {
        color: var(--ink);
        font-family: 'Space Grotesk', sans-serif;
        font-size: 28px;
        font-weight: 700;
        margin-top: 8px;
    }

    .kpi-note {
        color: var(--muted);
        font-size: 12px;
        margin-top: 4px;
    }

    .section-label {
        color: var(--muted);
        font-size: 11px;
        font-weight: 700;
        letter-spacing: .09em;
        text-transform: uppercase;
        margin-top: 26px;
        margin-bottom: 8px;
    }

    .signal {
        border-radius: 14px;
        padding: 16px 18px;
        border: 1px solid var(--line);
        background: white;
    }

    .signal-danger {
        border-color: #FECACA;
        background: var(--danger-soft);
    }

    .signal-warn {
        border-color: #FEDF89;
        background: var(--warn-soft);
    }

    .signal-title {
        font-weight: 700;
        font-size: 14px;
    }

    .signal-body {
        color: #475467;
        font-size: 13px;
        line-height: 1.55;
        margin-top: 4px;
    }

    .rank {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 11px 0;
        border-bottom: 1px solid #F2F4F7;
    }

    .rank:last-child {
        border-bottom: 0;
    }

    .rank-name {
        font-weight: 600;
        font-size: 13px;
    }

    .rank-meta {
        color: var(--muted);
        font-size: 11px;
        margin-top: 2px;
    }

    .rank-value {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        font-size: 14px;
    }

    .risk-high { color: var(--danger); }
    .risk-mid { color: var(--warn); }
    .risk-good { color: var(--success); }

    .footnote {
        color: var(--muted);
        font-size: 11px;
        line-height: 1.5;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid var(--line);
        border-radius: 12px;
        overflow: hidden;
    }

    .stButton > button {
        border-radius: 9px;
        font-weight: 600;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        border-bottom: 1px solid var(--line);
    }

    .stTabs [data-baseweb="tab"] {
        padding: 10px 14px;
    }

    /* Reduce Streamlit chrome */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# DATA
# -----------------------------
@st.cache_data(ttl=300, show_spinner=False)
def query_db(query: str) -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(query, conn)


def fmt_int(x):
    return f"{int(round(float(x))):,}"


def fmt_inr(x):
    return f"₹{float(x):,.0f}"


def card(label, value, note=""):
    st.markdown(
        f"""
        <div class="kpi">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def rank_list(df, name_col, value_col, n=5, percent=False):
    for _, row in df.head(n).iterrows():
        value = f"{row[value_col]:.2f}%" if percent else fmt_inr(row[value_col])
        st.markdown(
            f"""
            <div class="rank">
                <div>
                    <div class="rank-name">{row[name_col]}</div>
                    <div class="rank-meta">{'Fill rate' if percent else 'Return value'}</div>
                </div>
                <div class="rank-value {'risk-high' if percent and row[value_col] < 85 else ''}">{value}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# -----------------------------
# SIDEBAR
# -----------------------------
with st.sidebar:
    st.markdown("### KESTREL")
    st.caption("Supply Chain Control Tower")

    st.markdown("---")

    page = st.radio(
        "View",
        ["Overview", "Service", "Inventory & Returns", "Cold Chain", "Freight & Price", "Divya's Questions"],
        label_visibility="collapsed",
    )

    st.markdown("---")

    if st.button("Refresh data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.caption("Database")
    st.code("kestrel_ops.db", language=None)

    st.caption("Data through")
    st.markdown("**30 June 2026**")

# -----------------------------
# CORE METRICS: Q1 FY2026-27 (Apr-Jun 2026)
# -----------------------------
# Rakesh's brief says explicitly, twice for emphasis: "make sure Q1 is on the
# front page. The board asks about Q1 first, every time." The original code
# had no date filtering anywhere on the Overview page; every number was an
# 18-month all-time average. Fixed: the front-page KPIs are now Q1-scoped by
# default, matching the direct instruction, not just a general aggregate.
Q1_START = "2026-04-01"
Q1_END = "2026-06-30"

kpi = query_db(
    f"""
    SELECT
        SUM(CASE WHEN ol.qty_uom = 'CASE'
                 THEN ol.ordered_qty * ol.case_pack_at_order
                 ELSE ol.ordered_qty END) AS ordered_eaches,
        SUM(CASE WHEN ol.qty_uom = 'CASE'
                 THEN ol.delivered_qty * ol.case_pack_at_order
                 ELSE ol.delivered_qty END) AS delivered_eaches
    FROM order_lines ol
    JOIN orders o ON ol.order_id = o.order_id
    JOIN outlets ot ON o.outlet_id = ot.outlet_id
    WHERE o.order_status IN ('DELIVERED', 'PARTIAL')
      AND o.order_date >= '{Q1_START}' AND o.order_date <= '{Q1_END}'
      AND ot.status = 'ACTIVE'
      AND ot.is_deleted = 0
      AND ot.outlet_id NOT IN (721, 722, 723);
    """
).iloc[0]

ordered = float(kpi["ordered_eaches"])
delivered = float(kpi["delivered_eaches"])
fill_rate = delivered / ordered * 100

on_time_by_delay = query_db(
    f"""
    SELECT COUNT(*) AS on_time_orders
    FROM orders o
    JOIN deliveries d ON o.order_id = d.order_id
    JOIN outlets ot ON o.outlet_id = ot.outlet_id
    WHERE o.order_status IN ('DELIVERED', 'PARTIAL')
      AND o.order_date >= '{Q1_START}' AND o.order_date <= '{Q1_END}'
      AND d.delay_minutes IS NOT NULL
      AND d.delay_minutes <= 120
      AND ot.status = 'ACTIVE' AND ot.is_deleted = 0
      AND ot.outlet_id NOT IN (721, 722, 723);
    """
).iloc[0]["on_time_orders"]

# Second on-time definition: did actual_arrival fall on/before requested_delivery_date.
# SQLite's DATE() silently returns NULL on the TELEMATICS_B format
# ("03-Jan-2025 12:43 PM"), which made the original query drop ~35% of rows
# from the numerator while the denominator still counted them. Fixed by parsing
# both vendor formats explicitly in pandas instead of relying on SQLite DATE().
_raw_dates = query_db(
    f"""
    SELECT o.order_id, o.requested_delivery_date, d.actual_arrival, d.telematics_vendor
    FROM orders o
    JOIN deliveries d ON o.order_id = d.order_id
    JOIN outlets ot ON o.outlet_id = ot.outlet_id
    WHERE o.order_status IN ('DELIVERED', 'PARTIAL')
      AND o.order_date >= '{Q1_START}' AND o.order_date <= '{Q1_END}'
      AND ot.status = 'ACTIVE' AND ot.is_deleted = 0
      AND ot.outlet_id NOT IN (721, 722, 723);
    """
)
_mask_a = _raw_dates["telematics_vendor"] == "TELEMATICS_A"
_mask_b = _raw_dates["telematics_vendor"] == "TELEMATICS_B"
_parsed_arrival = pd.Series(pd.NaT, index=_raw_dates.index, dtype="datetime64[ns]")
_parsed_arrival[_mask_a] = pd.to_datetime(
    _raw_dates.loc[_mask_a, "actual_arrival"], format="%Y-%m-%d %H:%M:%S", errors="coerce"
)
_parsed_arrival[_mask_b] = pd.to_datetime(
    _raw_dates.loc[_mask_b, "actual_arrival"], format="%d-%b-%Y %I:%M %p", errors="coerce"
)
_raw_dates["actual_arrival_parsed"] = _parsed_arrival
_raw_dates["requested_parsed"] = pd.to_datetime(_raw_dates["requested_delivery_date"], errors="coerce")
_unparsed = _raw_dates["actual_arrival_parsed"].isna().sum()
on_time_by_date = int(
    (_raw_dates["actual_arrival_parsed"].dt.date <= _raw_dates["requested_parsed"].dt.date).sum()
)

eligible_orders = query_db(
    f"""
    SELECT COUNT(*) AS count
    FROM orders o
    JOIN outlets ot ON o.outlet_id = ot.outlet_id
    WHERE o.order_status IN ('DELIVERED', 'PARTIAL')
      AND o.order_date >= '{Q1_START}' AND o.order_date <= '{Q1_END}'
      AND ot.status = 'ACTIVE' AND ot.is_deleted = 0
      AND ot.outlet_id NOT IN (721, 722, 723);
    """
).iloc[0]["count"]

on_time_rate_delay = float(on_time_by_delay) / float(eligible_orders) * 100
on_time_rate_date = float(on_time_by_date) / float(eligible_orders) * 100

near_expiry = query_db(
    """
    SELECT
        SUM(on_hand_cases) AS on_hand,
        SUM(available_cases) AS available
    FROM inventory_snapshots
    WHERE expiry_date IS NOT NULL
      AND DATE(expiry_date) >= DATE(snapshot_date)
      AND DATE(expiry_date) <= DATE(snapshot_date, '+30 days')
      AND snapshot_date = (SELECT MAX(snapshot_date) FROM inventory_snapshots);
    """
).iloc[0]

returns_total = query_db(
    f"SELECT SUM(credit_note_value_inr) AS value FROM returns_credit_notes "
    f"WHERE return_date >= '{Q1_START}' AND return_date <= '{Q1_END}';"
).iloc[0]["value"]

# Illustrative question 1 asks for the worst outlets "last month" as a rule,
# not a fixed date. Computed here once, shared by Overview and Service, so
# it's dynamic and consistent everywhere instead of a hardcoded "June 2026"
# that silently goes stale the next time this runs against newer data.
import calendar as _calendar
_max_date_str = query_db("SELECT MAX(order_date) AS d FROM orders;").iloc[0]["d"]
_max_date = pd.Timestamp(_max_date_str)
_last_day_of_max_month = _calendar.monthrange(_max_date.year, _max_date.month)[1]
if _max_date.day == _last_day_of_max_month:
    _lm_year, _lm_month = _max_date.year, _max_date.month
else:
    _prev_month_date = _max_date.replace(day=1) - pd.Timedelta(days=1)
    _lm_year, _lm_month = _prev_month_date.year, _prev_month_date.month
_lm_start = f"{_lm_year:04d}-{_lm_month:02d}-01"
_lm_end_day = _calendar.monthrange(_lm_year, _lm_month)[1]
_lm_end = f"{_lm_year:04d}-{_lm_month:02d}-{_lm_end_day:02d}"
_lm_label = _max_date.replace(year=_lm_year, month=_lm_month, day=1).strftime("%B %Y")

last_month_worst_outlets = query_db(
    f"""
    SELECT ot.outlet_code, ot.outlet_name,
           SUM(CASE WHEN ol.qty_uom='CASE'
                    THEN ol.ordered_qty*ol.case_pack_at_order ELSE ol.ordered_qty END) ordered_eaches,
           SUM(CASE WHEN ol.qty_uom='CASE'
                    THEN ol.delivered_qty*ol.case_pack_at_order ELSE ol.delivered_qty END) delivered_eaches
    FROM order_lines ol
    JOIN orders o ON ol.order_id=o.order_id
    JOIN outlets ot ON o.outlet_id=ot.outlet_id
    WHERE o.order_status IN ('DELIVERED','PARTIAL')
      AND o.order_date BETWEEN '{_lm_start}' AND '{_lm_end}'
      AND ot.status='ACTIVE' AND ot.is_deleted=0 AND ot.outlet_id NOT IN (721,722,723)
    GROUP BY ot.outlet_id,ot.outlet_code,ot.outlet_name
    HAVING ordered_eaches > 0
    ORDER BY delivered_eaches*1.0/ordered_eaches
    LIMIT 10;
    """
)
last_month_worst_outlets["short_eaches"] = last_month_worst_outlets.ordered_eaches - last_month_worst_outlets.delivered_eaches
last_month_worst_outlets["fill_rate"] = last_month_worst_outlets.delivered_eaches / last_month_worst_outlets.ordered_eaches * 100

# -----------------------------
# HERO
# -----------------------------
st.markdown(
    """
    <div class="hero">
        <div class="hero-title">Kestrel Supply Chain Control Tower</div>
        <div class="hero-sub">Operational command view across service, inventory, cold chain and logistics cost.</div>
        <div class="hero-pill">DATA THROUGH 30 JUN 2026</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# OVERVIEW
# -----------------------------
if page == "Overview":
    st.markdown('<div class="section-label">Q1 FY2026-27 | orders placed Apr-Jun 2026 (order_date): the board asks about Q1 first</div>', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        card("Fill rate (Q1)", f"{fill_rate:.2f}%", f"{ordered/1e6:.2f}M ordered → {delivered/1e6:.2f}M delivered")
    with c2:
        card("On-time (2hr std, Q1)", f"{on_time_rate_delay:.2f}%", "delay_minutes ≤ 120")
    with c3:
        card("On-time (by date, Q1)", f"{on_time_rate_date:.2f}%", "vs requested_delivery_date")
    with c4:
        card("Near-expiry available", fmt_int(near_expiry["available"]), "Cases expiring within 30 days (current, not Q1)")
    with c5:
        card("Return value (Q1)", fmt_inr(returns_total), "Credit notes, Apr–Jun 2026")

    st.markdown('<div class="section-label">OTIF by region: Q1 FY2026-27</div>', unsafe_allow_html=True)
    st.caption(
        "OTIF = delivered in full (eaches ≥90%) AND on time (≤120 min late). "
        "90%, not 100%, because no order line in the whole dataset is ever delivered "
        "at exactly 100%. A literal 100% bar makes OTIF permanently 0% everywhere. "
        "See DECISIONS.md."
    )
    otif_df = pd.DataFrame(metrics.calculate_otif_by_region())
    st.dataframe(
        otif_df.style.format({
            "total_orders": "{:,.0f}",
            "otif_orders": "{:,.0f}",
            "otif_pct": "{:.1f}%",
        }),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown('<div class="section-label">Executive signals</div>', unsafe_allow_html=True)

    _worst_outlet_fill = last_month_worst_outlets["fill_rate"].min() if not last_month_worst_outlets.empty else None

    s1, s2, s3 = st.columns(3)
    with s1:
        st.markdown(
            f"""
            <div class="signal signal-danger">
                <div class="signal-title">Service reliability</div>
                <div class="signal-body">
                Q1 fill is {fill_rate:.2f}%. On-time performance is {on_time_rate_delay:.2f}%
                (2hr standard) / {on_time_rate_date:.2f}% (by requested date).
                {_lm_label} outlet performance falls as low as {_worst_outlet_fill:.2f}%.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with s2:
        st.markdown(
            f"""
            <div class="signal signal-warn">
                <div class="signal-title">Expiry exposure</div>
                <div class="signal-body">
                {fmt_int(near_expiry['available'])} available cases are within 30 days of
                expiry (latest snapshot). Near-expiry is the leading return reason across
                every product category. See Inventory &amp; Returns.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with s3:
        st.markdown(
            """
            <div class="signal signal-warn">
                <div class="signal-title">Cold-chain data quality</div>
                <div class="signal-body">
                Excursion flags exist on non-reefer deliveries.
                Validate vehicle classification and telematics before acting.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-label">Service snapshot</div>', unsafe_allow_html=True)

    region_df = query_db(
        """
        SELECT r.region_name AS region,
               SUM(CASE WHEN ol.qty_uom='CASE'
                        THEN ol.ordered_qty*ol.case_pack_at_order
                        ELSE ol.ordered_qty END) ordered_eaches,
               SUM(CASE WHEN ol.qty_uom='CASE'
                        THEN ol.delivered_qty*ol.case_pack_at_order
                        ELSE ol.delivered_qty END) delivered_eaches
        FROM order_lines ol
        JOIN orders o ON ol.order_id=o.order_id
        JOIN regions r ON o.region_id=r.region_id
        JOIN outlets ot ON o.outlet_id=ot.outlet_id
        WHERE o.order_status IN ('DELIVERED','PARTIAL')
          AND ot.status='ACTIVE' AND ot.is_deleted=0 AND ot.outlet_id NOT IN (721,722,723)
        GROUP BY r.region_id,r.region_name
        ORDER BY region;
        """
    )
    region_df["fill_rate"] = region_df.delivered_eaches / region_df.ordered_eaches * 100

    route_df = query_db(
        """
        SELECT r.route_code AS route,
               SUM(CASE WHEN ol.qty_uom='CASE'
                        THEN ol.ordered_qty*ol.case_pack_at_order
                        ELSE ol.ordered_qty END) ordered_eaches,
               SUM(CASE WHEN ol.qty_uom='CASE'
                        THEN ol.delivered_qty*ol.case_pack_at_order
                        ELSE ol.delivered_qty END) delivered_eaches
        FROM order_lines ol
        JOIN orders o ON ol.order_id=o.order_id
        JOIN routes r ON o.route_id=r.route_id
        JOIN outlets ot ON o.outlet_id=ot.outlet_id
        WHERE o.order_status IN ('DELIVERED','PARTIAL')
          AND ot.status='ACTIVE' AND ot.is_deleted=0 AND ot.outlet_id NOT IN (721,722,723)
        GROUP BY r.route_id,r.route_code
        HAVING ordered_eaches > 0
        ORDER BY delivered_eaches * 1.0 / ordered_eaches
        LIMIT 10;
        """
    )
    route_df["fill_rate"] = route_df.delivered_eaches / route_df.ordered_eaches * 100

    a, b = st.columns([1.4, 1])
    with a:
        st.subheader("Regional fill")
        st.bar_chart(region_df.set_index("region")[["fill_rate"]], height=280)
    with b:
        st.subheader("Lowest-performing routes")
        rank_list(route_df, "route", "fill_rate", n=7, percent=True)

# -----------------------------
# SERVICE
# -----------------------------
elif page == "Service":
    st.subheader("Service performance")
    st.caption("Fill rate is calculated in eaches, matching the Sales reporting definition (based on order_date). Network service performance below uses all available history (18 months), not Q1-scoped; the OTIF sections further down are explicitly Q1.")

    region_df = query_db(
        """
        SELECT r.region_name AS region,
               SUM(CASE WHEN ol.qty_uom='CASE'
                        THEN ol.ordered_qty*ol.case_pack_at_order ELSE ol.ordered_qty END) ordered_eaches,
               SUM(CASE WHEN ol.qty_uom='CASE'
                        THEN ol.delivered_qty*ol.case_pack_at_order ELSE ol.delivered_qty END) delivered_eaches
        FROM order_lines ol
        JOIN orders o ON ol.order_id=o.order_id
        JOIN regions r ON o.region_id=r.region_id
        JOIN outlets ot ON o.outlet_id=ot.outlet_id
        WHERE o.order_status IN ('DELIVERED','PARTIAL')
          AND ot.status='ACTIVE' AND ot.is_deleted=0 AND ot.outlet_id NOT IN (721,722,723)
        GROUP BY r.region_id,r.region_name
        ORDER BY delivered_eaches*1.0/ordered_eaches;
        """
    )
    region_df["fill_rate"] = region_df.delivered_eaches / region_df.ordered_eaches * 100

    warehouse_df = query_db(
        """
        SELECT w.warehouse_name AS warehouse,
               SUM(CASE WHEN ol.qty_uom='CASE'
                        THEN ol.ordered_qty*ol.case_pack_at_order ELSE ol.ordered_qty END) ordered_eaches,
               SUM(CASE WHEN ol.qty_uom='CASE'
                        THEN ol.delivered_qty*ol.case_pack_at_order ELSE ol.delivered_qty END) delivered_eaches
        FROM order_lines ol
        JOIN orders o ON ol.order_id=o.order_id
        JOIN warehouses w ON o.warehouse_id=w.warehouse_id
        JOIN outlets ot ON o.outlet_id=ot.outlet_id
        WHERE o.order_status IN ('DELIVERED','PARTIAL')
          AND ot.status='ACTIVE' AND ot.is_deleted=0 AND ot.outlet_id NOT IN (721,722,723)
        GROUP BY w.warehouse_id,w.warehouse_name
        ORDER BY delivered_eaches*1.0/ordered_eaches;
        """
    )
    warehouse_df["fill_rate"] = warehouse_df.delivered_eaches / warehouse_df.ordered_eaches * 100

    t1, t2 = st.tabs(["Regions", "Warehouses"])
    with t1:
        st.bar_chart(region_df.set_index("region")[["fill_rate"]], height=360)
        st.dataframe(
            region_df.style.format({
                "ordered_eaches": "{:,.0f}",
                "delivered_eaches": "{:,.0f}",
                "fill_rate": "{:.2f}%"
            }),
            use_container_width=True,
            hide_index=True,
        )
    with t2:
        st.bar_chart(warehouse_df.set_index("warehouse")[["fill_rate"]], height=360)
        st.dataframe(
            warehouse_df.style.format({
                "ordered_eaches": "{:,.0f}",
                "delivered_eaches": "{:,.0f}",
                "fill_rate": "{:.2f}%"
            }),
            use_container_width=True,
            hide_index=True,
        )

    st.subheader("Worst performers")
    st.caption("18-month historical view, not Q1-scoped.")

    route_df = query_db(
        """
        SELECT r.route_code AS route,
               SUM(CASE WHEN ol.qty_uom='CASE'
                        THEN ol.ordered_qty*ol.case_pack_at_order ELSE ol.ordered_qty END) ordered_eaches,
               SUM(CASE WHEN ol.qty_uom='CASE'
                        THEN ol.delivered_qty*ol.case_pack_at_order ELSE ol.delivered_qty END) delivered_eaches
        FROM order_lines ol
        JOIN orders o ON ol.order_id=o.order_id
        JOIN routes r ON o.route_id=r.route_id
        JOIN outlets ot ON o.outlet_id=ot.outlet_id
        WHERE o.order_status IN ('DELIVERED','PARTIAL')
          AND ot.status='ACTIVE' AND ot.is_deleted=0 AND ot.outlet_id NOT IN (721,722,723)
        GROUP BY r.route_id,r.route_code
        HAVING ordered_eaches > 0
        ORDER BY delivered_eaches*1.0/ordered_eaches
        LIMIT 10;
        """
    )
    route_df["short_eaches"] = route_df.ordered_eaches - route_df.delivered_eaches
    route_df["fill_rate"] = route_df.delivered_eaches / route_df.ordered_eaches * 100

    outlet_df = query_db(
        """
        SELECT ot.outlet_code, ot.outlet_name,
               SUM(CASE WHEN ol.qty_uom='CASE'
                        THEN ol.ordered_qty*ol.case_pack_at_order ELSE ol.ordered_qty END) ordered_eaches,
               SUM(CASE WHEN ol.qty_uom='CASE'
                        THEN ol.delivered_qty*ol.case_pack_at_order ELSE ol.delivered_qty END) delivered_eaches
        FROM order_lines ol
        JOIN orders o ON ol.order_id=o.order_id
        JOIN outlets ot ON o.outlet_id=ot.outlet_id
        WHERE o.order_status IN ('DELIVERED','PARTIAL')
          AND ot.status='ACTIVE' AND ot.is_deleted=0 AND ot.outlet_id NOT IN (721,722,723)
        GROUP BY ot.outlet_id,ot.outlet_code,ot.outlet_name
        HAVING ordered_eaches > 0
        ORDER BY delivered_eaches*1.0/ordered_eaches
        LIMIT 10;
        """
    )
    outlet_df["short_eaches"] = outlet_df.ordered_eaches - outlet_df.delivered_eaches
    outlet_df["fill_rate"] = outlet_df.delivered_eaches / outlet_df.ordered_eaches * 100

    x, y = st.columns(2)
    with x:
        st.markdown("**Worst routes**")
        st.dataframe(
            route_df[["route","ordered_eaches","delivered_eaches","short_eaches","fill_rate"]].style.format({
                "ordered_eaches": "{:,.0f}",
                "delivered_eaches": "{:,.0f}",
                "short_eaches": "{:,.0f}",
                "fill_rate": "{:.2f}%"
            }),
            use_container_width=True,
            hide_index=True,
        )
    with y:
        st.markdown("**Worst outlets**")
        st.dataframe(
            outlet_df[["outlet_code","outlet_name","ordered_eaches","delivered_eaches","short_eaches","fill_rate"]].style.format({
                "ordered_eaches": "{:,.0f}",
                "delivered_eaches": "{:,.0f}",
                "short_eaches": "{:,.0f}",
                "fill_rate": "{:.2f}%"
            }),
            use_container_width=True,
            hide_index=True,
        )

    # Illustrative question 1 asks for "last month" as a rule, not a fixed
    # date. The original code hardcoded June 2026; this is computed dynamically here:
    # last complete month = the most recent calendar month fully covered by
    # the data (if the data's max date is the last day of its month, that
    # month counts; otherwise the month before it does).
    import calendar as _calendar
    st.subheader(f"{_lm_label} early-warning outlets (worst 5+ by eaches fill rate)")
    st.caption("Illustrative Q1 asks for the worst outlets \"last month\" as computed dynamically from the data's latest date, not hardcoded. Same underlying query used in the Overview signal card.")
    st.dataframe(
        last_month_worst_outlets.style.format({
            "ordered_eaches": "{:,.0f}",
            "delivered_eaches": "{:,.0f}",
            "short_eaches": "{:,.0f}",
            "fill_rate": "{:.2f}%"
        }),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Routes >10% of deliveries more than 2hrs late")
    late_routes_df = pd.DataFrame(metrics.calculate_late_routes())
    if late_routes_df.empty:
        st.markdown("<p style='color:#888'>No routes exceed a 10% late-delivery rate.</p>", unsafe_allow_html=True)
    else:
        st.dataframe(
            late_routes_df.style.format({
                "total_deliveries": "{:,.0f}",
                "late_deliveries": "{:,.0f}",
                "late_pct": "{:.1f}%",
            }),
            use_container_width=True,
            hide_index=True,
        )

    st.subheader("OTIF by warehouse: Q1 FY2026-27")
    st.caption("Same definition as the Overview OTIF table (eaches fill ≥90% AND delay ≤120 min). Warehouse-level is also close to uniform: the shortfall isn't concentrated at any single site.")
    otif_wh_df = pd.DataFrame(metrics.calculate_otif_by("warehouse"))
    st.dataframe(
        otif_wh_df.style.format({"total_orders": "{:,.0f}", "otif_orders": "{:,.0f}", "otif_pct": "{:.1f}%"}),
        use_container_width=True, hide_index=True,
    )

    st.subheader("Worst 10 routes and outlets by OTIF: Q1 FY2026-27")
    st.caption("Unlike region/warehouse, real variance shows up here: some routes and outlets sit at 0% OTIF for the quarter.")
    otif_col1, otif_col2 = st.columns(2)
    with otif_col1:
        st.markdown("**Routes**")
        otif_route_df = pd.DataFrame(metrics.calculate_otif_by("route", limit=10))
        st.dataframe(
            otif_route_df.style.format({"total_orders": "{:,.0f}", "otif_orders": "{:,.0f}", "otif_pct": "{:.1f}%"}),
            use_container_width=True, hide_index=True,
        )
    with otif_col2:
        st.markdown("**Outlets**")
        otif_outlet_df = pd.DataFrame(metrics.calculate_otif_by("outlet", limit=10))
        st.dataframe(
            otif_outlet_df.style.format({"total_orders": "{:,.0f}", "otif_orders": "{:,.0f}", "otif_pct": "{:.1f}%"}),
            use_container_width=True, hide_index=True,
        )

    st.subheader("Outlets ordering discontinued SKUs")
    st.caption("Orders placed after a SKU's discontinuation date. Excludes closed/test/deleted outlets.")
    disc_df = pd.DataFrame(metrics.calculate_discontinued_sku_orders())
    st.markdown(f"**{len(disc_df):,} order lines found** across **{disc_df['sku_code'].nunique() if not disc_df.empty else 0} discontinued SKUs**, showing the 15 most recent:")
    if not disc_df.empty:
        st.dataframe(
            disc_df.sort_values("order_date", ascending=False).head(15).style.format({
                "ordered_qty": "{:,.0f}",
            }),
            use_container_width=True,
            hide_index=True,
        )

# -----------------------------
# INVENTORY
# -----------------------------
elif page == "Inventory & Returns":
    st.subheader("Inventory & returns")

    inv_df = query_db(
        """
        SELECT w.warehouse_name AS warehouse,
               SUM(i.on_hand_cases) AS on_hand_cases,
               SUM(i.available_cases) AS available_cases
        FROM inventory_snapshots i
        JOIN warehouses w ON i.warehouse_id=w.warehouse_id
        WHERE i.expiry_date IS NOT NULL
          AND DATE(i.expiry_date) >= DATE(i.snapshot_date)
          AND DATE(i.expiry_date) <= DATE(i.snapshot_date,'+30 days')
          AND i.snapshot_date = (SELECT MAX(snapshot_date) FROM inventory_snapshots)
        GROUP BY w.warehouse_id,w.warehouse_name
        ORDER BY available_cases DESC;
        """
    )

    returns_df = query_db(
        """
        SELECT return_reason_code AS reason,
               COUNT(*) AS return_lines,
               SUM(return_qty) AS return_qty,
               SUM(credit_note_value_inr) AS return_value
        FROM returns_credit_notes
        GROUP BY return_reason_code
        ORDER BY return_value DESC;
        """
    )

    a, b = st.columns(2)
    with a:
        st.subheader("Near-expiry by warehouse")
        st.bar_chart(inv_df.set_index("warehouse")[["available_cases"]], height=340)
        st.dataframe(
            inv_df.style.format({
                "on_hand_cases": "{:,.0f}",
                "available_cases": "{:,.0f}"
            }),
            use_container_width=True,
            hide_index=True,
        )
    with b:
        st.subheader("Returns by reason")
        st.caption("All available history, not Q1-scoped. Kept as full history for signal; explicitly labeled so the scope isn't assumed to match the Q1 KPIs on Overview.")
        st.bar_chart(returns_df.set_index("reason")[["return_value"]], height=340)
        st.dataframe(
            returns_df.style.format({
                "return_qty": "{:,.0f}",
                "return_value": "₹{:,.2f}"
            }),
            use_container_width=True,
            hide_index=True,
        )

    st.subheader("Returns by category, with leading reason code")
    st.caption("All available history, not Q1-scoped. Illustrative question 3, answered as literally asked: category totals AND the leading reason per category, not just one or the other.")
    cat_reason_df = pd.DataFrame(metrics.calculate_returns_by_category())
    st.dataframe(
        cat_reason_df.style.format({
            "return_lines": "{:,.0f}",
            "return_value": "₹{:,.2f}",
        }),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Returns & credit notes as % of dispatch value, by region")
    st.caption("All available history, not Q1-scoped. Explicit pillar-3 ask. Dispatch value = order_value_net_inr on delivered/partial orders, active outlets only.")
    disp_pct_df = pd.DataFrame(metrics.calculate_returns_pct_of_dispatch())
    st.dataframe(
        disp_pct_df.style.format({
            "dispatch_value": "₹{:,.0f}",
            "return_value": "₹{:,.0f}",
            "return_pct": "{:.2f}%",
        }),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown(
        f"""
        <div class="signal signal-warn">
            <div class="signal-title">Inventory action</div>
            <div class="signal-body">
            {fmt_int(near_expiry['available'])} available cases sit within 30 days of expiry
            (latest snapshot). Prioritize FEFO, warehouse-to-warehouse redistribution and
            targeted sell-through before expiry converts into returns.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# -----------------------------
# COLD CHAIN
# -----------------------------
elif page == "Cold Chain":
    st.subheader("Cold-chain integrity")
    st.caption("Reefer classification is taken from route master data; excursion flags come from delivery records.")

    # LEFT JOIN deliberately preserves every eligible delivery even if a route master record is missing.
    cold = query_db(
        """
        SELECT
            COUNT(*) AS total_deliveries,
            SUM(CASE WHEN COALESCE(r.is_reefer,0)=1 THEN 1 ELSE 0 END) AS reefer_deliveries,
            SUM(CASE WHEN d.temperature_excursion_flag=1 THEN 1 ELSE 0 END) AS excursions,
            SUM(CASE WHEN COALESCE(r.is_reefer,0)=1
                      AND d.temperature_excursion_flag=1
                     THEN 1 ELSE 0 END) AS reefer_excursions,
            SUM(CASE WHEN COALESCE(r.is_reefer,0)=0
                      AND d.temperature_excursion_flag=1
                     THEN 1 ELSE 0 END) AS non_reefer_excursions
        FROM deliveries d
        LEFT JOIN routes r ON d.route_id=r.route_id
        WHERE d.delivery_status IN ('DELIVERED','PARTIAL');
        """
    ).iloc[0]

    reefer_deliveries = int(cold["reefer_deliveries"])
    reefer_excursions = int(cold["reefer_excursions"])
    non_reefer = int(cold["non_reefer_excursions"])
    reefer_rate = reefer_excursions / reefer_deliveries * 100 if reefer_deliveries else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card("Reefer deliveries", fmt_int(reefer_deliveries), "Eligible delivered / partial deliveries")
    with c2:
        card("Reefer excursions", fmt_int(reefer_excursions), "Temperature excursion flags")
    with c3:
        card("Excursion rate", f"{reefer_rate:.2f}%", "Reefer excursions / reefer deliveries")
    with c4:
        card("Non-reefer flags", fmt_int(non_reefer), "Requires classification validation")

    if non_reefer:
        st.markdown(
            f"""
            <div class="signal signal-warn" style="margin-top:16px">
                <div class="signal-title">Data-quality exception</div>
                <div class="signal-body">
                {non_reefer:,} temperature excursion flags are attached to non-reefer
                deliveries. Validate telematics mapping, vehicle classification and
                route master data before treating these as genuine cold-chain failures.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.subheader("Excursions by vehicle / route type")
    route_type_df = query_db(
        """
        SELECT r.vehicle_type AS route_type,
               r.is_reefer AS reefer,
               COUNT(*) AS deliveries,
               SUM(CASE WHEN d.temperature_excursion_flag=1 THEN 1 ELSE 0 END) AS excursions
        FROM deliveries d
        JOIN routes r ON d.route_id=r.route_id
        WHERE d.delivery_status IN ('DELIVERED','PARTIAL')
        GROUP BY r.vehicle_type,r.is_reefer
        ORDER BY excursions DESC;
        """
    )
    route_type_df["excursion_rate"] = route_type_df.excursions / route_type_df.deliveries * 100
    st.dataframe(
        route_type_df.style.format({
            "deliveries": "{:,.0f}",
            "excursions": "{:,.0f}",
            "excursion_rate": "{:.2f}%"
        }),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Excursions per 100 chilled deliveries, by month")
    exc_month_df = pd.DataFrame(metrics.calculate_excursions_by_month())
    st.line_chart(exc_month_df.set_index("month")[["excursions_per_100"]], height=280)
    st.dataframe(
        exc_month_df.style.format({
            "chilled_deliveries": "{:,.0f}",
            "excursions": "{:,.0f}",
            "excursions_per_100": "{:.2f}",
        }),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Returns caused specifically by cold-chain breach")
    st.caption("return_reason_code = RT06_COLD_CHAIN_BREACH. Divya's pillar 2 explicitly asks for this, separate from general returns.")
    cc_returns_df = pd.DataFrame(metrics.calculate_cold_chain_returns())
    st.dataframe(
        cc_returns_df.style.format({
            "return_lines": "{:,.0f}",
            "return_value": "₹{:,.2f}",
        }),
        use_container_width=True,
        hide_index=True,
    )

# -----------------------------
# FREIGHT + PRICE
# -----------------------------
elif page == "Freight & Price":
    st.subheader("Freight cost")
    st.caption("Q1 FY2027 | 1 April 2026 – 30 June 2026 · Live from the Partner API, not a proxy")

    if "freight_data" not in st.session_state:
        st.session_state.freight_data = None
    if "carrier_data" not in st.session_state:
        st.session_state.carrier_data = None

    fcol1, fcol2 = st.columns([1, 3])
    with fcol1:
        fetch_freight = st.button("Fetch live freight data", use_container_width=True)
    with fcol2:
        st.caption(
            "Pulls ~7,100 real invoices through the Partner API's deliberate rate limiting "
            "(~2 min). Requires `python partner_api/server.py` running at localhost:8088. "
            "Not fetched automatically on page load. Powers both the warehouse and carrier "
            "breakdowns below from a single pull."
        )

    if fetch_freight:
        with st.spinner("Fetching and reconciling freight invoices... this takes about 2 minutes"):
            try:
                invoices = live_metrics.get_freight_invoices()
                st.session_state.freight_data = live_metrics.get_freight_cost_by_warehouse(invoices)
                st.session_state.carrier_data = live_metrics.get_freight_cost_by_carrier(invoices)
            except ConnectionError as e:
                st.session_state.freight_data = None
                st.session_state.carrier_data = None
                st.error(str(e))

    if st.session_state.freight_data:
        freight_df = pd.DataFrame(st.session_state.freight_data)

        c1, c2 = st.columns(2)
        with c1:
            cheapest = freight_df.loc[freight_df.cost_per_case.idxmin()]
            card("Lowest cost / case", fmt_inr(cheapest.cost_per_case), cheapest.warehouse)
        with c2:
            priciest = freight_df.loc[freight_df.cost_per_case.idxmax()]
            card("Highest cost / case", fmt_inr(priciest.cost_per_case), priciest.warehouse)

        st.bar_chart(freight_df.set_index("warehouse")[["cost_per_case"]], height=360)
        st.dataframe(
            freight_df[["warehouse", "city", "delivered_cases", "freight_inr", "cost_per_case"]].style.format({
                "delivered_cases": "{:,.0f}",
                "freight_inr": "₹{:,.2f}",
                "cost_per_case": "₹{:,.2f}",
            }),
            use_container_width=True,
            hide_index=True,
        )

        st.subheader("Freight leakage by carrier")
        st.caption("Explicit pillar-3 ask: \"leakage by category and by carrier.\" Category is covered in Inventory & Returns; this is the carrier half.")
        carrier_df = pd.DataFrame(st.session_state.carrier_data)
        st.bar_chart(carrier_df.set_index("carrier")[["total_freight_inr"]], height=280)
        st.dataframe(
            carrier_df.style.format({
                "invoice_count": "{:,.0f}",
                "total_freight_inr": "₹{:,.2f}",
                "detention_inr": "₹{:,.2f}",
                "avg_invoice_inr": "₹{:,.2f}",
            }),
            use_container_width=True,
            hide_index=True,
        )

        st.markdown(
            f"""
            <div class="signal">
                <div class="signal-title">Interpretation</div>
                <div class="signal-body">
                Cost per delivered case ranges from {fmt_inr(freight_df.cost_per_case.min())} to
                {fmt_inr(freight_df.cost_per_case.max())}, computed from real Partner API invoices
                reconciled against Q1 delivered cases (outlet-filtered, same rule as Service).
                Treat this as an investigation signal, not proof of warehouse inefficiency.
                normalize for route distance, shipment weight, vehicle type, carrier and service mix
                before drawing conclusions.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.info("Click \"Fetch live freight data\" above to pull real, reconciled freight cost per case.")

    st.subheader("Price position")
    st.caption("Kestrel SKUs in the Top-20 sales-value cohort · Mumbai listings only, live from BazaarPulse")

    if "price_data" not in st.session_state:
        with st.spinner("Matching Kestrel SKUs against BazaarPulse listings..."):
            st.session_state.price_data = live_metrics.get_top20_price_position()

    price_rows = st.session_state.price_data
    price_df = pd.DataFrame([{
        "SKU": r["sku"],
        "Product": r["product_name"],
        "Sales Value": r["sales_value"],
        "Kestrel MRP": r["kestrel_mrp"],
        "Market Price": r["market_price"],
        "Gap": r["gap_pct"],
        "Confidence": (
            "No validated match" if r["best_match"] is None
            else "Directional: single generic word match" if r["single_generic_word_match"]
            else "Directional"
        ),
    } for r in price_rows])

    st.dataframe(
        price_df.style.format({
            "Sales Value": "₹{:,.0f}",
            "Kestrel MRP": "₹{:,.2f}",
            "Market Price": lambda x: f"₹{x:,.2f}" if pd.notna(x) else "N/A",
            "Gap": lambda x: f"{x:+.2f}%" if pd.notna(x) else "N/A",
        }),
        use_container_width=True,
        hide_index=True,
    )

    _flagged_rows = [r for r in price_rows if r["single_generic_word_match"] and r["gap_pct"] is not None]
    _example_gap = f"{_flagged_rows[0]['gap_pct']:+.2f}%" if _flagged_rows else "the reported"
    st.caption(
        "Only 3 of the Top-20 SKUs by sales value are Kestrel-branded, and only Mumbai listings "
        "are checked (see DECISIONS.md for scope). Matches require same pack size AND ≥75% "
        "overlap of significant name words after stripping brand/marketing terms. The Atta match "
        "is flagged \"single generic word match\": after removing brand words, \"ATTA\" is the "
        f"only distinguishing word, so a {_example_gap} gap should be read as directional (comparing "
        "against some 200ml atta product), not as a validated like-for-like comparison."
    )

# -----------------------------
# DIVYA'S QUESTIONS
# -----------------------------
elif page == "Divya's Questions":
    st.subheader("Divya's 8 questions, answered directly")
    st.caption(
        "The assignment brief lists these as illustrative, not a spec but a sense-check. "
        "Each answer below runs a real query against the database (or, for freight/price, "
        "live data) when you select it. Not a general-purpose question box; see DECISIONS.md "
        "for why a small, honest version of this beats a general one we couldn't fully validate."
    )

    QUESTIONS = [
        "1. Which five outlets had the lowest case fill rate last month, excluding closed and test outlets?",
        "2. What was OTIF by region for the last complete quarter?",
        "3. Which categories drive the largest value of returns, and what is the leading reason code?",
        "4. Temperature excursions per hundred chilled deliveries, by month.",
        "5. Which routes are more than two hours late on more than one delivery in ten?",
        "6. For our top twenty SKUs by value, how does our MRP compare with the lowest observed competitor price in Mumbai?",
        "7. Freight cost per delivered case, by warehouse, for the last quarter.",
        "8. Which outlets ordered a discontinued SKU after its discontinuation date?",
    ]
    choice = st.selectbox("Pick a question", QUESTIONS, label_visibility="collapsed")

    if choice.startswith("1."):
        q1_df = pd.DataFrame(metrics.calculate_worst_outlets_by_case_fill_rate(_lm_start, _lm_end, 5))
        st.markdown(f"**Answer, for {_lm_label} (computed as the last complete calendar month in the data, not hardcoded):**")
        st.dataframe(
            q1_df.style.format({
                "ordered_cases": "{:,.1f}", "delivered_cases": "{:,.1f}", "case_fill_rate_pct": "{:.2f}%",
            }),
            use_container_width=True, hide_index=True,
        )
        st.caption("This is the one place cases fill rate is shown; everywhere else on this dashboard reports eaches, per Sales' override. See DECISIONS.md.")

    elif choice.startswith("2."):
        q2_df = pd.DataFrame(metrics.calculate_otif_by_region())
        st.markdown(f"**Answer, Q1 FY2026-27 ({Q1_START} to {Q1_END}):**")
        st.dataframe(
            q2_df.style.format({"total_orders": "{:,.0f}", "otif_orders": "{:,.0f}", "otif_pct": "{:.1f}%"}),
            use_container_width=True, hide_index=True,
        )
        st.caption("OTIF = eaches fill ≥90% AND delay ≤120 min. 90%, not 100%, because zero order lines in the whole dataset are ever delivered at exactly 100%; see DECISIONS.md.")

    elif choice.startswith("3."):
        q3_df = pd.DataFrame(metrics.calculate_returns_by_category())
        st.markdown("**Answer:**")
        st.dataframe(
            q3_df.style.format({"return_lines": "{:,.0f}", "return_value": "₹{:,.2f}"}),
            use_container_width=True, hide_index=True,
        )
        _top_cat = q3_df.iloc[0]
        st.caption(f"{_top_cat['category']} drives the largest return value (₹{_top_cat['return_value']:,.0f}), led by {_top_cat['leading_reason']}. Notably, that same reason code leads in every category, not just this one.")

    elif choice.startswith("4."):
        q4_df = pd.DataFrame(metrics.calculate_excursions_by_month())
        st.markdown("**Answer:**")
        st.line_chart(q4_df.set_index("month")[["excursions_per_100"]], height=280)
        st.dataframe(
            q4_df.style.format({"chilled_deliveries": "{:,.0f}", "excursions": "{:,.0f}", "excursions_per_100": "{:.2f}"}),
            use_container_width=True, hide_index=True,
        )

    elif choice.startswith("5."):
        q5_df = pd.DataFrame(metrics.calculate_late_routes(min_late_pct=10))
        st.markdown(f"**Answer: {len(q5_df)} routes exceed a 10% rate of deliveries more than 2 hours late.**")
        st.dataframe(
            q5_df.style.format({"total_deliveries": "{:,.0f}", "late_deliveries": "{:,.0f}", "late_pct": "{:.1f}%"}),
            use_container_width=True, hide_index=True,
        )

    elif choice.startswith("6."):
        q6_rows = live_metrics.get_top20_price_position()
        q6_df = pd.DataFrame([{
            "SKU": r["sku"], "Product": r["product_name"], "Kestrel MRP": r["kestrel_mrp"],
            "Lowest Mumbai Price": r["market_price"], "Gap": r["gap_pct"],
            "Confidence": "No validated match" if r["best_match"] is None
                          else "Single generic word match" if r["single_generic_word_match"]
                          else "Validated",
        } for r in q6_rows])
        st.markdown("**Answer:** (only 3 of the Top-20 SKUs by sales value are Kestrel-branded; Mumbai listings only)")
        st.dataframe(
            q6_df.style.format({
                "Kestrel MRP": "₹{:,.2f}",
                "Lowest Mumbai Price": lambda x: f"₹{x:,.2f}" if pd.notna(x) else "N/A",
                "Gap": lambda x: f"{x:+.2f}%" if pd.notna(x) else "N/A",
            }),
            use_container_width=True, hide_index=True,
        )

    elif choice.startswith("7."):
        if st.session_state.get("freight_data"):
            q7_df = pd.DataFrame(st.session_state.freight_data)
            st.markdown("**Answer, Q1 FY2026-27, live from the Partner API:**")
            st.dataframe(
                q7_df[["warehouse", "city", "delivered_cases", "freight_inr", "cost_per_case"]].style.format({
                    "delivered_cases": "{:,.0f}", "freight_inr": "₹{:,.2f}", "cost_per_case": "₹{:,.2f}",
                }),
                use_container_width=True, hide_index=True,
            )
        else:
            st.info(
                "This needs a live pull from the Partner API (~2 min) that hasn't been fetched yet this "
                "session. Go to the **Freight & Price** tab, click \"Fetch live freight data,\" then come "
                "back here; the answer will use that same result, not fetch twice."
            )

    elif choice.startswith("8."):
        q8_df = pd.DataFrame(metrics.calculate_discontinued_sku_orders())
        st.markdown(f"**Answer: {len(q8_df):,} order lines found, across {q8_df['sku_code'].nunique() if not q8_df.empty else 0} discontinued SKUs.** Showing the 15 most recent:")
        if not q8_df.empty:
            st.dataframe(
                q8_df.sort_values("order_date", ascending=False).head(15).style.format({"ordered_qty": "{:,.0f}"}),
                use_container_width=True, hide_index=True,
            )

# -----------------------------
# FOOTER
# -----------------------------
st.divider()
st.caption(
    "Kestrel Control Tower  ·  Operational SQLite database  ·  "
    "Fill rate reported in eaches as requested by Sales"
)
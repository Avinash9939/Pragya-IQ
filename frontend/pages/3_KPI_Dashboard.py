import os
import streamlit as st

from frontend.components.auth_guard import require_login
from frontend.components.sidebar import render_sidebar_header, render_sidebar_nav

# ── Auth & Layout ──────────────────────────────────────────────
require_login()



import datetime
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from frontend.services import api_client
from frontend.utils.formatting import format_currency, format_percentage, format_number
from frontend.utils.schema_detector import detect_schema, get_dashboard_title, get_domain_kpis, compute_kpi, generate_ai_insights
from frontend.utils.domain_generator import generate_domain_dataset

# ── US State name map ──────────────────────────────────────────
us_state_names = {
    'AL':'Alabama','AK':'Alaska','AZ':'Arizona','AR':'Arkansas','CA':'California',
    'CO':'Colorado','CT':'Connecticut','DE':'Delaware','DC':'District of Columbia','FL':'Florida','GA':'Georgia',
    'HI':'Hawaii','ID':'Idaho','IL':'Illinois','IN':'Indiana','IA':'Iowa',
    'KS':'Kansas','KY':'Kentucky','LA':'Louisiana','ME':'Maine','MD':'Maryland',
    'MA':'Massachusetts','MI':'Michigan','MN':'Minnesota','MS':'Mississippi','MO':'Missouri',
    'MT':'Montana','NE':'Nebraska','NV':'Nevada','NH':'New Hampshire','NJ':'New Jersey',
    'NM':'New Mexico','NY':'New York','NC':'North Carolina','ND':'North Dakota','OH':'Ohio',
    'OK':'Oklahoma','OR':'Oregon','PA':'Pennsylvania','RI':'Rhode Island','SC':'South Carolina',
    'SD':'South Dakota','TN':'Tennessee','TX':'Texas','UT':'Utah','VT':'Vermont',
    'VA':'Virginia','WA':'Washington','WV':'West Virginia','WI':'Wisconsin','WY':'Wyoming'
}
state_to_code = {v.upper(): k for k, v in us_state_names.items()}

def _clean_numeric_col(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce").fillna(0.0)
    # Convert to string and clean up currency symbols, commas, percent signs
    s = series.astype(str).str.replace(r'[^\d.-]', '', regex=True)
    return pd.to_numeric(s, errors="coerce").fillna(0.0)

# ── General CSS (moved below page config) ───────────────────────
st.markdown("""
<style>
/* App core background */
.stApp {
    background-color: #080914 !important;
    color: #F8FAFC !important;
}

/* Hide Streamlit default menus & header spacing */
[data-testid="stSidebarNav"] { display: none !important; }
[data-testid="stHeader"] { display: none !important; }

div.block-container {
    padding-top: 0.5rem !important; padding-bottom: 0rem !important;
    padding-left: 1.5rem !important; padding-right: 1.5rem !important;
}

/* Custom rounded glassmorphic box layouts */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: rgba(13, 15, 30, 0.45) !important;
    border-radius: 12px !important; 
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;
    padding: 12px 14px !important;
    margin-bottom: 8px !important;
}
div[data-testid="stVerticalBlock"] > div { padding-bottom: 0px !important; margin-bottom: 0px !important; }
div[data-testid="stHorizontalBlock"] { gap: 1rem !important; }
div.element-container { margin-bottom: 0px !important; }
hr { margin-top: 0.4rem !important; margin-bottom: 0.4rem !important; border-color: rgba(255,255,255,0.06); }

/* Header titles */
.dashboard-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0px;
    margin-bottom: 4px;
}
.dashboard-title-wrapper {
    display: flex;
    flex-direction: column;
}
.dashboard-title {
    font-size: 1.45rem;
    font-weight: 700;
    color: #F8FAFC;
    margin: 0;
    letter-spacing: -0.02em;
}
.dashboard-subtitle {
    font-size: 0.78rem;
    color: #94A3B8;
    margin-top: 2px;
}

/* Header metadata chips */
.meta-chips-container {
    display: flex;
    gap: 8px;
    align-items: center;
}
.meta-chip {
    background-color: rgba(30, 41, 59, 0.4);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 0.70rem;
    color: #E2E8F0;
    display: flex;
    align-items: center;
    gap: 5px;
    font-weight: 500;
}
.meta-chip-domain {
    background-color: rgba(168, 85, 247, 0.12) !important;
    border: 1px solid rgba(168, 85, 247, 0.35) !important;
    color: #C084FC !important;
    text-transform: uppercase;
    font-weight: 600;
    letter-spacing: 0.03em;
}
.last-updated {
    font-size: 0.70rem;
    color: #64748B;
    display: flex;
    align-items: center;
    gap: 4px;
}

/* KPI Card layouts */
.kpi-mini-card {
    background-color: rgba(13, 15, 30, 0.45);
    border-radius: 12px;
    padding: 12px 14px;
    border: 1px solid rgba(255, 255, 255, 0.05);
    box-shadow: 0 4px 15px rgba(0,0,0,0.25);
    color: #F8FAFC;
    height: 105px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}
.kpi-mini-title {
    font-size: 0.68rem;
    text-transform: uppercase;
    color: #94A3B8;
    font-weight: 600;
    letter-spacing: 0.03em;
    display: flex;
    align-items: center;
    gap: 4px;
}
.kpi-mini-value {
    font-size: 1.45rem;
    font-weight: 700;
    margin: 1px 0px;
}
.kpi-mini-trend {
    font-size: 0.65rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 3px;
}

/* Chart block headers */
p.chart-box-title {
    font-size: 0.72rem;
    font-weight: 700;
    color: #F8FAFC;
    margin-bottom: 8px !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    display: flex;
    align-items: center;
    gap: 5px;
}

/* AI Insights panel styling */
.ai-insights-container {
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding-top: 2px;
}

/* Hide column card scrollbars */
div[data-testid="column"] ::-webkit-scrollbar {
    display: none !important;
    width: 0 !important;
    height: 0 !important;
}
div[data-testid="column"] * {
    scrollbar-width: none !important;
    -ms-overflow-style: none !important;
}
div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlock"],
div[data-testid="stVerticalBlockBorderWrapper"] > div {
    overflow: hidden !important;
    overflow-y: hidden !important;
}
.ai-insight-item {
    font-size: 0.70rem;
    color: #E2E8F0;
    display: flex;
    align-items: flex-start;
    gap: 6px;
    line-height: 1.35;
}
.ai-insight-icon {
    font-size: 0.85rem;
    flex-shrink: 0;
    margin-top: 1px;
}
</style>
""", unsafe_allow_html=True)

# ── General Chart Styles ───────────────────────────────────────
_theme = st.session_state.get("theme", "dark")
_txt_color = "#334155" if _theme == "light" else "#94A3B8"

CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=_txt_color, size=8, family="Inter, sans-serif"),
    margin=dict(t=5, b=5, l=15, r=10)
)
COLORS = ["#8B5CF6", "#3B82F6", "#10B981", "#F59E0B", "#EC4899", "#FB923C", "#A78BFA"]
day_order   = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
month_order = ["January","February","March","April","May","June","July",
               "August","September","October","November","December"]

# ── Helper functions ───────────────────────────────────────────
@st.cache_data(show_spinner=False)
def _load_active_df(active_id, prefer_raw=False):
    try:
        datasets = api_client.list_datasets(force_refresh=True)
        active_dataset = next((d for d in datasets if d["id"] == active_id), None)
        if not active_dataset:
            return None, None
        user_id = st.session_state["user"]["id"]
        mapping  = active_dataset.get("column_mapping") or {}
        folder = f"../backend/storage/{user_id}"
        # Check both local workspace storage and C:\Project backend storage location
        if not os.path.exists(folder) or not any(f.startswith(f"{active_id}_") for f in os.listdir(folder) if os.path.exists(folder)):
            alt_folder = f"C:/Project/backend/storage/{user_id}"
            if os.path.exists(alt_folder):
                folder = alt_folder
        if not os.path.exists(folder):
            return None, None
        files   = os.listdir(folder)
        matches = [f for f in files if f.startswith(f"{active_id}_")]
        if not matches:
            return None, None
        selected = matches[0]
        if prefer_raw:
            # For baseline: pick file without _cleaned or _features suffix
            for m in matches:
                if "_cleaned" not in m and "_features" not in m and "_featured" not in m:
                    selected = m
                    break
        else:
            # Prioritize '_cleaned', then '_features'
            for sfx in ["_cleaned", "_features"]:
                found = False
                for m in matches:
                    if sfx == "_cleaned" and "_features" in m:
                        continue
                    if sfx in m:
                        selected = m
                        found = True
                        break
                if found:
                    break
        filepath = os.path.join(folder, selected)
        df = pd.read_csv(filepath) if filepath.lower().endswith(".csv") else pd.read_excel(filepath)
        return df, mapping
    except Exception as e:
        st.error(f"Error loading dataset: {e}")
        return None, None

def _apply_time_dim(df: pd.DataFrame, date_col: str, grain: str):
    if not date_col or not pd.api.types.is_datetime64_any_dtype(df[date_col]):
        df["_td"] = "All"
        return df, ["All"]
    if grain == "Day":
        df["_td"] = df[date_col].dt.day_name()
        vals = [d for d in day_order if d in df["_td"].unique()]
    elif grain == "Date":
        df["_td"] = df[date_col].dt.date
        vals = sorted(df["_td"].dropna().unique().tolist())
    elif grain == "Week":
        df["_td"] = df[date_col].dt.to_period("W").dt.start_time.dt.date
        vals = sorted(df["_td"].dropna().unique().tolist())
    elif grain == "Month":
        df["_td"] = df[date_col].dt.month_name()
        vals = [m for m in month_order if m in df["_td"].unique()]
    else:
        df["_td"] = df[date_col].dt.year
        vals = sorted(df["_td"].dropna().unique().tolist())
    return df, vals

def _chart_layout(height=130, **extra):
    lay = dict(**CHART_LAYOUT, height=height)
    lay.update(extra)
    return lay

def _generate_sparkline_and_trend(df: pd.DataFrame, spec: dict, schema: dict):
    trend_pct = 0.0
    spark_values = []
    
    date_col = schema.get("date_col")
    val_col = spec.get("col")
    agg = spec.get("agg", "sum")
    
    if val_col == "__len__":
        if date_col and date_col in df.columns:
            counts = df.groupby(df[date_col].dt.date if pd.api.types.is_datetime64_any_dtype(df[date_col]) else date_col).size()
            spark_values = counts.toList() if hasattr(counts, 'toList') else list(counts)
        else:
            chunk_size = max(1, len(df) // 10)
            spark_values = [len(df[i:i+chunk_size]) for i in range(0, len(df), chunk_size)]
    elif val_col == "__aov__":
        rev_col = spec.get("rev_col")
        ord_col = spec.get("ord_col")
        if rev_col and ord_col and rev_col in df.columns and ord_col in df.columns:
            if date_col and date_col in df.columns:
                g = df.groupby(df[date_col].dt.date if pd.api.types.is_datetime64_any_dtype(df[date_col]) else date_col)
                spark_values = [(group[rev_col].sum() / group[ord_col].nunique()) if group[ord_col].nunique() > 0 else 0 for _, group in g]
            else:
                chunk_size = max(1, len(df) // 10)
                spark_values = []
                for i in range(0, len(df), chunk_size):
                    chunk = df[i:i+chunk_size]
                    orders_count = chunk[ord_col].nunique()
                    spark_values.append((chunk[rev_col].sum() / orders_count) if orders_count > 0 else 0)
    elif val_col == "__total_profit__":
        def safe_series(col_id):
            if not col_id or col_id not in df.columns:
                return pd.Series(0.0, index=df.index)
            series = df[col_id]
            if pd.api.types.is_numeric_dtype(series):
                return series.fillna(0.0)
            return pd.to_numeric(series.astype(str).str.replace(r'[^\d.-]', '', regex=True), errors="coerce").fillna(0.0)

        prof_col = next((c for c in df.columns if c.lower() == "profit"), schema.get("profit_col"))
        sales_col = next((c for c in df.columns if c.lower() in ["sales", "revenue"]), schema.get("revenue_col"))
        cost_col = next((c for c in df.columns if c.lower() == "cost"), schema.get("cost_col"))
        
        df_temp = df.copy()
        if prof_col and prof_col in df.columns:
            df_temp["_prof_val"] = safe_series(prof_col)
        else:
            df_temp["_prof_val"] = safe_series(sales_col) - safe_series(cost_col)
            
        if date_col and date_col in df.columns:
            g = df_temp.groupby(df_temp[date_col].dt.date if pd.api.types.is_datetime64_any_dtype(df_temp[date_col]) else date_col)
            spark_values = g["_prof_val"].sum().tolist()
        else:
            chunk_size = max(1, len(df_temp) // 10)
            spark_values = [df_temp["_prof_val"][i:i+chunk_size].sum() for i in range(0, len(df_temp), chunk_size)]
    elif val_col in df.columns:
        if date_col and date_col in df.columns:
            g = df.groupby(df[date_col].dt.date if pd.api.types.is_datetime64_any_dtype(df[date_col]) else date_col)[val_col]
            if agg == "sum": spark_values = g.sum().tolist()
            elif agg == "mean": spark_values = g.mean().tolist()
            elif agg == "nunique": spark_values = g.nunique().tolist()
            else: spark_values = g.sum().tolist()
        else:
            chunk_size = max(1, len(df) // 10)
            spark_values = []
            for i in range(0, len(df), chunk_size):
                chunk = df[i:i+chunk_size]
                if agg == "sum": spark_values.append(chunk[val_col].sum())
                elif agg == "mean": spark_values.append(chunk[val_col].mean())
                elif agg == "nunique": spark_values.append(chunk[val_col].nunique())
                else: spark_values.append(chunk[val_col].sum())
                    
    spark_values = [v if pd.notna(v) and np.isfinite(v) else 0 for v in spark_values]
    
    if len(spark_values) >= 2:
        n = len(spark_values)
        if n >= 4:
            split = n // 2
            prev_val = sum(spark_values[:split]) / split
            curr_val = sum(spark_values[split:]) / (n - split)
        else:
            prev_val = spark_values[-2]
            curr_val = spark_values[-1]
            
        if prev_val > 0:
            trend_pct = ((curr_val - prev_val) / prev_val) * 100
        else:
            trend_pct = 0.0
            
    svg_html = ""
    if len(spark_values) > 1:
        w, h = 200, 30
        mn, mx = min(spark_values), max(spark_values)
        span = mx - mn if mx != mn else 1
        points = []
        for idx, val in enumerate(spark_values):
            x = idx * (w / (len(spark_values) - 1))
            y = h - 2 - ((val - mn) / span) * (h - 4)
            points.append(f"{x:.1f},{y:.1f}")
            
        path_d = "M " + " L ".join(points)
        color = spec.get("color", "#A855F7")
        svg_html = f"""
        <svg width="100%" height="24" viewBox="0 0 200 30" preserveAspectRatio="none" style="margin-top:auto; filter: drop-shadow(0px 1px 3px rgba(0,0,0,0.15));">
          <defs>
            <linearGradient id="grad_{spec['label'].replace(' ','')}" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="{color}" stop-opacity="0.25"/>
              <stop offset="100%" stop-color="{color}" stop-opacity="0.0"/>
            </linearGradient>
          </defs>
          <path d="{path_d} L 200,30 L 0,30 Z" fill="url(#grad_{spec['label'].replace(' ','')})" />
          <path d="{path_d}" fill="none" stroke="{color}" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round" />
        </svg>
        """
    else:
        svg_html = '<div style="height:24px;"></div>'
        
    return trend_pct, svg_html

def _render_kpi_cards(df: pd.DataFrame, schema: dict):
    specs = get_domain_kpis(schema, df)
    cols = st.columns(4)
    for i in range(4):
        if i < len(specs):
            spec = specs[i]
            raw, fmt = compute_kpi(df, spec)
            color = spec.get("color","#C084FC")
            trend_pct, spark_svg = _generate_sparkline_and_trend(df, spec, schema)
            
            if trend_pct >= 0:
                trend_color = "#10B981"
                trend_arrow = "↑"
            else:
                trend_color = "#EF4444"
                trend_arrow = "↓"
                
            trend_html = f'<div class="kpi-mini-trend" style="color:{trend_color};">{trend_arrow} {abs(trend_pct):.1f}% <span style="color:#64748B; font-weight:normal; margin-left: 2px;">vs previous</span></div>'
            
            with cols[i]:
                st.markdown(
                    f'<div class="kpi-mini-card">'
                    f'<div class="kpi-mini-title">{spec["icon"]} {spec["label"]}</div>'
                    f'<div class="kpi-mini-value" style="color:{color};">{fmt}</div>'
                    f'{trend_html}'
                    f'{spark_svg}'
                    f'</div>',
                    unsafe_allow_html=True
                )
        else:
            with cols[i]:
                st.markdown(
                    f'<div class="kpi-mini-card">'
                    f'<div class="kpi-mini-title">➖ N/A</div>'
                    f'<div class="kpi-mini-value" style="color:#64748B;">N/A</div>'
                    f'<div class="kpi-mini-trend" style="color:#64748B;">No data</div>'
                    f'<div style="height:24px;"></div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

def _build_sidebar_filters(df: pd.DataFrame, schema: dict):
    date_col    = schema.get("date_col")
    region_col  = schema.get("region_col")
    category_col= schema.get("category_col")

    with st.sidebar:
        st.markdown("<hr style='margin:8px 0;'>", unsafe_allow_html=True)
        st.markdown("<h3 style='margin-bottom:10px;'>⚙️ Active Filters</h3>", unsafe_allow_html=True)

        date_range = None
        if date_col and date_col in df.columns:
            if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
                try:
                    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
                except Exception:
                    pass
            if pd.api.types.is_datetime64_any_dtype(df[date_col]) and len(df[date_col].dropna()) > 0:
                mn, mx = df[date_col].min().date(), df[date_col].max().date()
                if mn == mx:
                    date_range = (mn, mx)
                else:
                    date_range = st.date_input("📅 Date Range", value=(mn, mx), min_value=mn, max_value=mx)
            else:
                st.info("No valid datetime in date column.")
        else:
            st.info("No date column detected.")

        grain = st.radio("⏰ View By", ["Day","Date","Week","Month","Year"], horizontal=True, index=3)

        df, time_vals = _apply_time_dim(df, date_col, grain)
        sel_time = st.multiselect(f"📅 Filter by {grain}", time_vals, default=time_vals)

        sel_region = None
        if region_col and region_col in df.columns:
            opts = sorted(df[region_col].dropna().unique().tolist())
            sel_region = st.multiselect("🌍 Region", opts, default=opts)

        sel_cat = None
        if category_col and category_col in df.columns:
            opts = sorted(df[category_col].dropna().unique().tolist())
            sel_cat = st.multiselect("🏷️ Category", opts, default=opts)

        if st.button("🔄 Reset Filters", use_container_width=True):
            st.rerun()

    # Apply filters
    filtered = df.copy()
    if date_col and date_range and date_col in filtered.columns and pd.api.types.is_datetime64_any_dtype(filtered[date_col]):
        if isinstance(date_range, (tuple, list)):
            if len(date_range) == 2:
                s, e = date_range
                filtered = filtered[(filtered[date_col].dt.date >= s) & (filtered[date_col].dt.date <= e)]
            elif len(date_range) == 1:
                s = date_range[0]
                filtered = filtered[filtered[date_col].dt.date >= s]
        else:
            s = date_range
            filtered = filtered[filtered[date_col].dt.date == s]

    if sel_time and "_td" in filtered.columns:
        filtered = filtered[filtered["_td"].isin(sel_time)]
    if sel_region and region_col:
        filtered = filtered[filtered[region_col].isin(sel_region)]
    if sel_cat and category_col:
        filtered = filtered[filtered[category_col].isin(sel_cat)]

    return filtered, grain

# ── Chart Plotting Helpers ─────────────────────────────────────
def _line_chart(df, date_col, metric_col, grain):
    try:
        g = df.groupby("_td")[metric_col].sum().reset_index().rename(columns={"_td":"Time"})
        if grain == "Day":
            g["Time"] = pd.Categorical(g["Time"], categories=day_order, ordered=True)
        elif grain == "Month":
            g["Time"] = pd.Categorical(g["Time"], categories=month_order, ordered=True)
        g = g.sort_values("Time")
        fig = px.line(g, x="Time", y=metric_col, markers=True, color_discrete_sequence=["#A855F7"])
        fig.update_traces(
            line=dict(width=2, shape="spline"),
            fill="tozeroy",
            fillcolor="rgba(168, 85, 247, 0.08)"
        )
        _g_c = "rgba(0,0,0,0.08)" if st.session_state.get("theme") == "light" else "rgba(255,255,255,0.05)"
        fig.update_layout(**_chart_layout(150), 
                          xaxis=dict(showgrid=False, linecolor=_g_c),
                          yaxis=dict(showgrid=True, gridcolor=_g_c, linecolor=_g_c),
                          hovermode="x unified")
        return fig
    except Exception:
        return None

def _map_chart(df, state_col, metric_col):
    try:
        g = df.groupby(state_col)[metric_col].sum().reset_index()
        g[state_col] = g[state_col].astype(str).str.upper().str.strip()
        
        # Test for USA states
        g["_code"] = g[state_col].apply(lambda x: state_to_code.get(x, x))
        us_matches = g[g["_code"].isin(us_state_names.keys())]
        
        # Test for Indian states
        india_states = {
            'ANDAMAN AND NICOBAR', 'ANDHRA PRADESH', 'ARUNACHAL PRADESH', 'ASSAM', 'BIHAR',
            'CHANDIGARH', 'CHHATTISGARH', 'DADRA AND NAGAR HAVELI', 'DAMAN AND DIU', 'DELHI',
            'GOA', 'GUJARAT', 'HARYANA', 'HIMACHAL PRADESH', 'JAMMU AND KASHMIR', 'JHARKHAND',
            'KARNATAKA', 'KERALA', 'LAKSHADWEEP', 'MADHYA PRADESH', 'MAHARASHTRA', 'MANIPUR',
            'MEGHALAYA', 'MIZORAM', 'NAGALAND', 'ORISSA', 'ODISHA', 'PUDUCHERRY', 'PUNJAB',
            'RAJASTHAN', 'SIKKIM', 'TAMIL NADU', 'TRIPURA', 'UTTAR PRADESH', 'UP', 'UTTARANCHAL',
            'WEST BENGAL'
        }
        india_matches = g[g[state_col].isin(india_states)]
        
        if len(us_matches) > 0:
            us_matches = us_matches.copy()
            us_matches["_name"] = us_matches["_code"].map(us_state_names)
            total = us_matches[metric_col].sum()
            us_matches["_pct"] = (us_matches[metric_col] / total * 100).apply(lambda x: f"{x:.1f}%")
            us_matches["_fmt"] = us_matches[metric_col].apply(format_currency if any(
                x in metric_col.lower() for x in ["revenue","sales","amount","profit","cost","salary"]
            ) else format_number)
            
            fig = px.choropleth(us_matches, locations="_code", locationmode="USA-states",
                                color=metric_col, scope="usa", 
                                color_continuous_scale=["#3B82F6", "#8B5CF6", "#EC4899", "#10B981", "#F59E0B"])
            fig.update_traces(
                hovertemplate="<b>%{customdata[0]}</b><br>" + metric_col +
                               ": %{customdata[1]}<br>Share: %{customdata[2]}<extra></extra>",
                customdata=np.stack((us_matches["_name"], us_matches["_fmt"], us_matches["_pct"]), axis=-1),
                marker_line_color="rgba(255,255,255,0.15)", marker_line_width=0.8
            )
            fig.add_trace(go.Scattergeo(
                locations=us_matches["_code"], locationmode="USA-states",
                text=us_matches["_code"], mode="text",
                textfont=dict(color="white", size=8), hoverinfo="skip"
            ))
            fig.update_layout(**_chart_layout(150), dragmode=False,
                              coloraxis_showscale=False,
                              geo=dict(bgcolor="rgba(0,0,0,0)", lakecolor="rgba(0,0,0,0)",
                                       landcolor="rgba(255,255,255,0.02)",
                                       subunitcolor="rgba(255,255,255,0.08)",
                                       showlakes=True, projection_type="albers usa"))
            return fig

        elif len(india_matches) > 0:
            geojson_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend", "storage", "india_states.geojson"))
            if not os.path.exists(geojson_path):
                import urllib.request
                try:
                    os.makedirs(os.path.dirname(geojson_path), exist_ok=True)
                    url = "https://raw.githubusercontent.com/geohacker/india/master/state/india_state.geojson"
                    urllib.request.urlretrieve(url, geojson_path)
                except Exception:
                    pass
            
            import json
            if os.path.exists(geojson_path):
                try:
                    with open(geojson_path, "r", encoding="utf-8") as f:
                        india_geojson = json.load(f)
                except Exception:
                    india_geojson = None
            else:
                india_geojson = None
                
            if india_geojson:
                india_state_mapping = {
                    "ODISHA": "Orissa",
                    "UP": "Uttar Pradesh",
                }
                india_matches = india_matches.copy()
                india_matches["_map_name"] = india_matches[state_col].apply(
                    lambda x: india_state_mapping.get(x, x.title())
                )
                total = india_matches[metric_col].sum()
                total_abs = max(1e-9, abs(total))
                india_matches["_pct"] = (india_matches[metric_col] / total_abs * 100).apply(lambda x: f"{x:.1f}%")
                india_matches["_fmt"] = india_matches[metric_col].apply(format_currency if any(
                    x in metric_col.lower() for x in ["revenue","sales","amount","profit","cost","salary"]
                ) else format_number)
                
                fig = px.choropleth(
                    india_matches,
                    geojson=india_geojson,
                    locations="_map_name",
                    featureidkey="properties.NAME_1",
                    color=metric_col,
                    color_continuous_scale=["#3B82F6", "#8B5CF6", "#EC4899", "#10B981", "#F59E0B"]
                )
                fig.update_traces(
                    hovertemplate="<b>%{locations}</b><br>" + metric_col +
                                   ": %{customdata[0]}<br>Share: %{customdata[1]}<extra></extra>",
                    customdata=np.stack((india_matches["_fmt"], india_matches["_pct"]), axis=-1),
                    marker_line_color="rgba(255,255,255,0.15)", marker_line_width=0.8
                )
                fig.update_geos(fitbounds="locations", visible=False)
                fig.update_layout(**_chart_layout(150), dragmode=False,
                                  coloraxis_showscale=False,
        # Generic Regions Bubble Map Fallback (For generic regions like "West", "East", "Central")
        if len(g) > 0:
            region_coords = {
                "WEST": (40.0, -119.0),
                "EAST": (40.0, -75.0),
                "SOUTH": (33.0, -86.0),
                "CENTRAL": (39.0, -98.0),
                "NORTH": (45.0, -96.0),
                "MIDWEST": (42.0, -92.0),
                "NORTHEAST": (43.0, -74.0),
                "SOUTHEAST": (33.0, -83.0),
                "SOUTHWEST": (34.0, -106.0),
                "NORTHWEST": (45.0, -114.0),
                "EMEA": (45.0, 15.0),
                "APAC": (15.0, 105.0),
                "LATAM": (-10.0, -65.0),
                "AMERICAS": (40.0, -95.0),
                "EUROPE": (50.0, 10.0),
                "ASIA": (40.0, 95.0),
                "AFRICA": (0.0, 20.0),
                "NORTH AMERICA": (45.0, -100.0),
                "SOUTH AMERICA": (-15.0, -60.0),
                "AUSTRALIA": (-25.0, 135.0),
                "OCEANIA": (-20.0, 140.0),
            }
            
            g_generic = g.copy()
            g_generic["_lat"] = g_generic[state_col].apply(lambda x: region_coords.get(x, (None, None))[0])
            g_generic["_lon"] = g_generic[state_col].apply(lambda x: region_coords.get(x, (None, None))[1])
            
            generic_matches = g_generic.dropna(subset=["_lat", "_lon"]).copy()
            
            if len(generic_matches) > 0:
                is_us_scoped = any(x in generic_matches[state_col].values for x in ["WEST", "EAST", "SOUTH", "CENTRAL", "MIDWEST", "NORTHEAST"])
                scope = "usa" if is_us_scoped else "world"
                
                total = generic_matches[metric_col].sum()
                total_abs = max(1e-9, abs(total))
                generic_matches["_pct"] = (generic_matches[metric_col] / total_abs * 100).apply(lambda x: f"{x:.1f}%")
                generic_matches["_fmt"] = generic_matches[metric_col].apply(format_currency if any(
                    x in metric_col.lower() for x in ["revenue","sales","amount","profit","cost","salary"]
                ) else format_number)
                
                fig = px.scatter_geo(
                    generic_matches,
                    lat="_lat",
                    lon="_lon",
                    size=metric_col,
                    color=metric_col,
                    hover_name=state_col,
                    scope=scope,
                    color_continuous_scale=["#3B82F6", "#8B5CF6", "#EC4899", "#10B981", "#F59E0B"]
                )
                fig.update_traces(
                    hovertemplate="<b>%{hovertext}</b><br>" + metric_col +
                                   ": %{customdata[0]}<br>Share: %{customdata[1]}<extra></extra>",
                    customdata=np.stack((generic_matches["_fmt"], generic_matches["_pct"]), axis=-1),
                    marker=dict(line=dict(width=1, color="rgba(255,255,255,0.7)")),
                    sizemin=10, sizemode="area"
                )
                
                fig.add_trace(go.Scattergeo(
                    lat=generic_matches["_lat"], lon=generic_matches["_lon"],
                    text=generic_matches[state_col].str.title(), mode="text",
                    textfont=dict(color="white", size=10, family="Inter"),
                    textposition="top center", hoverinfo="skip",
                    showlegend=False
                ))
                
                fig.update_layout(**_chart_layout(150), dragmode=False,
                                  coloraxis_showscale=False,
                                  geo=dict(bgcolor="rgba(0,0,0,0)",
                                           lakecolor="rgba(0,0,0,0)",
                                           landcolor="rgba(255,255,255,0.02)",
                                           subunitcolor="rgba(255,255,255,0.08)",
                                           showlakes=True))
                return fig
                
            # If not generic regions, assume World Countries and render standard choropleth
            total = g[metric_col].sum()
            total_abs = max(1e-9, abs(total))
            g["_pct"] = (g[metric_col] / total_abs * 100).apply(lambda x: f"{x:.1f}%")
            g["_fmt"] = g[metric_col].apply(format_currency if any(
                x in metric_col.lower() for x in ["revenue","sales","amount","profit","cost","salary"]
            ) else format_number)
            
            fig = px.choropleth(
                g,
                locations=state_col,
                locationmode="country names",
                color=metric_col,
                color_continuous_scale=["#3B82F6", "#8B5CF6", "#EC4899", "#10B981", "#F59E0B"]
            )
            fig.update_traces(
                hovertemplate="<b>%{location}</b><br>" + metric_col +
                               ": %{customdata[0]}<br>Share: %{customdata[1]}<extra></extra>",
                customdata=np.stack((g["_fmt"], g["_pct"]), axis=-1),
                marker_line_color="rgba(255,255,255,0.15)", marker_line_width=0.8
            )
            fig.update_layout(**_chart_layout(150), dragmode=False,
                              coloraxis_showscale=False,
                              geo=dict(bgcolor="rgba(0,0,0,0)",
                                       lakecolor="rgba(0,0,0,0)",
                                       landcolor="rgba(255,255,255,0.02)",
                                       subunitcolor="rgba(255,255,255,0.08)",
                                       showlakes=True))
            return fig
            
        return None
    except Exception:
        return None

def _donut_chart(df, label_col, value_col):
    try:
        df = df.copy()
        df[label_col] = df[label_col].astype(str).str.title().str.strip()
        g = df.groupby(label_col)[value_col].sum().reset_index()
        fig = px.pie(g, names=label_col, values=value_col, hole=0.6,
                     color_discrete_sequence=["#3B82F6","#8B5CF6","#10B981","#F59E0B","#EC4899"])
        fig.update_traces(
            textinfo="percent",
            textposition="inside",
            insidetextorientation="radial",
            marker=dict(line=dict(color="rgba(13,15,30,0.45)", width=2))
        )
        fig.update_layout(**_chart_layout(180), showlegend=True,
                          legend=dict(orientation="h", yanchor="top", y=-0.15,
                                      xanchor="center", x=0.5, font=dict(size=7, color="#94A3B8")))
        return fig
    except Exception:
        return None

def _bar_chart(df, x_col, y_col):
    try:
        g = df.groupby(x_col)[y_col].sum().reset_index()
        fig = px.bar(g, x=x_col, y=y_col, color=x_col, color_discrete_sequence=COLORS)
        _g_c = "rgba(0,0,0,0.08)" if st.session_state.get("theme") == "light" else "rgba(255,255,255,0.05)"
        fig.update_layout(**_chart_layout(180), showlegend=False,
                          xaxis_title="", yaxis_title="",
                          xaxis=dict(showgrid=False),
                          yaxis=dict(showgrid=True, gridcolor=_g_c))
        return fig
    except Exception:
        return None

def _hbar_chart(df, x_col, y_col, top_n=5):
    try:
        g = df.groupby(y_col)[x_col].sum().reset_index()
        g = g.sort_values(x_col, ascending=True).tail(top_n)
        fig = px.bar(g, x=x_col, y=y_col, orientation="h",
                     color=x_col, color_continuous_scale="Purples")
        _g_c = "rgba(0,0,0,0.08)" if st.session_state.get("theme") == "light" else "rgba(255,255,255,0.05)"
        fig.update_layout(**_chart_layout(180), coloraxis_showscale=False,
                          xaxis_title="", yaxis_title="",
                          xaxis=dict(showgrid=True, gridcolor=_g_c),
                          yaxis=dict(showgrid=False))
        return fig
    except Exception:
        return None

# ── Data Pipeline (Live vs Preset) ─────────────────────────────
active_id = st.session_state.get("active_dataset_id")
has_active_dataset = False
active_dataset_info = None

try:
    datasets = api_client.list_datasets(force_refresh=True)
except Exception:
    datasets = []

cleaned_datasets = [d for d in datasets if d.get("status","").upper() not in ("UPLOADED", "FAILED")]

if active_id and cleaned_datasets:
    ds = next((d for d in cleaned_datasets if d["id"] == active_id), None)
    if ds:
        has_active_dataset = True
        active_dataset_info = ds
elif cleaned_datasets:
    active_dataset_info = cleaned_datasets[0]
    active_id = active_dataset_info["id"]
    st.session_state["active_dataset_id"] = active_id
    has_active_dataset = True

if has_active_dataset:
    df_raw, mapping = _load_active_df(active_id)
    if df_raw is None:
        st.error("⚠️ Could not load the active dataset file from storage. Please re-upload or re-clean the dataset.")
        if len(cleaned_datasets) > 1:
            with st.sidebar:
                st.markdown("<hr style='margin:8px 0;'>", unsafe_allow_html=True)
                ds_opts = {d["id"]: f"📊 {d['filename']}" for d in cleaned_datasets}
                sel_id = st.selectbox(
                    "📂 Switch Active Dataset",
                    options=list(ds_opts.keys()),  # Cleaned datasets only
                    format_func=lambda x: ds_opts[x],
                    index=list(ds_opts.keys()).index(active_id) if active_id in ds_opts else 0
                )
                if sel_id != active_id:
                    st.session_state["active_dataset_id"] = sel_id
                    st.rerun()
        st.stop()
    schema = detect_schema(df_raw, mapping)
    filename = active_dataset_info.get("filename", "")
    is_demo = False
else:
    st.error("⚠️ No active dataset selected. Please upload and prepare a dataset to view the KPI Dashboard.")
    if len(cleaned_datasets) > 1:
        with st.sidebar:
            st.markdown("<hr style='margin:8px 0;'>", unsafe_allow_html=True)
            ds_opts = {d["id"]: f"📊 {d['filename']}" for d in cleaned_datasets}
            sel_id = st.selectbox(
                "📂 Switch Active Dataset",
                options=list(ds_opts.keys()),  # Cleaned datasets only
                format_func=lambda x: ds_opts[x]
            )
            if sel_id != active_id:
                st.session_state["active_dataset_id"] = sel_id
                st.rerun()
    st.stop()

# Process date column
date_col = schema.get("date_col")
if date_col and date_col in df_raw.columns:
    try:
        df_raw[date_col] = pd.to_datetime(df_raw[date_col], infer_datetime_format=True, errors="coerce")
    except Exception:
        pass

# Clean and coerce numeric columns to handle currency symbols, commas, and percentage strings
num_fields = ["revenue_col", "profit_col", "cost_col", "quantity_col", "salary_col", "balance_col", "primary_metric"]
for field in num_fields:
    col_name = schema.get(field)
    if col_name and col_name in df_raw.columns:
        try:
            df_raw[col_name] = _clean_numeric_col(df_raw[col_name])
        except Exception:
            pass

# Write diagnostic info to local file for debug analysis
try:
    debug_path = "c:/Users/akkum/OneDrive/Desktop/Project/backend/storage/debug_dashboard.txt"
    with open(debug_path, "w", encoding="utf-8") as f:
        f.write(f"Filename: {filename}\n")
        f.write(f"Is Demo: {is_demo}\n")
        f.write(f"Mapping: {dict(mapping) if mapping else {}}\n")
        f.write(f"Schema: {dict(schema) if schema else {}}\n")
        f.write(f"Dataframe Shape: {str(df_raw.shape)}\n")
        f.write(f"Dataframe Columns: {list(df_raw.columns)}\n")
        f.write("Columns Dtypes:\n")
        for c, t in df_raw.dtypes.items():
            f.write(f"  {c}: {t}\n")
        
        rev_col = schema.get("revenue_col")
        if rev_col and rev_col in df_raw.columns:
            f.write(f"\nRevenue Column '{rev_col}' first 15 values:\n")
            f.write(f"{df_raw[rev_col].head(15).to_dict()}\n")
            f.write(f"Revenue Column Sum: {df_raw[rev_col].sum()}\n")
            f.write(f"Revenue Column Is Null Count: {df_raw[rev_col].isna().sum()}\n")
except Exception as e:
    pass

# Render dynamic dataset selector if live mode has multiple datasets
if has_active_dataset and len(cleaned_datasets) > 1:
    with st.sidebar:
        st.markdown("<hr style='margin:8px 0;'>", unsafe_allow_html=True)
        ds_opts = {d["id"]: f"📊 {d['filename']}" for d in cleaned_datasets}
        sel_id = st.selectbox(
            "📂 Switch Active Dataset",
            options=list(ds_opts.keys()),  # Cleaned datasets only
            format_func=lambda x: ds_opts[x],
            index=list(ds_opts.keys()).index(active_id) if active_id in ds_opts else 0
        )
        if sel_id != active_id:
            st.session_state["active_dataset_id"] = sel_id
            st.rerun()

# Apply filters
df, grain = _build_sidebar_filters(df_raw, schema)
if len(df) == 0:
    st.warning("⚠️ No data matches the active filters.")
    st.stop()

# Re-detect schema on filtered data
schema = detect_schema(df, mapping)

# ── Dynamic Header Details ───────────────────────────────────────
if date_col and date_col in df.columns:
    min_d, max_d = df[date_col].min(), df[date_col].max()
    if hasattr(min_d, 'strftime'):
        date_range_str = f"{min_d.strftime('%d %b %Y')} - {max_d.strftime('%d %b %Y')}"
    else:
        date_range_str = f"{min_d} - {max_d}"
else:
    date_range_str = "All Time"

detected_domain_label = schema.get("domain", "GENERIC").upper().replace("_", " ")
if detected_domain_label == "SALES":
    detected_domain_label = "E-COMMERCE / SALES"

now_str = datetime.datetime.now().strftime("%d %b %Y %I:%M %p")

st.markdown(f"""
<div class="dashboard-header">
    <div class="dashboard-title-wrapper">
        <div class="dashboard-title">Executive Dashboard</div>
        <div class="dashboard-subtitle">AI Powered Business Intelligence</div>
    </div>
    <div class="meta-chips-container">
        <div class="meta-chip">
            📁 <span style="color:#64748B;">Active Dataset:</span> <b>{filename}</b>
        </div>
        <div class="meta-chip">
            📅 <span style="color:#64748B;">Date Range:</span> <b>{date_range_str}</b>
        </div>
        <div class="meta-chip meta-chip-domain">
            Domain Detected: <b>{detected_domain_label}</b>
        </div>
        <div class="last-updated">
            Last Updated: {now_str} 🔄
        </div>
    </div>
</div>
""", unsafe_allow_html=True)
st.markdown("<hr style='margin-top:2px; margin-bottom:12px; border-color: rgba(255,255,255,0.06);'>", unsafe_allow_html=True)

# ── KPI Cards ──────────────────────────────────────────────────
_render_kpi_cards(df, schema)
st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)


# ── Row 1: Monthly Trend + Map ────────────────────────────────
primary_metric = schema.get("primary_metric")
primary_label  = schema.get("primary_label", "Metric")
cat_col     = schema.get("category_col")
region_col  = schema.get("region_col")
product_col = schema.get("product_col")
state_col   = schema.get("state_col") or schema.get("region_col")
city_col    = schema.get("city_col")

fig_trend = _line_chart(df, date_col, primary_metric, grain) if date_col and primary_metric else None
fig_map   = _map_chart(df, state_col, primary_metric) if state_col and primary_metric else None
fig_city  = _hbar_chart(df, primary_metric, city_col) if city_col and primary_metric and not fig_map else None

r1c1, r1c2 = st.columns([1.2, 0.8])
with r1c1:
    with st.container(border=True):
        grain_suffixes = {"Day": "DAILY", "Date": "DAILY", "Week": "WEEKLY", "Month": "MONTHLY", "Year": "YEARLY"}
        suffix = grain_suffixes.get(grain, grain.upper())
        st.markdown(f"<p class='chart-box-title'>📈 {primary_label.upper()} TREND ({suffix})</p>", unsafe_allow_html=True)
        if fig_trend:
            st.plotly_chart(fig_trend, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("ℹ️ Trend requires a detected date column and numeric metric.")
with r1c2:
    with st.container(border=True):
        if fig_map:
            st.markdown(f"<p class='chart-box-title'>🗺️ GEOGRAPHIC DISTRIBUTION ({primary_label.upper()})</p>", unsafe_allow_html=True)
            st.plotly_chart(fig_map, use_container_width=True, config={"displayModeBar": False})
        elif fig_city:
            st.markdown(f"<p class='chart-box-title'>🏙️ TOP CITIES BY {primary_label.upper()}</p>", unsafe_allow_html=True)
            st.plotly_chart(fig_city, use_container_width=True, config={"displayModeBar": False})
        else:
            st.markdown("<p class='chart-box-title'>🗺️ GEOGRAPHIC DISTRIBUTION</p>", unsafe_allow_html=True)
            st.info("ℹ️ Geographic chart requires a State, City, or Region mapping.")

# ── Row 2: Donut + Category Bar + Product H-Bar + AI Insights ──
r2c1, r2c2, r2c3, r2c4 = st.columns(4)
with r2c1:
    with st.container(border=True, height=245):
        st.markdown(f"<p class='chart-box-title'>🍩 REGIONAL SHARE</p>", unsafe_allow_html=True)
        fig = _donut_chart(df, region_col, primary_metric) if region_col and primary_metric else None
        if fig:
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Donut requires a Region column.")
with r2c2:
    with st.container(border=True, height=245):
        lbl = cat_col.replace("_"," ").title() if cat_col else "Category"
        st.markdown(f"<p class='chart-box-title'>📊 {primary_label.upper()} BY {lbl.upper()}</p>", unsafe_allow_html=True)
        fig = _bar_chart(df, cat_col, primary_metric) if cat_col and primary_metric else None
        if fig:
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Bar chart requires a Category column.")
with r2c3:
    with st.container(border=True, height=245):
        p_lbl = product_col.replace("_"," ").title() if product_col else "Item"
        st.markdown(f"<p class='chart-box-title'>📚 TOP {p_lbl.upper()}S BY {primary_label.upper()}</p>", unsafe_allow_html=True)
        fig = _hbar_chart(df, primary_metric, product_col) if product_col and primary_metric else None
        if fig:
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Horizontal chart requires a Product column.")
with r2c4:
    with st.container(border=True, height=245):
        st.markdown("<p class='chart-box-title'>✨ AI BUSINESS INSIGHTS</p>", unsafe_allow_html=True)
        insights = generate_ai_insights(df, schema)
        st.markdown('<div class="ai-insights-container">', unsafe_allow_html=True)
        for ins in insights:
            parts = ins.split(" ", 1)
            if len(parts) == 2 and len(parts[0]) <= 2:
                icon, text = parts[0], parts[1]
            else:
                icon, text = "✨", ins
            formatted_text = text.replace("**", "<b>").replace("**", "</b>")
            st.markdown(
                f'<div class="ai-insight-item">'
                f'<span class="ai-insight-icon">{icon}</span>'
                f'<span>{formatted_text}</span>'
                f'</div>',
                unsafe_allow_html=True
            )
        st.markdown('</div>', unsafe_allow_html=True)

# ── Dataset preview ───────────────────────────────────────────
st.markdown("<hr style='margin:10px 0; border-color: rgba(255,255,255,0.06);'>", unsafe_allow_html=True)
with st.expander("🔍 View Dataset Preview (first 100 rows)", expanded=False):
    st.dataframe(df.head(100), use_container_width=True)

# Render sidebar navigation links at the bottom of the sidebar


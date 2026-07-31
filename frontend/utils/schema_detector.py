"""
schema_detector.py  ─  AI-Driven Domain & Schema Detection
──────────────────────────────────────────────────────────
Supports 12+ business domains with semantic column detection.

Usage:
    from frontend.utils.schema_detector import detect_schema, get_dashboard_title, get_domain_kpis

    schema = detect_schema(df, mapping)
    title  = get_dashboard_title(schema)
    kpis   = get_domain_kpis(schema, df)
"""

from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Optional

# ─────────────────────────────────────────────────────────────
#  Keyword maps: canonical → substrings (case-insensitive match)
# ─────────────────────────────────────────────────────────────
COLUMN_KEYWORDS: dict[str, list[str]] = {
    # Time
    "date":       ["date","order_date","created_at","timestamp","time","invoice_date",
                   "purchase_date","transaction_date","shipdate","ship_date","admission_date",
                   "discharge_date","enrollment_date","hire_date","start_date"],
    # Revenue / Sales
    "revenue":    ["revenue","sales","amount","income","turnover","total_sales","sale_amount",
                   "gross_revenue","net_revenue","billing_amount","total_amount","sales_amount"],
    "profit":     ["profit","net_profit","gross_profit","earnings","net_income",
                   "operating_profit","ebit","ebitda","margin_amount"],
    "cost":       ["cost","expense","cogs","expenditure","total_cost","unit_cost","operating_cost",
                   "purchase_cost","manufacturing_cost"],
    "quantity":   ["quantity","qty","units","volume","units_sold","order_quantity","num_units",
                   "produced","manufactured"],
    "discount":   ["discount","discount_pct","promo","coupon","rebate"],
    "target_var": ["target","label","churn","outcome","default","fraud","approved",
                   "converted","class","y","result"],
    # Customers / Entities
    "customer":   ["customer_id","customer","client_id","client","account_id","user_id","member_id",
                   "subscriber_id","consumer_id"],
    "product":    ["product_id","product","item","sku","product_name","item_name",
                   "service","part_no","goods"],
    "category":   ["category","sub_category","segment","type","genre","product_category",
                   "department","class","subcategory"],
    "order":      ["order_id","order_number","transaction_id","invoice_id","purchase_id","order_no"],
    # Geography
    "region":     ["region","zone","territory","area","market","country","geo"],
    "state":      ["state","province","state_code","state_name"],
    "city":       ["city","town","location","city_name","metro"],
    # HR / Employee
    "employee":   ["employee_id","employee","emp_id","staff","worker","personnel","headcount"],
    "salary":     ["salary","wage","compensation","pay","annual_salary","monthly_salary"],
    "department": ["department","dept","division","unit","team","business_unit"],
    "attrition":  ["attrition","resign","left","exit","termination","churn_hr"],
    # Healthcare
    "patient":    ["patient_id","patient","patient_name","case_id","medical_id"],
    "diagnosis":  ["diagnosis","disease","condition","ailment","icd_code","illness"],
    "treatment":  ["treatment","procedure","therapy","medication","prescription"],
    "los":        ["length_of_stay","los","days_admitted","stay_duration","admission_days"],
    "bed":        ["bed","ward","room","bed_no","ward_id"],
    # Banking / Finance
    "account":    ["account_id","account_no","account_number","acct","acc_id"],
    "balance":    ["balance","account_balance","closing_balance","opening_balance","total_balance"],
    "loan":       ["loan","loan_id","loan_amount","credit","mortgage","emi"],
    "transaction":["transaction","txn","transfer","payment","deposit","withdrawal"],
    # Education
    "student":    ["student_id","student","student_name","learner","pupil"],
    "grade":      ["grade","score","marks","gpa","cgpa","result","percentage"],
    "course":     ["course","subject","module","program","class_name"],
    # Manufacturing
    "production": ["production","output","manufactured","produced","units_made"],
    "defect":     ["defect","defective","rejects","scrap","fault"],
    "shift":      ["shift","shift_id","work_shift"],
    # Marketing
    "campaign":   ["campaign","campaign_id","campaign_name","ad_name","initiative"],
    "conversion": ["conversion","converted","leads","signups","purchases","acquisitions"],
    "clicks":     ["clicks","click","impressions","views","sessions","traffic"],
    "ctr":        ["ctr","click_through","open_rate","bounce_rate"],
    "roi":        ["roi","roas","return_on_investment"],
    # Telecom / Insurance / Logistics
    "subscriber": ["subscriber","subscription","plan","tariff","mobile_no"],
    "policy":     ["policy_id","policy","policy_no","coverage_type"],
    "claim":      ["claim","claim_id","claim_amount","payout"],
    "premium":    ["premium","insurance_cost","annual_premium"],
    "shipment":   ["shipment","shipment_id","delivery","parcel","tracking"],
    "carrier":    ["carrier","courier","logistics_company","delivery_partner"],
    # General numeric signals
    "rating":     ["rating","score","satisfaction","review_score","nps","stars"],
    "age":        ["age","dob","birth_year","age_group"],
    "gender":     ["gender","sex","biological_sex"],
}

# ─────────────────────────────────────────────────────────────
#  Domain detection rules — evaluated in ORDER; first match wins
#  Format: (any_of_these_keys_present, all_of_these_keys_present, domain, title)
# ─────────────────────────────────────────────────────────────
DOMAIN_RULES: list[tuple[list[str], list[str], str, str]] = [
    # Sales / E-Commerce / Retail
    (["revenue","order","product"],     [],               "sales",        "Revenue Dashboard"),
    (["revenue","category"],            [],               "sales",        "Revenue Dashboard"),
    (["revenue","customer"],            [],               "sales",        "Sales Performance Dashboard"),
    (["revenue"],                       [],               "sales",        "Sales Performance Dashboard"),
    (["product","quantity","category"], [],               "retail",       "Retail Performance Dashboard"),
    # Healthcare
    (["patient","diagnosis"],           [],               "healthcare",   "Healthcare Analytics Dashboard"),
    (["patient","los"],                 [],               "healthcare",   "Healthcare Analytics Dashboard"),
    (["patient","treatment"],           [],               "healthcare",   "Healthcare Analytics Dashboard"),
    (["patient","bed"],                 [],               "healthcare",   "Hospital Operations Dashboard"),
    (["patient"],                       [],               "healthcare",   "Patient Analytics Dashboard"),
    # HR / Workforce
    (["employee","salary"],             [],               "hr",           "Workforce Analytics Dashboard"),
    (["employee","attrition"],          [],               "hr",           "HR Attrition Dashboard"),
    (["salary","department"],           [],               "hr",           "Workforce Analytics Dashboard"),
    (["employee"],                      [],               "hr",           "Employee Performance Dashboard"),
    # Banking / Finance
    (["account","balance"],             [],               "banking",      "Banking Performance Dashboard"),
    (["loan","balance"],                [],               "banking",      "Loan Portfolio Dashboard"),
    (["transaction","balance"],         [],               "banking",      "Transaction Analytics Dashboard"),
    (["profit","cost"],                 [],               "finance",      "Financial Performance Dashboard"),
    (["profit"],                        ["revenue"],      "finance",      "Financial Performance Dashboard"),
    # Education
    (["student","grade"],               [],               "education",    "Academic Performance Dashboard"),
    (["student","course"],              [],               "education",    "Education Analytics Dashboard"),
    (["student"],                       [],               "education",    "Student Analytics Dashboard"),
    # Manufacturing
    (["production","defect"],           [],               "manufacturing","Manufacturing Quality Dashboard"),
    (["production","shift"],            [],               "manufacturing","Production Operations Dashboard"),
    (["production"],                    [],               "manufacturing","Production Analytics Dashboard"),
    # Marketing
    (["campaign","conversion"],         [],               "marketing",    "Marketing Performance Dashboard"),
    (["campaign","roi"],                [],               "marketing",    "Marketing ROI Dashboard"),
    (["clicks","conversion"],           [],               "marketing",    "Digital Marketing Dashboard"),
    (["campaign"],                      [],               "marketing",    "Campaign Analytics Dashboard"),
    # Telecom
    (["subscriber","churn"],            [],               "telecom",      "Telecom Churn Dashboard"),
    (["subscriber"],                    [],               "telecom",      "Subscriber Analytics Dashboard"),
    # Insurance
    (["policy","claim"],                [],               "insurance",    "Insurance Claims Dashboard"),
    (["premium","claim"],               [],               "insurance",    "Insurance Performance Dashboard"),
    # Logistics / Supply Chain
    (["shipment","carrier"],            [],               "logistics",    "Logistics Operations Dashboard"),
    (["shipment"],                      [],               "logistics",    "Supply Chain Dashboard"),
    # Generic fallback
    ([],                                [],               "generic",      "Business Intelligence Dashboard"),
]


# ─────────────────────────────────────────────────────────────
#  Internal helpers
# ─────────────────────────────────────────────────────────────
def _find_col(df: pd.DataFrame, keyword_group: str) -> Optional[str]:
    """Return first column matching keywords for a group (exact then substring)."""
    keywords = COLUMN_KEYWORDS.get(keyword_group, [])
    cols_lower = {c.lower(): c for c in df.columns}
    for kw in keywords:
        if kw in cols_lower:
            return cols_lower[kw]
        for cl, co in cols_lower.items():
            if kw in cl:
                return co
    return None


def _find_date_col(df: pd.DataFrame) -> Optional[str]:
    hit = _find_col(df, "date")
    if hit:
        return hit
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            return col
    return None


def _is_ohe(series: pd.Series) -> bool:
    """Detect one-hot-encoded binary columns."""
    if not pd.api.types.is_numeric_dtype(series):
        return False
    uniq = series.dropna().unique()
    return set(uniq).issubset({0, 1, 0.0, 1.0}) and len(uniq) <= 2


# ─────────────────────────────────────────────────────────────
#  Public API
# ─────────────────────────────────────────────────────────────
def detect_schema(df: pd.DataFrame, mapping: Optional[dict] = None) -> dict:
    """
    Analyse a DataFrame and return a comprehensive schema dict.
    mapping: backend column-mapping dict (keys like 'date', 'amount', etc.)
    """
    mapping = mapping or {}

    def resolve(canonical: str, kw_group: str) -> Optional[str]:
        if canonical == "revenue":
            sales_col = next((c for c in df.columns if c.strip().lower() in ["sales", "revenue"]), None)
            if sales_col:
                return sales_col
        if canonical == "quantity":
            qty_col = next((c for c in df.columns if c.strip().lower() == "quantity"), None)
            if qty_col:
                return qty_col
        mapped = mapping.get(canonical)
        if mapped and mapped in df.columns:
            return mapped
        for alt in ["amount", "revenue", "sales"] if canonical == "revenue" else []:
            v = mapping.get(alt)
            if v and v in df.columns:
                return v
        return _find_col(df, kw_group)

    schema = {
        "date_col":        mapping.get("date") if mapping.get("date") in df.columns else _find_date_col(df),
        "revenue_col":     resolve("revenue",    "revenue"),
        "profit_col":      resolve("profit",     "profit"),
        "cost_col":        resolve("cost",       "cost"),
        "quantity_col":    resolve("quantity",   "quantity"),
        "discount_col":    _find_col(df, "discount"),
        "target_col":      resolve("target",     "target_var"),
        "customer_col":    resolve("customer_id","customer"),
        "product_col":     resolve("product",    "product"),
        "category_col":    resolve("category",   "category"),
        "order_col":       _find_col(df, "order"),
        "region_col":      resolve("region",     "region"),
        "state_col":       resolve("state",      "state"),
        "city_col":        resolve("city",       "city"),
        "department_col":  _find_col(df, "department"),
        "employee_col":    _find_col(df, "employee"),
        "salary_col":      _find_col(df, "salary"),
        "attrition_col":   _find_col(df, "attrition"),
        "patient_col":     _find_col(df, "patient"),
        "diagnosis_col":   _find_col(df, "diagnosis"),
        "los_col":         _find_col(df, "los"),
        "bed_col":         _find_col(df, "bed"),
        "account_col":     _find_col(df, "account"),
        "balance_col":     _find_col(df, "balance"),
        "loan_col":        _find_col(df, "loan"),
        "transaction_col": _find_col(df, "transaction"),
        "student_col":     _find_col(df, "student"),
        "grade_col":       _find_col(df, "grade"),
        "course_col":      _find_col(df, "course"),
        "production_col":  _find_col(df, "production"),
        "defect_col":      _find_col(df, "defect"),
        "campaign_col":    _find_col(df, "campaign"),
        "conversion_col":  _find_col(df, "conversion"),
        "roi_col":         _find_col(df, "roi"),
        "clicks_col":      _find_col(df, "clicks"),
        "subscriber_col":  _find_col(df, "subscriber"),
        "policy_col":      _find_col(df, "policy"),
        "claim_col":       _find_col(df, "claim"),
        "premium_col":     _find_col(df, "premium"),
        "shipment_col":    _find_col(df, "shipment"),
        "rating_col":      _find_col(df, "rating"),
        "age_col":         _find_col(df, "age"),
        "gender_col":      _find_col(df, "gender"),
    }

    # Detect domain keys
    domain_keys = {k.replace("_col","") for k, v in schema.items() if v and k.endswith("_col")}

    # Numeric and categorical cols (exclude OHE cols)
    all_num  = df.select_dtypes(include="number").columns.tolist()
    num_cols = [c for c in all_num if not _is_ohe(df[c])]
    cat_cols = df.select_dtypes(include=["object","category"]).columns.tolist()

    # Primary metric: revenue > profit > balance > salary > cost > grade > production > first valid numeric
    primary = (schema["revenue_col"] or schema["profit_col"] or schema["balance_col"] or
               schema["salary_col"] or schema["cost_col"] or schema["grade_col"] or
               schema["production_col"])
    if not primary:
        primary = next((c for c in num_cols if "id" not in c.lower()), num_cols[0] if num_cols else None)

    schema.update({
        "domain_keys":   domain_keys,
        "numeric_cols":  num_cols,
        "categorical_cols": cat_cols,
        "primary_metric": primary,
        "primary_label":  primary.replace("_"," ").title() if primary else "Metric",
    })

    # Domain detection
    for any_keys, all_keys, domain_id, title in DOMAIN_RULES:
        if any_keys and not any(k in domain_keys for k in any_keys):
            continue
        if all_keys and not all(k in domain_keys for k in all_keys):
            continue
        schema["domain"]  = domain_id
        schema["title"]   = title
        break
    else:
        schema["domain"] = "generic"
        schema["title"]  = "Business Intelligence Dashboard"

    return schema


def get_dashboard_title(schema: dict) -> str:
    return schema.get("title", "Business Intelligence Dashboard")


def get_domain_kpis(schema: dict, df: pd.DataFrame) -> list[dict]:
    """
    Return up to 4 KPI specs for the detected domain.
    Each spec: {icon, label, col, agg, format, color, trend_col (optional)}
    """
    domain = schema.get("domain", "generic")
    pm     = schema.get("primary_metric")
    specs  = []

    def _add(icon, label, col, agg="sum", fmt="currency", color="#A855F7"):
        if col and col in df.columns:
            specs.append({"icon": icon, "label": label, "col": col,
                          "agg": agg, "format": fmt, "color": color})

    def _add_len(icon, label, color="#10B981"):
        specs.append({"icon": icon, "label": label, "col": "__len__",
                      "agg": "count", "format": "number", "color": color})

    def _add_nunique(icon, label, col, color="#F59E0B"):
        if col and col in df.columns:
            specs.append({"icon": icon, "label": label, "col": col,
                          "agg": "nunique", "format": "number", "color": color})

    if domain == "sales" or domain == "retail":
        _add("💰", "Total Revenue",   schema.get("revenue_col"), "sum", "currency", "#A855F7")
        # Total Orders: prefer distinct order IDs; fall back to row count
        ord_col = schema.get("order_col")
        if ord_col and ord_col in df.columns:
            _add_nunique("🛒", "Total Orders", ord_col, "#3B82F6")
        else:
            _add_len("🛒", "Total Orders", "#3B82F6")
        # Total Profit
        specs.append({"icon": "💸", "label": "Total Profit", "col": "__total_profit__",
                      "agg": "profit", "format": "currency", "color": "#10B981",
                      "profit_col": schema.get("profit_col"),
                      "revenue_col": schema.get("revenue_col"),
                      "cost_col": schema.get("cost_col")})
        # AOV
        rev_col = schema.get("revenue_col")
        ord_col = schema.get("order_col") or schema.get("customer_col")
        if rev_col and ord_col and rev_col in df.columns and ord_col in df.columns:
            specs.append({"icon": "📊", "label": "Avg Order Value", "col": "__aov__",
                          "agg": "aov", "format": "currency", "color": "#F59E0B",
                          "rev_col": rev_col, "ord_col": ord_col})

    elif domain == "healthcare":
        _add_nunique("🏥", "Total Patients",   schema.get("patient_col"), "#A855F7")
        _add_len("📋", "Total Records", "#3B82F6")
        if schema.get("los_col") and schema["los_col"] in df.columns:
            specs.append({"icon": "🛏️", "label": "Avg Length of Stay", "col": schema["los_col"],
                          "agg": "mean", "format": "number", "color": "#10B981"})
        if schema.get("bed_col") and schema["bed_col"] in df.columns:
            _add_nunique("🏨", "Unique Wards/Beds", schema.get("bed_col"), "#F59E0B")
        elif schema.get("diagnosis_col"):
            _add_nunique("🔬", "Unique Diagnoses", schema.get("diagnosis_col"), "#F59E0B")

    elif domain == "hr":
        _add_nunique("👨‍💼", "Total Employees", schema.get("employee_col"), "#A855F7")
        _add_nunique("🏢", "Departments",     schema.get("department_col") or schema.get("category_col"), "#3B82F6")
        _add("💵", "Avg Salary", schema.get("salary_col"), "mean", "currency", "#10B981")
        atr = schema.get("attrition_col")
        if atr and atr in df.columns:
            try:
                rate = df[atr].astype(float).mean() * 100
                specs.append({"icon": "🚪", "label": "Attrition Rate", "col": "__pct__",
                              "agg": "fixed_pct", "format": "percent", "color": "#EF4444",
                              "_value": rate})
            except Exception:
                pass

    elif domain == "banking":
        _add_nunique("🏦", "Total Accounts",  schema.get("account_col"), "#A855F7")
        _add("💳", "Total Balance",    schema.get("balance_col"), "sum", "currency", "#3B82F6")
        _add_len("📑", "Total Transactions", "#10B981")
        loan_col = schema.get("loan_col")
        if loan_col and loan_col in df.columns:
            _add("💰", "Total Loans",  loan_col, "sum", "currency", "#F59E0B")
        tgt = schema.get("target_col")
        if tgt and tgt in df.columns:
            try:
                rate = df[tgt].astype(float).mean() * 100
                specs.append({"icon": "⚠️", "label": "Default Rate", "col": "__pct__",
                              "agg": "fixed_pct", "format": "percent", "color": "#EF4444",
                              "_value": rate})
            except Exception:
                pass

    elif domain == "education":
        _add_nunique("🎓", "Total Students", schema.get("student_col"), "#A855F7")
        _add_nunique("📚", "Courses/Subjects", schema.get("course_col") or schema.get("category_col"), "#3B82F6")
        _add("📊", "Avg Score/Grade", schema.get("grade_col"), "mean", "number", "#10B981")
        _add_len("📝", "Total Records", "#F59E0B")

    elif domain == "manufacturing":
        _add("🏭", "Total Production", schema.get("production_col") or pm, "sum", "number", "#A855F7")
        _add("❌", "Total Defects",    schema.get("defect_col"), "sum", "number", "#EF4444")
        if schema.get("production_col") and schema.get("defect_col"):
            prod = schema["production_col"]; dfct = schema["defect_col"]
            if prod in df.columns and dfct in df.columns:
                try:
                    total_p = df[prod].sum()
                    total_d = df[dfct].sum()
                    rate = (total_d / total_p * 100) if total_p > 0 else 0
                    specs.append({"icon": "📉", "label": "Defect Rate", "col": "__pct__",
                                  "agg": "fixed_pct", "format": "percent", "color": "#F59E0B",
                                  "_value": rate})
                except Exception:
                    pass
        _add_len("📋", "Total Records", "#10B981")

    elif domain == "marketing":
        _add_nunique("📢", "Campaigns", schema.get("campaign_col"), "#A855F7")
        _add("🎯", "Conversions", schema.get("conversion_col"), "sum", "number", "#10B981")
        _add("💰", "Total ROI",       schema.get("roi_col"), "sum", "currency", "#3B82F6")
        _add("👆", "Total Clicks",    schema.get("clicks_col"), "sum", "number", "#F59E0B")

    elif domain == "insurance":
        _add_nunique("📋", "Total Policies", schema.get("policy_col"), "#A855F7")
        _add("💸", "Total Claims",  schema.get("claim_col"), "sum", "currency", "#EF4444")
        _add("💰", "Total Premium", schema.get("premium_col"), "sum", "currency", "#10B981")
        _add_len("📑", "Total Records", "#3B82F6")

    elif domain == "logistics":
        _add_nunique("📦", "Shipments", schema.get("shipment_col"), "#A855F7")
        _add_len("📋", "Total Records", "#3B82F6")
        _add_nunique("🚛", "Carriers",  schema.get("carrier_col"), "#10B981")
        _add("📊", primary.replace("_"," ").title() if pm else "Value", pm, "sum", "currency" if pm and any(x in (pm or "").lower() for x in ["cost","amount","value"]) else "number", "#F59E0B")

    else:  # generic / telecom / finance
        if pm:
            _add("💰", pm.replace("_"," ").title(), pm, "sum",
                 "currency" if any(x in pm.lower() for x in ["revenue","amount","profit","salary","balance","cost"]) else "number",
                 "#A855F7")
        cat = schema.get("category_col") or schema.get("department_col")
        if cat:
            _add_nunique("🏷️", f"Unique {cat.replace('_',' ').title()}s", cat, "#3B82F6")
        cust = schema.get("customer_col") or schema.get("employee_col") or schema.get("patient_col") or schema.get("student_col")
        if cust:
            _add_nunique("👥", f"Unique {cust.replace('_',' ').title()}s", cust, "#10B981")
        _add_len("📋", "Total Records", "#F59E0B")

    return specs[:4]


def compute_kpi(df: pd.DataFrame, spec: dict) -> tuple:
    """Compute and format a KPI value. Returns (raw, formatted_str)."""
    from frontend.utils.formatting import format_currency, format_number
    col = spec.get("col","")
    agg = spec.get("agg","sum")
    fmt = spec.get("format","number")

    if col == "__len__" or agg == "count":
        val = len(df)
    elif agg == "fixed_pct":
        val = spec.get("_value", 0.0)
    elif agg == "aov":
        rev = df[spec["rev_col"]].sum() if spec.get("rev_col") and spec["rev_col"] in df.columns else 0
        n   = df[spec["ord_col"]].nunique() if spec.get("ord_col") and spec["ord_col"] in df.columns else len(df)
        val = rev / n if n > 0 else 0
    elif col == "__total_profit__" or agg == "profit":
        def safe_series(col_id):
            if not col_id or col_id not in df.columns:
                return pd.Series(0.0, index=df.index)
            series = df[col_id]
            if pd.api.types.is_numeric_dtype(series):
                return series.fillna(0.0)
            return pd.to_numeric(series.astype(str).str.replace(r'[^\d.-]', '', regex=True), errors="coerce").fillna(0.0)

        prof_col = next((c for c in df.columns if c.lower() == "profit"), spec.get("profit_col"))
        if prof_col and prof_col in df.columns:
            val = safe_series(prof_col).sum()
        else:
            sales_col = next((c for c in df.columns if c.lower() in ["sales", "revenue"]), spec.get("revenue_col"))
            cost_col = next((c for c in df.columns if c.lower() == "cost"), spec.get("cost_col"))
            val = safe_series(sales_col).sum() - safe_series(cost_col).sum()
    elif col not in df.columns:
        return 0, "N/A"
    elif agg == "sum":
        val = df[col].sum()
    elif agg == "mean":
        val = df[col].mean()
    elif agg == "nunique":
        val = df[col].nunique()
    else:
        val = df[col].sum()

    if fmt == "currency":
        return val, format_currency(val)
    elif fmt == "percent":
        return val, f"{val:.1f}%"
    else:
        return val, format_number(val)


def generate_ai_insights(df: pd.DataFrame, schema: dict) -> list[str]:
    """
    Generate up to 5 concise business insights from dataset statistics.
    Completely data-driven — no hardcoded domain text.
    """
    insights = []
    pm       = schema.get("primary_metric")
    cat_col  = schema.get("category_col") or schema.get("department_col") or schema.get("course_col")
    region_col = schema.get("region_col") or schema.get("state_col")
    date_col   = schema.get("date_col")

    try:
        # 1. Trend insight (requires date + primary metric)
        if date_col and pm and date_col in df.columns and pm in df.columns:
            tmp = df.copy()
            tmp[date_col] = pd.to_datetime(tmp[date_col], errors="coerce")
            tmp = tmp.dropna(subset=[date_col, pm])
            if len(tmp) >= 4:
                tmp["_period"] = tmp[date_col].dt.to_period("M")
                monthly = tmp.groupby("_period")[pm].sum().sort_index()
                if len(monthly) >= 2:
                    last, prev = monthly.iloc[-1], monthly.iloc[-2]
                    if prev != 0:
                        pct = (last - prev) / abs(prev) * 100
                        direction = "increased" if pct >= 0 else "decreased"
                        metric_lbl = pm.replace("_"," ").title()
                        insights.append(f"📈 {metric_lbl} {direction} by {abs(pct):.1f}% in the latest period.")

        # 2. Top performing category
        if cat_col and pm and cat_col in df.columns and pm in df.columns:
            grp = df.groupby(cat_col)[pm].sum().sort_values(ascending=False)
            if len(grp) > 0:
                top_cat = grp.index[0]
                top_pct = grp.iloc[0] / grp.sum() * 100 if grp.sum() > 0 else 0
                cat_lbl = cat_col.replace("_"," ").title()
                metric_lbl = pm.replace("_"," ").title()
                insights.append(f"🏆 Top {cat_lbl}: **{top_cat}** — {top_pct:.1f}% of total {metric_lbl}.")

        # 3. Top region/state
        if region_col and pm and region_col in df.columns and pm in df.columns:
            grp = df.groupby(region_col)[pm].sum().sort_values(ascending=False)
            if len(grp) > 0:
                top_r = grp.index[0]
                top_pct = grp.iloc[0] / grp.sum() * 100 if grp.sum() > 0 else 0
                r_lbl = region_col.replace("_"," ").title()
                insights.append(f"🌍 Top {r_lbl}: **{top_r}** generates {top_pct:.1f}% of total value.")

        # 4. Anomaly / outlier hint
        if pm and pm in df.columns:
            series = df[pm].dropna()
            if len(series) > 10:
                q1, q3 = series.quantile(0.25), series.quantile(0.75)
                iqr = q3 - q1
                outliers = series[(series < q1 - 1.5*iqr) | (series > q3 + 1.5*iqr)]
                if len(outliers) > 0:
                    pct_out = len(outliers) / len(series) * 100
                    insights.append(f"⚠️ {pct_out:.1f}% of records show outlier {pm.replace('_',' ').title()} values — review for anomalies.")

        # 5. Actionable recommendation based on bottom performer
        if cat_col and pm and cat_col in df.columns and pm in df.columns:
            grp = df.groupby(cat_col)[pm].sum().sort_values(ascending=True)
            if len(grp) > 1:
                bot_cat = grp.index[0]
                cat_lbl = cat_col.replace("_"," ").title()
                metric_lbl = pm.replace("_"," ").title()
                lbl_plural = "Categories" if cat_lbl.lower() == "category" else f"{cat_lbl}s"
                insights.append(f"💡 Focus on **{bot_cat}** — lowest {metric_lbl} among all {lbl_plural}. Opportunity for growth.")

    except Exception:
        pass

    if not insights:
        insights.append("📊 Upload a dataset with numeric metrics and categories to generate AI insights.")

    return insights[:5]

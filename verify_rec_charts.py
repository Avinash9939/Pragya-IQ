def recommend_charts(columns, mapping, biz_domain):
    cols_clean = [c.lower().strip() for c in columns]
    
    date_col = mapping.get("date")
    if not date_col:
        date_col = next((c for c in columns if "date" in c.lower() or "time" in c.lower() or "timestamp" in c.lower()), None)
        
    has_date = date_col is not None and str(date_col).lower() != "none detected"
    has_sales_profit_qty = any(c.lower() in ["sales", "profit", "quantity", "revenue"] for c in columns)
    
    chart_list = []
    has_sales = any(c in cols_clean for c in ["sales", "revenue", "amount"])
    has_profit = "profit" in cols_clean
    has_quantity = "quantity" in cols_clean
    has_category = any("category" in c or "product" in c or "dept" in c for c in cols_clean)
    has_region = any("region" in c or "state" in c or "city" in c for c in cols_clean)
    
    if biz_domain == "E-Commerce / Sales" or has_sales_profit_qty:
        if has_date and has_sales:
            chart_list.append("Sales Trend (Line Chart)")
        if has_category and (has_sales or has_quantity):
            chart_list.append("Category Performance (Bar Chart)")
        if has_region and has_sales:
            chart_list.append("Region Sales (Bar Chart)")
        if has_date and (has_sales or has_profit):
            chart_list.append("Monthly Revenue Trend (Line Chart)")
        if has_category and has_profit:
            chart_list.append("Profit by Category (Bar Chart)")
        if any("product" in c for c in cols_clean) and (has_sales or has_quantity):
            chart_list.append("Top Products (Bar Chart)")
        if not chart_list:
            chart_list = ["Sales Trend (Line Chart)", "Category Performance (Bar Chart)", "Region Sales (Bar Chart)"]
    elif biz_domain == "Human Resources":
        if has_date and "attrition" in cols_clean:
            chart_list.append("Attrition Rate Trend (Line Chart)")
        if has_category or "department" in cols_clean:
            chart_list.append("Department Strength (Bar Chart)")
        if any("perf_score" in c or "performance" in c or "rating" in c for c in cols_clean):
            chart_list.append("Performance Score Distribution (Bar Chart)")
        if not chart_list:
            chart_list = ["Department Strength (Bar Chart)", "Performance Score Distribution (Bar Chart)"]
    elif biz_domain == "Healthcare":
        if has_date:
            chart_list.append("Patient Admission Trend (Line Chart)")
        if "cost" in cols_clean or "charge" in cols_clean:
            chart_list.append("Treatment Cost by Patient (Bar Chart)")
        if "readmission" in cols_clean:
            chart_list.append("Readmission by Diagnosis (Bar Chart)")
        if not chart_list:
            chart_list = ["Patient Admission Trend (Line Chart)", "Treatment Cost by Patient (Bar Chart)"]
    elif biz_domain == "Banking":
        if has_date:
            chart_list.append("Transaction Volume Trend (Line Chart)")
        if "balance" in cols_clean:
            chart_list.append("Customer Balance Distribution (Bar Chart)")
        if "transaction_type" in cols_clean:
            chart_list.append("Transaction Types (Bar Chart)")
        if not chart_list:
            chart_list = ["Transaction Volume Trend (Line Chart)", "Customer Balance Distribution (Bar Chart)"]
    elif biz_domain == "Manufacturing":
        if has_date and "yield" in cols_clean:
            chart_list.append("Production Yield Trend (Line Chart)")
        if "downtime" in cols_clean:
            chart_list.append("Downtime by Machine (Bar Chart)")
        if "defect" in cols_clean or "defect_rate" in cols_clean:
            chart_list.append("Defect Rates (Bar Chart)")
        if not chart_list:
            chart_list = ["Production Yield Trend (Line Chart)", "Defect Rates (Bar Chart)"]
    else:
        if has_date:
            chart_list.append("Record Volume Trend (Line Chart)")
        chart_list.append("Attribute Completeness (Bar Chart)")
        
    return ", ".join(chart_list)

# Test 1: Date + Sales/Profit/Quantity/Category/Region -> all six correct charts from prompt examples
t1 = recommend_charts(
    ["Order Date", "Sales", "Profit", "Quantity", "Category", "Region", "Product Name"],
    {"date": "Order Date"},
    "E-Commerce / Sales"
)
print("Test 1:", t1)
assert t1 == "Sales Trend (Line Chart), Category Performance (Bar Chart), Region Sales (Bar Chart), Monthly Revenue Trend (Line Chart), Profit by Category (Bar Chart), Top Products (Bar Chart)"

# Test 2: Date + Sales only -> subset of derivable charts
t2 = recommend_charts(["Order Date", "Sales"], {"date": "Order Date"}, "E-Commerce / Sales")
print("Test 2:", t2)
assert t2 == "Sales Trend (Line Chart), Monthly Revenue Trend (Line Chart)"

print("\nVerification Passed Successfully!")

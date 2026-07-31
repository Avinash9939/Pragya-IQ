def recommend_kpis(columns, mapping, biz_domain):
    cols_lower = [c.lower().strip() for c in columns]
    
    date_col = mapping.get("date")
    if not date_col:
        date_col = next((c for c in columns if "date" in c.lower() or "time" in c.lower() or "timestamp" in c.lower()), None)
        
    has_date = date_col is not None and str(date_col).lower() != "none detected"
    
    kpi_list = []
    if (
        any(x in cols_lower for x in ["sales", "revenue"]) and
        "profit" in cols_lower and
        "quantity" in cols_lower and
        has_date
    ):
        kpi_list = ["Revenue", "Profit", "Orders", "Quantity", "Average Order Value"]
    elif biz_domain == "E-Commerce / Sales":
        if any(c in cols_lower for c in ["sales", "revenue", "amount"]):
            kpi_list.append("Revenue")
        if "profit" in cols_lower:
            kpi_list.append("Profit")
        if any(c in cols_lower for c in ["order", "order_id", "transaction", "transaction_id", "id"]):
            kpi_list.append("Orders")
        if "quantity" in cols_lower:
            kpi_list.append("Quantity")
        if any(c in cols_lower for c in ["sales", "revenue", "amount"]) and any(c in cols_lower for c in ["order", "order_id", "transaction", "transaction_id", "id"]):
            kpi_list.append("Average Order Value")
        if not kpi_list:
            kpi_list = ["Revenue", "Profit", "Orders", "Quantity", "Average Order Value"]
    elif biz_domain == "Human Resources":
        if any(c in cols_lower for c in ["employee", "employee_id", "id"]):
            kpi_list.append("Employee Count")
        if "attrition" in cols_lower:
            kpi_list.append("Attrition Rate")
        if "salary" in cols_lower:
            kpi_list.append("Average Salary")
        if "department" in cols_lower:
            kpi_list.append("Department Strength")
        if any(c in cols_lower for c in ["perf_score", "performance", "rating"]):
            kpi_list.append("Performance Score")
        if not kpi_list:
            kpi_list = ["Employee Count", "Attrition Rate", "Average Salary", "Department Strength", "Performance Score"]
    elif biz_domain == "Healthcare":
        if any(c in cols_lower for c in ["patient", "patient_id", "id"]):
            kpi_list.append("Total Patients")
        if any(c in cols_lower for c in ["stay", "duration", "days"]):
            kpi_list.append("Average Stay Duration")
        if "recovery" in cols_lower:
            kpi_list.append("Recovery Rate")
        if "readmission" in cols_lower:
            kpi_list.append("Readmission Rate")
        if any(c in cols_lower for c in ["cost", "charge", "amount", "price"]):
            kpi_list.append("Treatment Cost")
        if not kpi_list:
            kpi_list = ["Total Patients", "Average Stay Duration", "Recovery Rate", "Readmission Rate", "Treatment Cost"]
    elif biz_domain == "Banking":
        if any(c in cols_lower for c in ["transaction", "transaction_id", "id"]):
            kpi_list.append("Total Transactions")
        if "loan" in cols_lower or "loan_amount" in cols_lower:
            kpi_list.append("Loan Amount")
        if "default" in cols_lower or "default_rate" in cols_lower:
            kpi_list.append("Default Rate")
        if any(c in cols_lower for c in ["balance", "amount"]):
            kpi_list.append("Customer Balance")
        if any(c in cols_lower for c in ["growth", "account"]):
            kpi_list.append("Account Growth")
        if not kpi_list:
            kpi_list = ["Total Transactions", "Loan Amount", "Default Rate", "Customer Balance", "Account Growth"]
    elif biz_domain == "Manufacturing":
        if "defect" in cols_lower or "defect_rate" in cols_lower:
            kpi_list.append("Defect Rate %")
        if "yield" in cols_lower:
            kpi_list.append("Yield %")
        if "downtime" in cols_lower:
            kpi_list.append("Machine Downtime")
        if "production" in cols_lower or "volume" in cols_lower:
            kpi_list.append("Production Output")
        if "sensor" in cols_lower or "temp" in cols_lower:
            kpi_list.append("Equipment Health")
        if not kpi_list:
            kpi_list = ["Production Output", "Yield %", "Defect Rate %", "Machine Downtime", "Equipment Health"]
    elif biz_domain == "Financial Services":
        if any(c in cols_lower for c in ["revenue", "sales", "income"]):
            kpi_list.append("Total Revenue")
        if any(c in cols_lower for c in ["profit", "income", "net"]):
            kpi_list.append("Net Income Margin")
        if "expense" in cols_lower or "cost" in cols_lower:
            kpi_list.append("Total Expenses")
        if "budget" in cols_lower:
            kpi_list.append("Budget Variance")
        if "tax" in cols_lower:
            kpi_list.append("Tax Liabilities")
        if not kpi_list:
            kpi_list = ["Total Revenue", "Net Income Margin", "Total Expenses", "Budget Variance", "Tax Liabilities"]
    elif biz_domain == "Customer Support":
        if any(c in cols_lower for c in ["ticket", "ticket_id", "id"]):
            kpi_list.append("Total Tickets")
        if "resolution_hours" in cols_lower:
            kpi_list.append("Average Resolution Time")
        if "sla_met" in cols_lower:
            kpi_list.append("SLA Compliance Rate")
        if not kpi_list:
            kpi_list = ["SLA Met Volume", "Average Resolution Time", "SLA Compliance Rate"]
    else:
        kpi_list = ["Row occurrences count", "Unique entity count", "Attribute completeness %"]
        
    return ", ".join(kpi_list)

# Test 1: Date + Sales/Profit/Quantity -> exact Revenue, Profit, Orders, Quantity, Average Order Value
t1 = recommend_kpis(["Order Date", "Sales", "Profit", "Quantity"], {"date": "Order Date"}, "E-Commerce / Sales")
print("Test 1:", t1)
assert t1 == "Revenue, Profit, Orders, Quantity, Average Order Value"

# Test 2: HR columns -> Attirition, salary, strength
t2 = recommend_kpis(["Employee_ID", "Tenure", "attrition", "salary"], {}, "Human Resources")
print("Test 2:", t2)
assert t2 == "Employee Count, Attrition Rate, Average Salary"

# Test 3: Healthcare columns -> Patients, Stay, Cost
t3 = recommend_kpis(["patient_id", "stay", "cost"], {}, "Healthcare")
print("Test 3:", t3)
assert t3 == "Total Patients, Average Stay Duration, Treatment Cost"

# Test 4: Banking columns -> Transactions balance
t4 = recommend_kpis(["transaction_id", "balance"], {}, "Banking")
print("Test 4:", t4)
assert t4 == "Total Transactions, Customer Balance"

# Test 5: Manufacturing columns -> defect yield
t5 = recommend_kpis(["defect_rate", "yield"], {}, "Manufacturing")
print("Test 5:", t5)
assert t5 == "Defect Rate %, Yield %"

print("\nVerification Passed Successfully!")

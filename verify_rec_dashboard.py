def recommend_db(columns, mapping):
    cols_lower = [c.lower().strip() for c in columns]
    
    date_col = mapping.get("date")
    if not date_col:
        # scan
        date_col = next((c for c in columns if "date" in c.lower() or "time" in c.lower() or "timestamp" in c.lower()), None)
        
    target_col = mapping.get("amount")
    if not target_col:
        target_col = next((c for c in columns if c.lower() in ["sales", "revenue", "amount", "profit"]), columns[0] if len(columns) > 0 else "")
        
    # Check date column matching
    has_date = date_col is not None and str(date_col).lower() != "none detected"
    has_sales_profit_qty = any(c.lower() in ["sales", "profit", "quantity", "revenue"] for c in columns)
    
    if has_date and has_sales_profit_qty:
        return "Executive Sales Dashboard"
    elif any(c.lower() in ["employee", "salary", "attrition", "perf_score", "tenure", "hr", "workforce", "department"] for c in columns):
        return "HR Workforce Dashboard"
    elif any(c.lower() in ["healthcare", "patient", "doctor", "diagnosis", "hospital", "clinic", "treatment", "medical"] for c in columns):
        return "Healthcare Analytics Dashboard"
    elif any(c.lower() in ["banking", "bank", "account", "transaction_type", "deposit", "withdrawal", "balance", "credit"] for c in columns):
        return "Banking Operations Dashboard"
    elif any(c.lower() in ["manufacturing", "factory", "machine", "production", "yield", "downtime", "defect", "sensor", "equip"] for c in columns):
        return "Manufacturing Performance Dashboard"
    elif any(c.lower() in ["financial", "finance", "revenue", "income", "expense", "budget", "cost", "tax", "profit_margin"] for c in columns):
        return "Financial Performance Dashboard"
    elif any(c.lower() in ["sales", "revenue", "amount", "price", "order", "spend"] for c in columns):
        return "Executive Sales Dashboard"
    elif any(c.lower() in ["ticket", "issues", "resolution_hours", "sla_met", "ticket_id"] for c in columns):
        return "Service SLA Analytics Dashboard"
    else:
        return "Operations Analytics Dashboard"

# Test 1: Date + Sales/Profit/Quantity -> Executive Sales Dashboard
t1 = recommend_db(["Order Date", "Sales"], {"date": "Order Date"})
print("Test 1:", t1)
assert t1 == "Executive Sales Dashboard"

# Test 2: Date + Profit -> Executive Sales Dashboard
t2 = recommend_db(["Transaction_Time", "Profit"], {})
print("Test 2:", t2)
assert t2 == "Executive Sales Dashboard"

# Test 3: HR columns -> HR Workforce Dashboard
t3 = recommend_db(["Employee_ID", "Tenure", "attrition"], {})
print("Test 3:", t3)
assert t3 == "HR Workforce Dashboard"

# Test 4: Financial columns -> Financial Performance Dashboard
t4 = recommend_db(["expense", "budget", "tax"], {})
print("Test 4:", t4)
assert t4 == "Financial Performance Dashboard"

# Test 5: Healthcare columns -> Healthcare Analytics Dashboard
t5 = recommend_db(["Patient_Name", "Diagnosis", "Hospital_Rating"], {})
print("Test 5:", t5)
assert t5 == "Healthcare Analytics Dashboard"

# Test 6: Banking columns -> Banking Operations Dashboard
t6 = recommend_db(["account_number", "deposit", "balance"], {})
print("Test 6:", t6)
assert t6 == "Banking Operations Dashboard"

# Test 7: Manufacturing columns -> Manufacturing Performance Dashboard
t7 = recommend_db(["machine_id", "yield", "downtime"], {})
print("Test 7:", t7)
assert t7 == "Manufacturing Performance Dashboard"

# Test 8: Unrelated columns -> Operations Analytics Dashboard
t8 = recommend_db(["other_column", "val"], {})
print("Test 8:", t8)
assert t8 == "Operations Analytics Dashboard"

print("\nVerification Passed Successfully!")

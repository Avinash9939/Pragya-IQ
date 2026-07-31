def recommend_ml(columns, mapping, biz_domain):
    cols_clean = [c.lower().strip() for c in columns]
    
    date_col = mapping.get("date")
    if not date_col:
        date_col = next((c for c in columns if "date" in c.lower() or "time" in c.lower() or "timestamp" in c.lower()), None)
        
    target_col = mapping.get("amount")
    if not target_col:
        target_col = next((c for c in columns if c.lower() in ["sales", "revenue", "amount", "profit"]), columns[0] if len(columns) > 0 else "")
        
    has_date = date_col is not None and str(date_col).lower() != "none detected"
    has_sales_profit_qty = any(c.lower() in ["sales", "profit", "quantity", "revenue"] for c in columns)
    
    if has_date and has_sales_profit_qty:
        return "Prophet Time Series Forecasting"
    elif any(x in cols_clean for x in ["churn", "attrition", "exit", "dropout", "leaving"]):
        return "Classification (XGBoost / Random Forest)"
    elif any(x in cols_clean for x in ["house", "price", "sqft", "bedroom", "bathroom", "home", "real_estate", "property_type"]):
        return "Regression"
    elif any(x in cols_clean for x in ["segment", "spending_score", "cluster", "annual_income"]):
        return "K-Means Clustering"
    elif any(x in cols_clean for x in ["fraud", "is_fraud", "anomaly", "fraudulent"]):
        return "Anomaly Detection"
    elif any(x in cols_clean for x in ["rating", "user_id", "item_id", "movie_id", "product_id"]) and any(x in cols_clean for x in ["rating", "like", "click"]):
        return "Recommendation Engine"
    elif biz_domain == "Customer Support":
        return "XGBoost Time Series Regressor"
    elif has_date and target_col and any(c.lower() == str(target_col).lower().strip() for c in cols_clean):
        return "Prophet Time Series Forecasting"
    elif any(c.lower() in ["status", "is_active", "target", "label", "class"] for c in cols_clean):
        return "Classification (XGBoost / Random Forest)"
    elif target_col and target_col != columns[0]:
        return "Regression"
    else:
        return "K-Means Clustering"

# Test 1: Date + Sales -> Prophet Time Series Forecasting
t1 = recommend_ml(["Order Date", "Sales"], {"date": "Order Date"}, "E-Commerce / Sales")
print("Test 1:", t1)
assert t1 == "Prophet Time Series Forecasting"

# Test 2: Churn columns -> Classification
t2 = recommend_ml(["customer_id", "churn", "tenure"], {}, "E-Commerce")
print("Test 2:", t2)
assert t2 == "Classification (XGBoost / Random Forest)"

# Test 3: House price -> Regression
t3 = recommend_ml(["sqft", "bedroom", "price"], {}, "Real Estate")
print("Test 3:", t3)
assert t3 == "Regression"

# Test 4: Segment columns -> K-Means Clustering
t4 = recommend_ml(["customer_id", "spending_score", "annual_income"], {}, "Marketing")
print("Test 4:", t4)
assert t4 == "K-Means Clustering"

# Test 5: Fraud columns -> Anomaly Detection
t5 = recommend_ml(["transaction_id", "is_fraud", "amount"], {}, "Banking")
print("Test 5:", t5)
assert t5 == "Anomaly Detection"

# Test 6: Rating system columns -> Recommendation Engine
t6 = recommend_ml(["user_id", "product_id", "rating"], {}, "E-Commerce")
print("Test 6:", t6)
assert t6 == "Recommendation Engine"

print("\nVerification Passed Successfully!")

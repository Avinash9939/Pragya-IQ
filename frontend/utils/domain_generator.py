import pandas as pd
import numpy as np

def generate_domain_dataset(domain_type: str, n_records: int = 800) -> pd.DataFrame:
    np.random.seed(42)
    # Generate common columns
    start_date = pd.to_datetime("2026-01-01")
    date_offsets = np.random.randint(0, 365, size=n_records)
    dates = start_date + pd.to_timedelta(date_offsets, unit="D")
    
    regions = np.random.choice(["East", "West", "North", "South", "Central"], size=n_records)
    states = np.random.choice(["NY", "CA", "IL", "FL", "TX", "MA", "WA", "GA", "CO", "MI"], size=n_records)
    
    # Category, Customer, Product, Department, Branch
    if domain_type == "🛒 E-Commerce":
        categories = np.random.choice(["Electronics", "Fashion", "Home", "Sports", "Beauty"], size=n_records)
        customers = [f"Cust-{np.random.randint(100, 999)}" for _ in range(n_records)]
        products = np.random.choice(["Laptop", "T-Shirt", "Sofa", "Dumbbell", "Lipstick", "Headphones", "Sneakers", "Blender"], size=n_records)
        departments = np.random.choice(["Retail Sales", "Online Store", "Corporate Clients"], size=n_records)
        branches = np.random.choice(["Branch East", "Branch West", "Central Depot", "South Warehouse"], size=n_records)
        
        # Metrics
        revenue = np.random.uniform(15.0, 1200.0, size=n_records).round(2)
        quantity = np.random.randint(1, 6, size=n_records)
        discount = np.random.uniform(0.0, 0.25, size=n_records).round(2)
        expenses = (revenue * np.random.uniform(0.4, 0.70, size=n_records)).round(2)
        
        df = pd.DataFrame({
            "Date": dates,
            "Region": regions,
            "State": states,
            "Category": categories,
            "Customer": customers,
            "Product": products,
            "Department": departments,
            "Branch": branches,
            "Revenue": revenue,
            "Quantity": quantity,
            "Discount": discount,
            "Expenses": expenses,
            "Orders": np.ones(n_records, dtype=int)
        })
        
    elif domain_type == "👥 HR":
        categories = np.random.choice(["Full-Time", "Part-Time", "Contractor"], size=n_records)
        customers = [f"Talent-{np.random.randint(10, 99)}" for _ in range(n_records)] # Placeholder to satisfy slicer requirement
        products = np.random.choice(["Recruiting", "L&D Services", "Payroll System", "Onboarding Module"], size=n_records) # Placeholder to satisfy slicer
        departments = np.random.choice(["Engineering", "Sales", "Finance", "HR", "Marketing", "Product"], size=n_records)
        branches = np.random.choice(["NY Headquarter", "CA Hub", "TX Office", "Remote Hub"], size=n_records)
        
        # Metrics
        salary = np.random.uniform(45000, 175000, size=n_records).round(-2)
        perf_score = np.random.choice([1, 2, 3, 4, 5], p=[0.05, 0.15, 0.50, 0.20, 0.10], size=n_records)
        attrition = np.random.choice([0, 1], p=[0.88, 0.12], size=n_records)
        tenure = np.random.uniform(0.5, 10.0, size=n_records).round(1)
        
        df = pd.DataFrame({
            "Date": dates,
            "Region": regions,
            "State": states,
            "Category": categories,
            "Customer": customers,
            "Product": products,
            "Department": departments,
            "Branch": branches,
            "Salary": salary,
            "Performance_Score": perf_score,
            "Attrition": attrition,
            "Tenure": tenure,
            "Employees": np.ones(n_records, dtype=int)
        })
        
    elif domain_type == "💰 Finance":
        categories = np.random.choice(["Corporate", "SME", "Retail", "Government"], size=n_records)
        customers = [f"Client-{np.random.randint(100, 490)}" for _ in range(n_records)]
        products = np.random.choice(["Consulting", "SaaS License", "Hardware", "Premium Support"], size=n_records)
        departments = np.random.choice(["Operations", "Treasury", "Lending", "Investment"], size=n_records)
        branches = np.random.choice(["NYC HQ", "London Office", "Tokyo Branch", "Singapore Hub"], size=n_records)
        
        # Metrics
        revenue = np.random.uniform(5000.0, 100000.0, size=n_records).round(2)
        expenses = (revenue * np.random.uniform(0.5, 0.85, size=n_records)).round(2)
        net_profit = (revenue - expenses).round(2)
        margin = ((net_profit / revenue) * 100).round(2)
        
        df = pd.DataFrame({
            "Date": dates,
            "Region": regions,
            "State": states,
            "Category": categories,
            "Customer": customers,
            "Product": products,
            "Department": departments,
            "Branch": branches,
            "Revenue": revenue,
            "Expenses": expenses,
            "Net_Profit": net_profit,
            "Margin": margin
        })
        
    else:  # "🎫 Service Tickets"
        categories = np.random.choice(["Access Issue", "Hardware Fault", "Billing Enquiry", "Software Bug"], size=n_records)
        customers = [f"User-{np.random.randint(1000, 9999)}" for _ in range(n_records)]
        products = np.random.choice(["Office Suite", "Cloud Storage", "ERP system", "CRM portal"], size=n_records)
        departments = np.random.choice(["IT Support", "Customer Success", "Finance Ops", "Engineering Helpdesk"], size=n_records)
        branches = np.random.choice(["North Facility", "South Facility", "East Warehouse", "Main Office"], size=n_records)
        
        # Metrics
        resolution_hours = np.random.uniform(0.5, 72.0, size=n_records).round(1)
        satisfaction_score = np.random.choice([1, 2, 3, 4, 5], p=[0.08, 0.12, 0.20, 0.40, 0.20], size=n_records)
        status_flag = np.random.choice([1, 0], p=[0.85, 0.15], size=n_records)  # 1 = Closed, 0 = Open
        sla_flag = np.random.choice([1, 0], p=[0.78, 0.22], size=n_records)  # 1 = Met, 0 = Breached
        
        df = pd.DataFrame({
            "Date": dates,
            "Region": regions,
            "State": states,
            "Category": categories,
            "Customer": customers,
            "Product": products,
            "Department": departments,
            "Branch": branches,
            "Tickets": np.ones(n_records, dtype=int),
            "Closed": status_flag,
            "SLA_Met": sla_flag,
            "Resolution_Hours": resolution_hours,
            "Satisfaction_Score": satisfaction_score
        })
        
    return df

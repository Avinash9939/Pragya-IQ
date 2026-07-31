import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_contoso_tickets() -> pd.DataFrame:
    """
    Generates a realistic synthetic ticket volume dataset conforming to Contoso's dashboard.
    Why: Feeds high-fidelity widgets for year, month, priority, severity, work type, category, etc.
    """
    np.random.seed(42)
    n_tickets = 26935
    
    # Generate dates across 2026
    start_date = datetime(2026, 1, 1)
    date_offsets = np.random.randint(0, 365, size=n_tickets)
    dates = [start_date + timedelta(days=int(offset)) for offset in date_offsets]
    
    # Priority distributions: High (38%), Mid (16.4%), Low (45.6%)
    priority_choices = ["High", "Mid", "Low"]
    priority_probs = [0.38, 0.164, 0.456]
    priorities = np.random.choice(priority_choices, size=n_tickets, p=priority_probs)
    
    # Work Type: Service Request (55%), Incident (45%)
    wt_choices = ["Service Request", "Incident"]
    wt_probs = [0.55, 0.45]
    work_types = np.random.choice(wt_choices, size=n_tickets, p=wt_probs)
    
    # Severity distributions
    sev_choices = ["Normal", "Low", "Minor", "Major", "Critical"]
    sev_probs = [0.47, 0.22, 0.18, 0.10, 0.03]
    severities = np.random.choice(sev_choices, size=n_tickets, p=sev_probs)
    
    # Category distributions
    cat_choices = ["System", "Login Access", "Software", "Hardware"]
    cat_probs = [0.42, 0.28, 0.18, 0.12]
    categories = np.random.choice(cat_choices, size=n_tickets, p=cat_probs)
    
    # Agents
    agent_choices = ["David Wilson", "Joseph Hall", "Victor Bell", "Rose Young", "Britney Watts"]
    agents = np.random.choice(agent_choices, size=n_tickets)
    
    # Satisfaction rating: Average around 4.2
    ratings = np.clip(np.random.normal(4.2, 0.8, size=n_tickets), 1.0, 5.0)
    ratings = np.round(ratings, 1)
    
    # SLA status: Within SLA (72.5%), Missed (27.5%)
    sla_choices = ["Within SLA", "Missed SLA"]
    sla_probs = [0.725, 0.275]
    sla_status = np.random.choice(sla_choices, size=n_tickets, p=sla_probs)
    
    # Status: Closed (26860 closed vs 26935 created total, which is 99.72% closure rate)
    status_choices = ["Closed", "Open"]
    status_probs = [0.9972, 0.0028]
    statuses = np.random.choice(status_choices, size=n_tickets, p=status_probs)
    
    # States for Filled Map (choropleth)
    state_choices = ["CA", "TX", "NY", "FL", "IL", "PA", "OH", "GA", "NC", "MI", "WA", "AZ", "CO", "MA", "VA"]
    states = np.random.choice(state_choices, size=n_tickets)
    
    df = pd.DataFrame({
        "Date": dates,
        "Year": [d.year for d in dates],
        "Month": [d.strftime("%B") for d in dates],
        "Month_Num": [d.month for d in dates],
        "Priority": priorities,
        "Severity": severities,
        "Work_Type": work_types,
        "Category": categories,
        "Agent": agents,
        "Rating": ratings,
        "SLA": sla_status,
        "Status": statuses,
        "State": states
    })
    
    # Sort chronologically
    df = df.sort_values(by="Date").reset_index(drop=True)
    return df

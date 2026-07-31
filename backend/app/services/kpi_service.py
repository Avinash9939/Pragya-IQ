import os
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, Any, List
from app.domain.entities.kpi_result import KpiResult
from app.domain.interfaces.dataset_repository import DatasetRepositoryInterface
from app.domain.interfaces.kpi_result_repository import KpiResultRepositoryInterface
from app.infrastructure.storage.local_storage import LocalStorage

class MissingColumnMappingError(Exception):
    """Exception raised when required semantic mapping keys are not set."""
    def __init__(self, missing_keys: List[str]) -> None:
        self.missing_keys = missing_keys
        super().__init__(f"Missing required column mappings: {', '.join(missing_keys)}")

class KpiService:
    """
    Service layer executing business logic KPI calculations and transactional database persistence.
    Why: Decouples raw pandas mathematics and mapping resolution from REST API routers.
    """
    def __init__(
        self,
        dataset_repo: DatasetRepositoryInterface,
        kpi_result_repo: KpiResultRepositoryInterface,
        storage_adapter: LocalStorage
    ) -> None:
        self.dataset_repo = dataset_repo
        self.kpi_repo = kpi_result_repo
        self.storage = storage_adapter

    def _load_dataframe(self, dataset_id: int) -> tuple[pd.DataFrame, dict]:
        """Helper to get dataset, verify column mappings, and load output file."""
        dataset = self.dataset_repo.get_by_id(dataset_id)
        if not dataset:
            raise ValueError(f"Dataset with id {dataset_id} not found")

        mapping = dataset.column_mapping or {}
        file_path = self.storage.get_path(dataset.storage_path)
        for suffix in ["_cleaned_features.csv", "_cleaned_features.xlsx"]:
            if suffix in file_path:
                clean_path = file_path.replace("_features", "")
                if os.path.exists(clean_path):
                    file_path = clean_path
                    break
                raw_path = file_path.replace("_cleaned_features", "")
                if os.path.exists(raw_path):
                    file_path = raw_path
                    break

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Source file not found at {file_path}")

        # Read CSV or Excel
        if file_path.lower().endswith(".csv"):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)

        return df, mapping

    def _get_midpoint_date(self, df: pd.DataFrame, date_col: str) -> tuple[pd.DataFrame, pd.Timestamp]:
        """Helper to parse date column and compute chronological midpoint."""
        dates = pd.to_datetime(df[date_col])
        df_copy = df.copy()
        df_copy[date_col] = dates
        min_date = dates.min()
        max_date = dates.max()
        if pd.isna(min_date) or pd.isna(max_date) or min_date == max_date:
            return df_copy, min_date
        midpoint = min_date + (max_date - min_date) / 2
        return df_copy, midpoint

    def compute_sales_kpis(self, dataset_id: int) -> KpiResult:
        """Compute sales KPIs: total revenue, growth % vs previous period, average order value, top 5 products."""
        df, mapping = self._load_dataframe(dataset_id)
        
        required = ["date", "amount", "product"]
        missing = [k for k in required if k not in mapping]
        if missing:
            raise MissingColumnMappingError(missing)

        date_col = mapping["date"]
        sales_col = next((c for c in df.columns if c.strip().lower() in ["sales", "revenue"]), None)
        amount_col = sales_col if sales_col else mapping["amount"]
        product_col = mapping["product"]

        revenue = float(df[amount_col].sum())
        
        order_col = next((c for c in df.columns if c.lower() in ["order_id", "order_no", "order_number", "transaction_id", "invoice_id"]), None)
        total_orders = df[order_col].nunique() if order_col and order_col in df.columns else len(df)
        aov = revenue / total_orders if total_orders > 0 else 0.0

        # Growth calculation by dividing timeline chronologically
        df_parsed, midpoint = self._get_midpoint_date(df, date_col)
        growth_pct = 0.0
        if midpoint and not pd.isna(midpoint):
            p1_rev = df_parsed.loc[df_parsed[date_col] < midpoint, amount_col].sum()
            p2_rev = df_parsed.loc[df_parsed[date_col] >= midpoint, amount_col].sum()
            if p1_rev > 0:
                growth_pct = float(((p2_rev - p1_rev) / p1_rev) * 100.0)

        # Top 5 products by sum of revenue
        top_products = df.groupby(product_col)[amount_col].sum().sort_values(ascending=False).head(5)
        top_products_dict = {str(k): float(v) for k, v in top_products.items()}

        val_json = {
            "total_revenue": revenue,
            "revenue_growth_percent": growth_pct,
            "average_order_value": aov,
            "top_products": top_products_dict
        }

        result = KpiResult(
            id=None,
            dataset_id=dataset_id,
            kpi_type="sales",
            value_json=val_json,
            computed_at=datetime.now(timezone.utc)
        )
        return self.kpi_repo.create(result)

    def compute_customer_kpis(self, dataset_id: int) -> KpiResult:
        """Compute customer KPIs: unique customers, new vs returning, and simple CLV estimate."""
        df, mapping = self._load_dataframe(dataset_id)

        required = ["customer_id", "amount", "date"]
        missing = [k for k in required if k not in mapping]
        if missing:
            raise MissingColumnMappingError(missing)

        cust_col = mapping["customer_id"]
        sales_col = next((c for c in df.columns if c.strip().lower() in ["sales", "revenue"]), None)
        amount_col = sales_col if sales_col else mapping["amount"]
        date_col = mapping["date"]

        unique_cust = int(df[cust_col].nunique())

        # New vs returning customer counts (Period 2 vs Period 1)
        df_parsed, midpoint = self._get_midpoint_date(df, date_col)
        new_count = 0
        returning_count = 0
        if midpoint and not pd.isna(midpoint) and unique_cust > 0:
            p1_custs = set(df_parsed.loc[df_parsed[date_col] < midpoint, cust_col].dropna().unique())
            p2_custs = set(df_parsed.loc[df_parsed[date_col] >= midpoint, cust_col].dropna().unique())
            
            returning_custs = p2_custs.intersection(p1_custs)
            new_custs = p2_custs - p1_custs
            
            returning_count = len(returning_custs)
            new_count = len(new_custs)
        else:
            new_count = unique_cust

        # Simple CLV: average order value * average orders per customer
        if unique_cust > 0:
            clv = float(df[amount_col].sum() / unique_cust)
        else:
            clv = 0.0

        val_json = {
            "total_unique_customers": unique_cust,
            "new_customers": new_count,
            "returning_customers": returning_count,
            "customer_lifetime_value_estimate": clv
        }

        result = KpiResult(
            id=None,
            dataset_id=dataset_id,
            kpi_type="customer",
            value_json=val_json,
            computed_at=datetime.now(timezone.utc)
        )
        return self.kpi_repo.create(result)

    def compute_product_kpis(self, dataset_id: int) -> KpiResult:
        """Compute product sellers by revenue and quantity (if quantity mapped)."""
        df, mapping = self._load_dataframe(dataset_id)

        required = ["product", "amount"]
        missing = [k for k in required if k not in mapping]
        if missing:
            raise MissingColumnMappingError(missing)

        prod_col = mapping["product"]
        sales_col = next((c for c in df.columns if c.strip().lower() in ["sales", "revenue"]), None)
        amount_col = sales_col if sales_col else mapping["amount"]

        # Best / Worst by revenue
        rev_grouped = df.groupby(prod_col)[amount_col].sum()
        best_revenue = str(rev_grouped.idxmax()) if not rev_grouped.empty else "N/A"
        worst_revenue = str(rev_grouped.idxmin()) if not rev_grouped.empty else "N/A"

        val_json = {
            "best_seller_revenue": {
                "product": best_revenue,
                "value": float(rev_grouped.max()) if not rev_grouped.empty else 0.0
            },
            "worst_seller_revenue": {
                "product": worst_revenue,
                "value": float(rev_grouped.min()) if not rev_grouped.empty else 0.0
            }
        }

        # Quantity calculations
        qty_col = next((c for c in df.columns if c.strip().lower() == "quantity"), None)
        if not qty_col and "quantity" in mapping:
            qty_col = mapping["quantity"]
            
        if qty_col and qty_col in df.columns:
            qty_grouped = df.groupby(prod_col)[qty_col].sum()
            best_qty = str(qty_grouped.idxmax()) if not qty_grouped.empty else "N/A"
            worst_qty = str(qty_grouped.idxmin()) if not qty_grouped.empty else "N/A"
            
            val_json["best_seller_quantity"] = {
                "product": best_qty,
                "value": int(qty_grouped.max()) if not qty_grouped.empty else 0
            }
            val_json["worst_seller_quantity"] = {
                "product": worst_qty,
                "value": int(qty_grouped.min()) if not qty_grouped.empty else 0
            }

        result = KpiResult(
            id=None,
            dataset_id=dataset_id,
            kpi_type="product",
            value_json=val_json,
            computed_at=datetime.now(timezone.utc)
        )
        return self.kpi_repo.create(result)

    def compute_regional_kpis(self, dataset_id: int) -> KpiResult:
        """Compute regional metrics: revenue by region, region-over-region growth metrics."""
        df, mapping = self._load_dataframe(dataset_id)

        required = ["region", "amount", "date"]
        missing = [k for k in required if k not in mapping]
        if missing:
            raise MissingColumnMappingError(missing)

        region_col = mapping["region"]
        sales_col = next((c for c in df.columns if c.strip().lower() in ["sales", "revenue"]), None)
        amount_col = sales_col if sales_col else mapping["amount"]
        date_col = mapping["date"]

        # Revenue by region
        reg_rev = df.groupby(region_col)[amount_col].sum()
        reg_rev_dict = {str(k): float(v) for k, v in reg_rev.items()}

        # Growth by region (Period 2 vs Period 1)
        df_parsed, midpoint = self._get_midpoint_date(df, date_col)
        reg_growth_dict = {}

        for region in reg_rev.index:
            reg_df = df_parsed[df_parsed[region_col] == region]
            reg_growth = 0.0
            if midpoint and not pd.isna(midpoint) and len(reg_df) > 0:
                p1_rev = reg_df.loc[reg_df[date_col] < midpoint, amount_col].sum()
                p2_rev = reg_df.loc[reg_df[date_col] >= midpoint, amount_col].sum()
                if p1_rev > 0:
                    reg_growth = float(((p2_rev - p1_rev) / p1_rev) * 100.0)
            
            reg_growth_dict[str(region)] = reg_growth

        val_json = {
            "revenue_by_region": reg_rev_dict,
            "regional_growth_percent": reg_growth_dict
        }

        result = KpiResult(
            id=None,
            dataset_id=dataset_id,
            kpi_type="region",
            value_json=val_json,
            computed_at=datetime.now(timezone.utc)
        )
        return self.kpi_repo.create(result)

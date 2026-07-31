from datetime import datetime, timezone
import os
from typing import Optional, List, Any
import json

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from app.domain.entities.report import Report
from app.domain.interfaces.report_repository import ReportRepositoryInterface
from app.domain.interfaces.dataset_repository import DatasetRepositoryInterface
from app.domain.interfaces.kpi_result_repository import KpiResultRepositoryInterface
from app.domain.interfaces.ml_repository import MlRunRepositoryInterface, MlPredictionRepositoryInterface
from app.services.ai_service import AIService


class ReportService:
    """
    Service layer compiling business metrics, ML runs, and AI cached conclusions into an elegant PDF.
    Why: Keeps PDF construction layouts separate from api layer validation logic.
    """
    def __init__(
        self,
        dataset_repo: DatasetRepositoryInterface,
        kpi_repo: KpiResultRepositoryInterface,
        ml_run_repo: MlRunRepositoryInterface,
        ml_pred_repo: MlPredictionRepositoryInterface,
        ai_service: AIService,
        report_repo: ReportRepositoryInterface,
        storage_base_dir: str = "storage"
    ) -> None:
        self.dataset_repo = dataset_repo
        self.kpi_repo = kpi_repo
        self.ml_run_repo = ml_run_repo
        self.ml_pred_repo = ml_pred_repo
        self.ai_service = ai_service
        self.report_repo = report_repo
        self.storage_base_dir = storage_base_dir

    def generate(self, dataset_id: int) -> Report:
        """
        Gathers KPIs, ML summaries, AI summary/recs, structures flowable canvas story,
        builds PDF, and persists Report database entry.
        """
        # Load dataset
        dataset = self.dataset_repo.get_by_id(dataset_id)
        if not dataset:
            raise ValueError(f"Dataset with id {dataset_id} not found")

        # Load all KPIs
        kpis = self.kpi_repo.list_by_dataset_id(dataset_id)
        sales_kpi = next((k for k in kpis if k.kpi_type == "sales"), None)
        customer_kpi = next((k for k in kpis if k.kpi_type == "customer"), None)
        product_kpi = next((k for k in kpis if k.kpi_type == "product"), None)
        region_kpi = next((k for k in kpis if k.kpi_type == "region"), None)

        # Build ML Summary context
        all_runs = self.ml_run_repo.list_by_dataset_id(dataset_id)
        all_runs = sorted(all_runs, key=lambda r: r.created_at, reverse=True)

        forecast_run = next((r for r in all_runs if r.model_type in ("prophet", "xgboost")), None)
        forecast_preds = []
        if forecast_run:
            forecast_preds = self.ml_pred_repo.list_by_run_id(forecast_run.id)
            forecast_preds = sorted(forecast_preds, key=lambda p: p.entity_ref)

        churn_run = next((r for r in all_runs if r.model_type == "xgboost_churn"), None)
        churn_preds = []
        if churn_run:
            churn_preds = self.ml_pred_repo.list_by_run_id(churn_run.id)
            churn_preds = sorted(churn_preds, key=lambda p: p.prediction, reverse=True)

        anomaly_run = next((r for r in all_runs if r.model_type == "isolation_forest"), None)
        anomaly_count = 0
        if anomaly_run:
            anomaly_count = anomaly_run.metrics_json.get("anomaly_count", 0)

        # Generate AI Executive Summary and recommendations (regenerate=False)
        ai_summary = self.ai_service.generate_executive_summary(dataset_id, regenerate=False)
        ai_recommendations = self.ai_service.generate_recommendations(dataset_id, regenerate=False)

        # Ensure directory structure
        user_id = dataset.user_id
        reports_dir = os.path.join(self.storage_base_dir, str(user_id), str(dataset_id), "reports")
        os.makedirs(reports_dir, exist_ok=True)

        filename = f"report_{int(datetime.now(timezone.utc).timestamp())}.pdf"
        file_path = os.path.join(reports_dir, filename)

        # Design PDF
        doc = SimpleDocTemplate(
            file_path,
            pagesize=letter,
            rightMargin=54,
            leftMargin=54,
            topMargin=54,
            bottomMargin=54
        )

        styles = getSampleStyleSheet()
        
        # Define clean, cohesive styles
        primary_color = colors.HexColor("#1A365D")
        text_color = colors.HexColor("#2D3748")
        
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=24,
            leading=28,
            textColor=primary_color,
            spaceAfter=15
        )
        
        meta_style = ParagraphStyle(
            'ReportMeta',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#718096"),
            spaceAfter=30
        )
        
        heading_style = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontSize=14,
            leading=18,
            textColor=primary_color,
            spaceBefore=15,
            spaceAfter=10,
            keepWithNext=True
        )

        body_style = ParagraphStyle(
            'ReportBody',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            textColor=text_color,
            spaceAfter=10
        )

        th_style = ParagraphStyle(
            'TableHeader',
            parent=styles['Normal'],
            fontSize=9,
            leading=11,
            textColor=colors.white,
            fontName="Helvetica-Bold"
        )

        td_style = ParagraphStyle(
            'TableCell',
            parent=styles['Normal'],
            fontSize=9,
            leading=11,
            textColor=text_color
        )

        story = []

        # Cover / Header
        story.append(Paragraph("Business Analytics & AI Executive Report", title_style))
        story.append(Paragraph(
            f"<b>Dataset:</b> {dataset.filename or 'N/A'}<br/>"
            f"<b>Generated At:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
            meta_style
        ))
        
        # Section 1: AI Executive Summary
        story.append(Paragraph("1. Executive Summary", heading_style))
        story.append(Paragraph(ai_summary or "No executive summary available.", body_style))
        story.append(Spacer(1, 10))

        # Section 2: AI Recommendations
        story.append(Paragraph("2. Actionable Recommendations", heading_style))
        if ai_recommendations:
            for idx, rec in enumerate(ai_recommendations, 1):
                story.append(Paragraph(f"{idx}. {rec}", body_style))
        else:
            story.append(Paragraph("No recommendations available.", body_style))
        story.append(Spacer(1, 10))

        # Section 3: Computed Key Performance Indicators (KPIs)
        story.append(Paragraph("3. Computed KPIs Summary", heading_style))
        
        # Build a table of KPIs
        kpi_data = [[Paragraph("KPI Metric", th_style), Paragraph("Value Detail", th_style)]]
        
        # Sales KPIs
        if sales_kpi and sales_kpi.value_json:
            v = sales_kpi.value_json
            kpi_data.append([Paragraph("Total Revenue", td_style), Paragraph(f"${v.get('total_revenue', 0.0):,.2f}", td_style)])
            kpi_data.append([Paragraph("Revenue Growth Rate", td_style), Paragraph(f"{v.get('revenue_growth_percent', 0.0):.2f}%", td_style)])
            kpi_data.append([Paragraph("Average Order Value (AOV)", td_style), Paragraph(f"${v.get('average_order_value', 0.0):,.2f}", td_style)])
        
        # Customer KPIs
        if customer_kpi and customer_kpi.value_json:
            v = customer_kpi.value_json
            kpi_data.append([Paragraph("Unique Customers Count", td_style), Paragraph(f"{v.get('total_unique_customers', 0):,}", td_style)])
            kpi_data.append([Paragraph("Customer LTV Estimate", td_style), Paragraph(f"${v.get('customer_lifetime_value_estimate', 0.0):,.2f}", td_style)])
            kpi_data.append([Paragraph("New vs. Returning", td_style), Paragraph(f"New: {v.get('new_customers', 0)} | Returning: {v.get('returning_customers', 0)}", td_style)])

        # Product KPIs
        if product_kpi and product_kpi.value_json:
            v = product_kpi.value_json
            best_sell = v.get("best_seller_revenue", {})
            worst_sell = v.get("worst_seller_revenue", {})
            kpi_data.append([Paragraph("Best Seller by Revenue", td_style), Paragraph(f"{best_sell.get('product', 'N/A')} (${best_sell.get('value', 0.0):,.2f})", td_style)])
            kpi_data.append([Paragraph("Worst Seller by Revenue", td_style), Paragraph(f"{worst_sell.get('product', 'N/A')} (${worst_sell.get('value', 0.0):,.2f})", td_style)])

        # Regional KPIs
        if region_kpi and region_kpi.value_json:
            v = region_kpi.value_json
            regions_rev = v.get("revenue_by_region", {})
            region_str = ", ".join([f"{reg}: ${val:,.2f}" for reg, val in regions_rev.items()])
            kpi_data.append([Paragraph("Regional Revenue breakdown", td_style), Paragraph(region_str or "N/A", td_style)])

        kpi_table = Table(kpi_data, colWidths=[200, 300])
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), primary_color),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
        ]))
        story.append(kpi_table)
        story.append(Spacer(1, 10))

        # Section 4: Machine Learning Insights
        story.append(Paragraph("4. Predictive Machine Learning Insights", heading_style))
        
        ml_lines = []
        if forecast_run:
            ml_lines.append(f"<b>Forecast Model:</b> {forecast_run.model_type.upper()}")
            if forecast_preds:
                first_pred = forecast_preds[0].prediction
                last_pred = forecast_preds[-1].prediction
                ml_lines.append(f"<b>Forecast Outlook:</b> Started at ${first_pred:,.2f}, projected to end at ${last_pred:,.2f}.")
        if churn_run:
            ml_lines.append("<b>Latest Churn Analysis:</b> Classification report shows risk indicators mapped.")
            if churn_preds:
                top_risk = [f"Cust {cp.entity_ref} ({cp.prediction*100:.1f}%)" for cp in churn_preds[:3]]
                ml_lines.append(f"<b>Top Churn Risks:</b> {', '.join(top_risk)}")
        if anomaly_run:
            ml_lines.append(f"<b>Flagged Anomalies Count:</b> {anomaly_count} outlier entries detected in Isolation Forest run.")

        if ml_lines:
            for ml_line in ml_lines:
                story.append(Paragraph(ml_line, body_style))
        else:
            story.append(Paragraph("No recent machine learning training runs are available.", body_style))

        # Build PDF
        doc.build(story)

        # Register report entity
        report_entity = Report(
            id=None,
            dataset_id=dataset_id,
            file_path=file_path,
            generated_at=datetime.now(timezone.utc)
        )
        return self.report_repo.create(report_entity)

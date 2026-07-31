import os
import json
import re
from datetime import datetime, timezone
from typing import Optional, Tuple, List, Any
from langchain_core.prompts import PromptTemplate
from app.domain.entities.chat import MessageRole
from app.domain.interfaces.chat_repository import ChatRepositoryInterface
from app.infrastructure.vectorstore.faiss_store import FaissVectorStore

from app.domain.entities.ai_output import AiOutput
from app.domain.interfaces.ai_output_repository import AiOutputRepositoryInterface
from app.domain.interfaces.kpi_result_repository import KpiResultRepositoryInterface
from app.domain.interfaces.ml_repository import MlRunRepositoryInterface, MlPredictionRepositoryInterface


RAG_PROMPT_TEMPLATE = PromptTemplate(
    input_variables=["context", "question"],
    template=(
        "You are a business data analyst assistant. "
        "Answer the user's question ONLY using the provided context excerpts "
        "from their dataset analytics. "
        "If the answer is not present in the context, say: "
        "'I could not find that information in the indexed dataset context.' "
        "Do NOT guess or use outside knowledge.\n\n"
        "=== CONTEXT ===\n{context}\n"
        "=== END CONTEXT ===\n\n"
        "Question: {question}\n"
        "Answer:"
    )
)

RECOMMENDATIONS_PROMPT_TEMPLATE = PromptTemplate(
    input_variables=["kpis_context", "ml_context"],
    template=(
        "You are a senior business intelligence analyst.\n"
        "Analyze the following dataset KPI metrics and machine learning summaries, and generate 3 to 5 concrete, actionable, numbered business recommendations.\n"
        "CRITICAL: Every recommendation must be directly grounded in the provided numerical data. Reference specific metrics, percentages, names, or dollar amounts from the data.\n\n"
        "=== DATASET KPIS ===\n"
        "{kpis_context}\n\n"
        "=== MACHINE LEARNING FORECAST & ANALYTICS ===\n"
        "{ml_context}\n\n"
        "Format your output exactly as a numbered list from 1 to N. Each line must be formatted EXACTLY like this (do not include any intro or outro text):\n"
        "1. [Action Title] | Reason: [Business Reason] | Expected Impact: [Expected Impact] | Priority Level: [High/Medium/Low]\n"
        "2. [Action Title] | Reason: [Business Reason] | Expected Impact: [Expected Impact] | Priority Level: [High/Medium/Low]\n"
    )
)

EXECUTIVE_SUMMARY_PROMPT_TEMPLATE = PromptTemplate(
    input_variables=["kpis_context", "ml_context"],
    template=(
        "You are a senior business intelligence analyst.\n"
        "Analyze the following dataset KPI metrics and machine learning summaries, and write a professional, cohesive Executive Summary of the business performance.\n"
        "The summary should be a plain-English narrative of 150 to 250 words, suitable for a non-technical business owner.\n"
        "Ground the narrative in the key highlights from the KPIs and machine learning predictions. Do not assume or invent facts outside the provided data.\n\n"
        "=== DATASET KPIS ===\n"
        "{kpis_context}\n\n"
        "=== MACHINE LEARNING FORECAST & ANALYTICS ===\n"
        "{ml_context}\n\n"
        "Write only the summary narrative. No bullet points, no titles, and no intro/outro conversational filler."
    )
)


class SessionNotFoundError(Exception):
    pass


class SessionOwnershipError(PermissionError):
    pass


class IndexNotFoundError(Exception):
    pass


class AIService:
    """
    Orchestrates the RAG pipeline: FAISS retrieval → prompt assembly → LLM generation.
    Also handles global recommenders and executive summary builders caching.
    Why: Decouples the multi-step Q&A flow and business reporting from HTTP concerns.
    """

    def __init__(
        self,
        embedding_client,
        llm_client,
        chat_repo: ChatRepositoryInterface,
        kpi_repo: Optional[KpiResultRepositoryInterface] = None,
        ml_run_repo: Optional[MlRunRepositoryInterface] = None,
        ml_pred_repo: Optional[MlPredictionRepositoryInterface] = None,
        ai_output_repo: Optional[AiOutputRepositoryInterface] = None,
        storage_base_dir: str = "storage"
    ) -> None:
        self.embedding_client = embedding_client
        self.llm_client = llm_client
        self.chat_repo = chat_repo
        self.kpi_repo = kpi_repo
        self.ml_run_repo = ml_run_repo
        self.ml_pred_repo = ml_pred_repo
        self.ai_output_repo = ai_output_repo
        self.storage_base_dir = storage_base_dir

    def _faiss_dir(self, user_id: int, dataset_id: int) -> str:
        return os.path.join(
            self.storage_base_dir,
            str(user_id),
            str(dataset_id),
            "faiss_index"
        )

    def ask(
        self,
        dataset_id: int,
        user_id: int,
        question: str,
        session_id: Optional[int] = None
    ) -> Tuple[str, int]:
        """
        Full RAG pipeline.
        """
        # 1. Load FAISS index
        faiss_dir = self._faiss_dir(user_id, dataset_id)
        if not os.path.exists(faiss_dir):
            raise IndexNotFoundError(
                f"No FAISS index found for dataset {dataset_id}. "
                "Please run POST /datasets/{id}/index first."
            )
        vector_store = FaissVectorStore.load_index(
            embedding_client=self.embedding_client,
            persist_dir=faiss_dir
        )

        # 2. Create or validate session
        if session_id is None:
            session = self.chat_repo.create_session(
                user_id=user_id,
                dataset_id=dataset_id
            )
            session_id = session.id
        else:
            session = self.chat_repo.get_session(session_id)
            if session is None:
                raise SessionNotFoundError(f"ChatSession {session_id} not found.")
            if session.user_id != user_id:
                raise SessionOwnershipError(
                    f"ChatSession {session_id} does not belong to user {user_id}."
                )

        # 3. Retrieve top-5 relevant chunks
        results: List[Tuple[str, float]] = vector_store.search(
            query=question,
            embedding_client=self.embedding_client,
            top_k=5
        )
        context_chunks = [chunk for chunk, _score in results]
        context_text = "\n\n".join(context_chunks) if context_chunks else "No context available."

        # 4. Build grounded prompt
        prompt = RAG_PROMPT_TEMPLATE.format(
            context=context_text,
            question=question
        )

        # 5. Generate answer
        answer = self.llm_client.generate(prompt)

        # 6. Persist messages
        self.chat_repo.add_message(session_id, MessageRole.USER, question)
        self.chat_repo.add_message(session_id, MessageRole.ASSISTANT, answer)

        # 7. Return
        return answer, session_id

    def _build_kpis_context(self, dataset_id: int) -> str:
        if not self.kpi_repo:
            return "No KPI repository configured."
        kpis = self.kpi_repo.list_by_dataset_id(dataset_id)
        if not kpis:
            return "No computed KPIs available for this dataset."

        lines = []
        for k in kpis:
            lines.append(f"- KPI Type: {k.kpi_type}")
            lines.append(f"  Metrics: {json.dumps(k.value_json)}")
        return "\n".join(lines)

    def _build_ml_context(self, dataset_id: int) -> str:
        if not self.ml_run_repo or not self.ml_pred_repo:
            return "No ML repository configured."

        all_runs = self.ml_run_repo.list_by_dataset_id(dataset_id)
        if not all_runs:
            return "No machine learning runs available for this dataset."

        # Sort runs by created_at descending
        all_runs = sorted(all_runs, key=lambda r: r.created_at, reverse=True)

        lines = []
        # 1. Latest Forecast Run
        forecast_run = next((r for r in all_runs if r.model_type in ("prophet", "xgboost")), None)
        if forecast_run:
            preds = self.ml_pred_repo.list_by_run_id(forecast_run.id)
            preds = sorted(preds, key=lambda p: p.entity_ref)
            lines.append(f"- Latest Forecast Run (Model: {forecast_run.model_type})")
            lines.append(f"  Parameters: {forecast_run.params_json}")
            lines.append(f"  Metrics: {forecast_run.metrics_json}")
            if preds:
                trend_direction = "stable"
                if len(preds) > 1:
                    first = preds[0].prediction
                    last = preds[-1].prediction
                    if last > first * 1.05:
                        trend_direction = "growing / upward trend"
                    elif last < first * 0.95:
                        trend_direction = "declining / downward trend"
                # Summarize standard forecast points
                forecast_summary = [f"{p.entity_ref}: {p.prediction:.2f}" for p in preds[:10]]
                lines.append(f"  Forecast Trend: {trend_direction}")
                lines.append(f"  Forecast Predictions: {', '.join(forecast_summary)}")

        # 2. Latest Segmentation Run
        seg_run = next((r for r in all_runs if r.model_type == "kmeans_segmentation"), None)
        if seg_run:
            lines.append("- Latest Customer Segmentation Run (KMeans)")
            lines.append(f"  Metrics: {seg_run.metrics_json}")

        # 3. Latest Churn Run
        churn_run = next((r for r in all_runs if r.model_type == "xgboost_churn"), None)
        if churn_run:
            preds = self.ml_pred_repo.list_by_run_id(churn_run.id)
            # Sort by probability (prediction) desc to find top risk customers
            preds = sorted(preds, key=lambda p: p.prediction, reverse=True)
            lines.append("- Latest Customer Churn Run (XGBoost Churn)")
            lines.append(f"  Metrics: {churn_run.metrics_json}")
            top_churners = [f"Customer {p.entity_ref} (Risk: {p.prediction * 100:.1f}%)" for p in preds[:5]]
            lines.append(f"  Top Churn-Risk Customers: {', '.join(top_churners) if top_churners else 'None'}")

        # 4. Latest Anomaly Run
        anomaly_run = next((r for r in all_runs if r.model_type == "isolation_forest"), None)
        if anomaly_run:
            preds = self.ml_pred_repo.list_by_run_id(anomaly_run.id)
            lines.append("- Latest Anomaly Detection Run (Isolation Forest)")
            lines.append(f"  Metrics: {anomaly_run.metrics_json}")
            anomaly_details = [
                f"Row {p.entity_ref}: Score {p.prediction:.3f} (Amount: {p.shap_values_json.get('features', {}).get('amount') if p.shap_values_json else 'N/A'})"
                for p in preds[:5]
            ]
            lines.append(f"  Flagged Anomalies Sample: {', '.join(anomaly_details) if anomaly_details else 'None'}")

        return "\n".join(lines)

    def generate_recommendations(self, dataset_id: int, regenerate: bool = False) -> List[str]:
        """
        Generates 3-5 concrete business recommendations based on KPIs and latest ML metrics.
        Grounded directly in actual values to ensure accuracy.
        Caches outputs in db to prevent duplicate external invocations.
        """
        if not regenerate and self.ai_output_repo:
            cached = self.ai_output_repo.get_latest_by_dataset_and_type(dataset_id, "recommendations")
            if cached:
                return cached.content_json.get("recommendations", [])

        kpis_context = self._build_kpis_context(dataset_id)
        ml_context = self._build_ml_context(dataset_id)

        prompt = RECOMMENDATIONS_PROMPT_TEMPLATE.format(
            kpis_context=kpis_context,
            ml_context=ml_context
        )

        res = self.llm_client.generate(prompt)

        # Parse numbered list from response
        lines = res.strip().split("\n")
        recommendations = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            cleaned = re.sub(r'^\d+[\s\.\)-]+', '', line).strip()
            if cleaned:
                recommendations.append(cleaned)

        if not recommendations:
            recommendations = ["Ggrounded recommendations could not be structured from model output."]

        # Cache results in DB
        if self.ai_output_repo:
            new_output = AiOutput(
                id=None,
                dataset_id=dataset_id,
                output_type="recommendations",
                content_json={"recommendations": recommendations},
                generated_at=datetime.now(timezone.utc)
            )
            self.ai_output_repo.create(new_output)

        return recommendations

    def generate_executive_summary(self, dataset_id: int, regenerate: bool = False) -> str:
        """
        Generates a 150-250 word business performance executive summary narrative.
        Grounded directly in computed metrics to assure factual accuracy.
        Caches outputs in db to avoid duplicate external invoices.
        """
        if not regenerate and self.ai_output_repo:
            cached = self.ai_output_repo.get_latest_by_dataset_and_type(dataset_id, "summary")
            if cached:
                return cached.content_json.get("summary", "")

        kpis_context = self._build_kpis_context(dataset_id)
        ml_context = self._build_ml_context(dataset_id)

        prompt = EXECUTIVE_SUMMARY_PROMPT_TEMPLATE.format(
            kpis_context=kpis_context,
            ml_context=ml_context
        )

        summary = self.llm_client.generate(prompt).strip()

        # Cache results in DB
        if self.ai_output_repo:
            new_output = AiOutput(
                id=None,
                dataset_id=dataset_id,
                output_type="summary",
                content_json={"summary": summary},
                generated_at=datetime.now(timezone.utc)
            )
            self.ai_output_repo.create(new_output)

        return summary

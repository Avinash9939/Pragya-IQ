from datetime import datetime, timezone
import pytest
from app.domain.entities.kpi_result import KpiResult
from app.domain.entities.ml import MlRun, MlPrediction
from app.domain.entities.ai_output import AiOutput
from app.domain.interfaces.kpi_result_repository import KpiResultRepositoryInterface
from app.domain.interfaces.ml_repository import MlRunRepositoryInterface, MlPredictionRepositoryInterface
from app.domain.interfaces.ai_output_repository import AiOutputRepositoryInterface
from app.services.ai_service import AIService
from app.infrastructure.llm.gemini_client import FakeLLMClient


class InMemoryKpiRepository(KpiResultRepositoryInterface):
    def __init__(self):
        self.kpis = []

    def create(self, result: KpiResult) -> KpiResult:
        if result.id is None:
            result.id = len(self.kpis) + 1
        self.kpis.append(result)
        return result

    def get_by_dataset_id_and_type(self, dataset_id: int, kpi_type: str):
        return next((k for k in self.kpis if k.dataset_id == dataset_id and k.kpi_type == kpi_type), None)

    def list_by_dataset_id(self, dataset_id: int):
        return [k for k in self.kpis if k.dataset_id == dataset_id]


class InMemoryMlRunRepository(MlRunRepositoryInterface):
    def __init__(self):
        self.runs = []

    def create(self, run: MlRun) -> MlRun:
        if run.id is None:
            run.id = len(self.runs) + 1
        self.runs.append(run)
        return run

    def get_by_id(self, run_id: int):
        return next((r for r in self.runs if r.id == run_id), None)

    def list_by_dataset_id(self, dataset_id: int):
        return [r for r in self.runs if r.dataset_id == dataset_id]


class InMemoryMlPredictionRepository(MlPredictionRepositoryInterface):
    def __init__(self):
        self.preds = []

    def create_batch(self, predictions):
        for idx, p in enumerate(predictions):
            if p.id is None:
                p.id = len(self.preds) + 1
            self.preds.append(p)
        return predictions

    def list_by_run_id(self, ml_run_id: int):
        return [p for p in self.preds if p.ml_run_id == ml_run_id]


class InMemoryAiOutputRepository(AiOutputRepositoryInterface):
    def __init__(self):
        self.outputs = []

    def create(self, ai_output: AiOutput) -> AiOutput:
        # Upsert logic: remove existing match to handle updates correctly
        existing_idx = next(
            (i for i, o in enumerate(self.outputs)
             if o.dataset_id == ai_output.dataset_id and o.output_type == ai_output.output_type),
            None
        )
        if existing_idx is not None:
            self.outputs[existing_idx] = ai_output
            return ai_output

        if ai_output.id is None:
            ai_output.id = len(self.outputs) + 1
        self.outputs.append(ai_output)
        return ai_output

    def get_latest_by_dataset_and_type(self, dataset_id: int, output_type: str):
        matches = [o for o in self.outputs if o.dataset_id == dataset_id and o.output_type == output_type]
        if not matches:
            return None
        # Sort descending by generated_at
        matches = sorted(matches, key=lambda x: x.generated_at, reverse=True)
        return matches[0]


def test_recommendations_and_summary_grounding():
    kpi_repo = InMemoryKpiRepository()
    kpi_repo.create(KpiResult(id=None, dataset_id=1, kpi_type="sales", value_json={"total_revenue": 950000.0, "revenue_growth_percent": 14.5}, computed_at=datetime.now(timezone.utc)))
    kpi_repo.create(KpiResult(id=None, dataset_id=1, kpi_type="customer", value_json={"total_unique_customers": 1250, "customer_lifetime_value_estimate": 760.0}, computed_at=datetime.now(timezone.utc)))

    ml_run_repo = InMemoryMlRunRepository()
    ml_pred_repo = InMemoryMlPredictionRepository()
    
    # 1. Create a forecast run
    run = ml_run_repo.create(MlRun(id=None, dataset_id=1, model_type="xgboost", params_json={"horizon_days": 7}, metrics_json={"rmse": 12.3}, created_at=datetime.now(timezone.utc)))
    ml_pred_repo.create_batch([
        MlPrediction(id=None, ml_run_id=run.id, entity_ref="2026-07-12", prediction=5000.0, shap_values_json={}),
        MlPrediction(id=None, ml_run_id=run.id, entity_ref="2026-07-13", prediction=5800.0, shap_values_json={})
    ])

    # 2. Create a churn run
    churn_run = ml_run_repo.create(MlRun(id=None, dataset_id=1, model_type="xgboost_churn", params_json={}, metrics_json={}, created_at=datetime.now(timezone.utc)))
    ml_pred_repo.create_batch([
        MlPrediction(id=None, ml_run_id=churn_run.id, entity_ref="Cust101", prediction=0.87, shap_values_json={})
    ])

    ai_output_repo = InMemoryAiOutputRepository()
    llm_client = FakeLLMClient()
    # Mock LLM to return specific text to verify parsing
    llm_client.generate = lambda prompt: (
        "1. Focus on Cust101 who has an 87% churn risk.\n"
        "2. Leverage the growing xgboost forecast from 5000 to 5800.\n"
        "3. Total revenue of 950000 is outstanding."
    ) if "recommendations" in prompt.lower() else "This is an executive summary highlighting 950000 revenue with 1250 unique customers."

    service = AIService(
        embedding_client=None,
        llm_client=llm_client,
        chat_repo=None,
        kpi_repo=kpi_repo,
        ml_run_repo=ml_run_repo,
        ml_pred_repo=ml_pred_repo,
        ai_output_repo=ai_output_repo
    )

    recs = service.generate_recommendations(dataset_id=1)
    assert len(recs) == 3
    assert "Cust101" in recs[0]
    assert "87%" in recs[0]
    assert "5000" in recs[1]
    assert "950000" in recs[2]

    summary = service.generate_executive_summary(dataset_id=1)
    assert "950000" in summary
    assert "1250" in summary


def test_caching_and_regeneration():
    kpi_repo = InMemoryKpiRepository()
    ml_run_repo = InMemoryMlRunRepository()
    ml_pred_repo = InMemoryMlPredictionRepository()
    ai_output_repo = InMemoryAiOutputRepository()
    llm_client = FakeLLMClient()
    
    service = AIService(
        embedding_client=None,
        llm_client=llm_client,
        chat_repo=None,
        kpi_repo=kpi_repo,
        ml_run_repo=ml_run_repo,
        ml_pred_repo=ml_pred_repo,
        ai_output_repo=ai_output_repo
    )

    # Track calls to generate
    call_count = 0
    
    def fake_generate(prompt):
        nonlocal call_count
        call_count += 1
        if "recommendations" in prompt.lower():
            return f"1. Recommendation {call_count}\n2. Grounded metrics"
        return f"Summary version {call_count}"

    llm_client.generate = fake_generate

    # 1. Call Recommendations first time (cache miss)
    recs1 = service.generate_recommendations(dataset_id=1)
    assert recs1 == ["Recommendation 1", "Grounded metrics"]
    assert call_count == 1

    # 2. Call Recommendations second time with regenerate=False (cache hit)
    recs2 = service.generate_recommendations(dataset_id=1, regenerate=False)
    assert recs2 == ["Recommendation 1", "Grounded metrics"]
    assert call_count == 1  # Should not increase!

    # 3. Call Recommendations with regenerate=True (cache bypass & update)
    recs3 = service.generate_recommendations(dataset_id=1, regenerate=True)
    assert recs3 == ["Recommendation 2", "Grounded metrics"]
    assert call_count == 2  # Increases!

    # 4. Call Executive Summary first time (cache miss)
    sum1 = service.generate_executive_summary(dataset_id=1)
    assert sum1 == "Summary version 3"
    assert call_count == 3

    # 5. Call Executive Summary second time with regenerate=False (cache hit)
    sum2 = service.generate_executive_summary(dataset_id=1, regenerate=False)
    assert sum2 == "Summary version 3"
    assert call_count == 3  # Should not increase!

    # 6. Call Executive Summary with regenerate=True (cache bypass & update)
    sum3 = service.generate_executive_summary(dataset_id=1, regenerate=True)
    assert sum3 == "Summary version 4"
    assert call_count == 4  # Increases!

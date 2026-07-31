from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any


@dataclass
class AiOutput:
    """
    Domain entity representing generated business recommendations or executive summaries.
    Why: Caches costly/large LLM text output and ties it directly to the dataset source.
    """
    id: Optional[int]
    dataset_id: int
    output_type: str  # "recommendations" or "summary"
    content_json: Any
    generated_at: datetime

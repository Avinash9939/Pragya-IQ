import os
import requests
import streamlit as st
from dotenv import load_dotenv

# Load env variables at configuration boundaries
load_dotenv()

BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")


class ApiError(Exception):
    """
    Custom exception representing API backend failure states.
    Why: Carries backend status codes and messages to render helpful frontend toasts or alerts.
    """
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _request(method: str, path: str, **kwargs) -> requests.Response:
    """
    Low level requests wrapper performing HTTP calls, injecting cookies/tokens,
    handling client timeouts, and mapping standard error shapes.
    Why: Centrally enforces API contract conventions.
    """
    # Enforce request timeout default broadly to allow for slow environment processing
    kwargs.setdefault("timeout", 60.0)

    # Inject Authorization header if JWT token is stored in the active session state
    headers = kwargs.get("headers", {})
    if "access_token" in st.session_state:
        headers["Authorization"] = f"Bearer {st.session_state['access_token']}"
    kwargs["headers"] = headers

    # Construct absolute target URL
    clean_path = path.lstrip("/")
    url = f"{BACKEND_API_URL.rstrip('/')}/api/v1/{clean_path}"

    try:
        response = requests.request(method, url, **kwargs)

        # Parse success pathways
        if 200 <= response.status_code < 300:
            return response

        # Extract message description from API details standard format
        detail_msg = f"HTTP Error {response.status_code}"
        try:
            body = response.json()
            if isinstance(body, dict) and "detail" in body:
                detail_msg = body["detail"]
        except Exception:
            pass

        # Handle specific authorization scopes errors
        if response.status_code == 401:
            raise ApiError("Session expired, please log in again", 401)
        elif response.status_code == 403:
            raise ApiError("You don't have permission for this action", 403)
        elif response.status_code == 404:
            raise ApiError(detail_msg if detail_msg != f"HTTP Error 404" else "Resource not found", 404)
        else:
            raise ApiError(detail_msg, response.status_code)

    except requests.exceptions.RequestException as e:
        raise ApiError(f"Network connectivity error: {str(e)}", None)


def register(email: str, password: str, role: str) -> dict:
    """
    Registers a new user account.
    Why: Form submission target for /auth/register.
    """
    payload = {"email": email, "password": password, "role": role}
    response = _request("POST", "auth/register", json=payload)
    return response.json()


def login(email: str, password: str) -> str:
    """
    Authenticates user credentials and sets state.
    Why: Automatically caches token in active UI session.
    """
    payload = {"username": email, "password": password}
    response = _request("POST", "auth/login", data=payload)
    data = response.json()
    token = data["access_token"]
    
    # Store token in session state
    st.session_state["access_token"] = token
    
    # Pre-fetch user details for faster UI checks
    try:
        user_profile = get_my_profile()
        st.session_state["user"] = user_profile
    except Exception:
        # If user retrieval fails, clear token to prevent partial auth state representation
        st.session_state.pop("access_token", None)
        raise

    return token


def get_my_profile() -> dict:
    """
    Queries current authenticated user details.
    Why: Extracts identity definitions to handle RBAC guards.
    """
    response = _request("GET", "users/me")
    return response.json()


def list_datasets(force_refresh: bool = False) -> list:
    """
    Returns array of metadata for datasets belonging to active user.
    """
    if "api_cached_datasets" in st.session_state and not force_refresh:
        return st.session_state["api_cached_datasets"]
        
    response = _request("GET", "datasets/")
    data = response.json()
    st.session_state["api_cached_datasets"] = data
    return data


def upload_dataset(file) -> dict:
    """
    Uploads a multipart dataset file to the backend service.
    Why: Facilitates file sharing pipeline.
    """
    # Build standard multipart files mapping payload
    files = {"file": (file.name, file.getvalue(), file.type)}
    response = _request("POST", "datasets/upload", files=files, timeout=300.0)
    return response.json()


def delete_dataset(dataset_id: int) -> dict:
    """
    Submits a deletion request for the target dataset.
    Why: Clears cache mappings and filesystem holdings.
    """
    response = _request("DELETE", f"datasets/{dataset_id}")
    return response.json()


def get_dataset(dataset_id: int, force_refresh: bool = False) -> dict:
    """
    Queries full detail definition of a single dataset.
    Why: Checks individual status, mappings, or fields.
    """
    cache_key = f"cached_dataset_{dataset_id}"
    if cache_key in st.session_state and not force_refresh:
        return st.session_state[cache_key]
        
    response = _request("GET", f"datasets/{dataset_id}")
    data = response.json()
    st.session_state[cache_key] = data
    return data


def download_dataset_file(dataset_id: int, file_type: str = "raw") -> bytes:
    """
    Downloads the physical dataset file via API.
    file_type: 'raw', 'cleaned', or 'features'
    """
    params = {"file_type": file_type}
    response = _request("GET", f"datasets/{dataset_id}/download", params=params, timeout=120.0)
    return response.content



def clean_dataset(dataset_id: int) -> dict:
    """
    Triggers automated cleaning processes on the target dataset.
    Why: Resolves duplicates, missing attributes, and outliers.
    """
    st.session_state.pop(f"cached_dataset_{dataset_id}", None)
    st.session_state.pop("api_cached_datasets", None)
    response = _request("POST", f"datasets/{dataset_id}/clean")
    return response.json()


def engineer_features(dataset_id: int) -> dict:
    """
    Runs feature engineering calculations on the cleaned dataset.
    Why: Generates scaling values, categories encoding.
    """
    st.session_state.pop(f"cached_dataset_{dataset_id}", None)
    st.session_state.pop("api_cached_datasets", None)
    response = _request("POST", f"datasets/{dataset_id}/engineer-features")
    return response.json()


def update_column_mapping(dataset_id: int, mapping: dict) -> dict:
    """
    Updates the semantic column mapping configuration for matching features.
    Why: Binds dataset columns to semantic variables like product, price, etc.
    """
    st.session_state.pop(f"cached_dataset_{dataset_id}", None)
    st.session_state.pop("api_cached_datasets", None)
    payload = {"mapping": mapping}
    response = _request("PUT", f"datasets/{dataset_id}/mapping", json=payload)
    return response.json()


def get_sales_kpis(dataset_id: int) -> dict:
    """
    Retrieves sales KPI computations such as revenue, growth, and top products.
    """
    response = _request("GET", f"kpi/{dataset_id}/sales")
    return response.json()


def get_customer_kpis(dataset_id: int) -> dict:
    """
    Retrieves customer KPI metrics (customer counts, returning rates, CLV).
    """
    response = _request("GET", f"kpi/{dataset_id}/customer")
    return response.json()


def get_product_kpis(dataset_id: int) -> dict:
    """
    Retrieves product metrics (best and worst sellers).
    """
    response = _request("GET", f"kpi/{dataset_id}/product")
    return response.json()


def get_regional_kpis(dataset_id: int) -> dict:
    """
    Retrieves regional boundaries performance metrics.
    """
    response = _request("GET", f"kpi/{dataset_id}/region")
    return response.json()


def run_forecast(dataset_id: int, horizon_days: int, model_type: str, cross_val: bool = True) -> dict:
    """
    Triggers demand forecasting with Prophet, XGBoost, or both.
    """
    payload = {"horizon_days": horizon_days, "model_type": model_type, "cross_val": cross_val}
    response = _request("POST", f"ml/{dataset_id}/forecast", json=payload)
    return response.json()


def run_segmentation(dataset_id: int, n_clusters: int = 4) -> dict:
    """
    Triggers KMeans customer segmentation over a dataset.
    """
    payload = {"n_clusters": n_clusters}
    response = _request("POST", f"ml/{dataset_id}/segment", json=payload)
    return response.json()


def run_churn_prediction(dataset_id: int, recency_threshold_days: int = None) -> dict:
    """
    Triggers XGBoost churn prediction over a dataset.
    """
    payload = {}
    if recency_threshold_days is not None:
        payload["recency_threshold_days"] = recency_threshold_days
    response = _request("POST", f"ml/{dataset_id}/churn", json=payload)
    return response.json()


def run_anomaly_detection(dataset_id: int, contamination: float = 0.05) -> dict:
    """
    Triggers IsolationForest anomaly detection over a dataset.
    """
    payload = {"contamination": contamination}
    response = _request("POST", f"ml/{dataset_id}/anomaly", json=payload)
    return response.json()


def get_shap_explanation(ml_run_id: int, entity_ref: str) -> dict:
    """
    Retrieves SHAP explainability values for a specific prediction entity.
    """
    response = _request("GET", f"ml/{ml_run_id}/shap/{entity_ref}")
    return response.json()


def index_dataset(dataset_id: int) -> dict:
    """
    Triggers FAISS vector indexing of a dataset's KPIs, ML outputs, and raw samples.
    Why: Required before RAG chat queries can retrieve relevant context.
    """
    response = _request("POST", f"datasets/{dataset_id}/index")
    return response.json()


def send_chat_message(dataset_id: int, question: str, session_id: int = None) -> dict:
    """
    Sends a natural-language question to the RAG chat pipeline.
    Returns {answer, session_id}.
    """
    payload = {"question": question}
    if session_id is not None:
        payload["session_id"] = session_id
    response = _request("POST", f"ai/{dataset_id}/chat", json=payload)
    return response.json()


def get_chat_history(dataset_id: int, session_id: int) -> list:
    """
    Retrieves the full message history for a chat session.
    """
    response = _request("GET", f"ai/{dataset_id}/chat/{session_id}/history")
    return response.json()


def get_recommendations(dataset_id: int, regenerate: bool = False) -> dict:
    """
    Retrieves 3-5 grounded business recommendations for the dataset.
    When regenerate=True, calls the AI model again (a few seconds);
    otherwise returns the cached result instantly.
    Returns: {"dataset_id": int, "recommendations": [str, ...], "generated_at": str}
    """
    params = {"regenerate": str(regenerate).lower()}
    response = _request("GET", f"ai/{dataset_id}/recommendations", params=params)
    return response.json()


def get_executive_summary(dataset_id: int, regenerate: bool = False) -> dict:
    """
    Retrieves a grounded plain-English executive summary (150-250 words) for the dataset.
    When regenerate=True, calls the AI model again (a few seconds);
    otherwise returns the cached result instantly.
    Returns: {"dataset_id": int, "summary": str, "generated_at": str}
    """
    params = {"regenerate": str(regenerate).lower()}
    response = _request("GET", f"ai/{dataset_id}/executive-summary", params=params)
    return response.json()


def generate_report(dataset_id: int) -> dict:
    """
    Triggers PDF report generation for the dataset (KPI tables + AI summary + recommendations).
    Uses a 60s timeout — PDF rendering can take several seconds.
    Returns: {"id": int, "dataset_id": int, "file_path": str, "generated_at": str}
    """
    response = _request("POST", f"reports/{dataset_id}/generate", timeout=60.0)
    return response.json()


def download_report(report_id: int) -> bytes:
    """
    Downloads the generated PDF report as raw bytes.
    Uses a 60s timeout to accommodate large file transfers.
    Returns raw PDF bytes suitable for st.download_button(data=...).
    """
    response = _request("GET", f"reports/{report_id}/download", timeout=60.0)
    return response.content


def get_logs(limit: int = 20, offset: int = 0) -> list:
    """
    Retrieves paginated system activity audit logs. Admin-only.
    Returns a list of log dicts: {id, user_id, action, resource, created_at}.
    """
    params = {"limit": limit, "offset": offset}
    response = _request("GET", "logs", params=params)
    return response.json()


def get_settings() -> dict:
    """
    Retrieves current system settings (e.g. maintenance_mode).
    Returns: {"maintenance_mode": bool}
    """
    response = _request("GET", "settings")
    return response.json()


def update_settings(settings_dict: dict) -> dict:
    """
    Updates system settings. Admin-only.
    Accepts keys: maintenance_mode (bool).
    Returns updated settings dict: {"maintenance_mode": bool}
    """
    response = _request("PUT", "settings", json=settings_dict)
    return response.json()


def generate_business_explanation(dataset_id: int, prompt: str) -> dict:
    """
    Retrieves dynamically generated business explanations using AI.
    Returns: {"explanation": str}
    """
    payload = {"prompt": prompt}
    response = _request("POST", f"ai/{dataset_id}/performance-intelligence/explain", json=payload)
    return response.json()

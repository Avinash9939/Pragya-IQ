import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

def run_kmeans_segmentation(rfm_df: pd.DataFrame, n_clusters: int = 4) -> tuple[pd.DataFrame, float]:
    """
    Fits KMeans clustering over standardized customer RFM metrics.
    Why: Unsupervised categorization of customers based on spending patterns.
    """
    # Ensure there are enough records to form n_clusters
    actual_clusters = min(n_clusters, len(rfm_df))
    if actual_clusters <= 0:
        actual_clusters = 1

    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(rfm_df[['Recency', 'Frequency', 'Monetary']])

    kmeans = KMeans(n_clusters=actual_clusters, random_state=42, n_init=10)
    kmeans.fit(scaled_features)

    out_df = rfm_df.copy()
    out_df['cluster'] = kmeans.labels_.astype(int)

    inertia = float(kmeans.inertia_)
    return out_df, inertia

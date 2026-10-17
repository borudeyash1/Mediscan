"""
Spatio-Temporal Outbreak Detection Engine.
Performs geospatial clustering over reported communicable diseases
(Dengue, Influenza, Malaria, COVID-19) to detect epidemic surges and calculate Rt.
"""

import math
from datetime import datetime, timezone
from typing import Any, Optional
import numpy as np

from .models import OutbreakSeverity, DiseaseOutbreakCluster


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on Earth in km."""
    r = 6371.0  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def lat_lon_to_geohash_approx(lat: float, lon: float) -> str:
    """Generate coarse 6-character geohash approximation."""
    base32 = "0123456789bcdefghjkmnpqrstuvwxyz"
    lat_idx = int((lat + 90.0) / 180.0 * 32.0 * 32.0)
    lon_idx = int((lon + 180.0) / 360.0 * 32.0 * 32.0)
    return f"{base32[lat_idx % 32]}{base32[lon_idx % 32]}{base32[(lat_idx // 32) % 32]}{base32[(lon_idx // 32) % 32]}gh"


class SpatioTemporalOutbreakDetector:
    """Clustering engine detecting regional disease clusters and computing reproduction rate Rt."""

    def __init__(self, cluster_radius_km: float = 15.0):
        self.cluster_radius_km = cluster_radius_km
        # In-memory registry of reported incident cases
        self._reported_cases: list[dict[str, Any]] = [
            # Pre-seeded Dengue surge in metro region (Mumbai / Pune / Western Ghats corridor)
            {"id": "case_01", "pathogen": "Dengue", "lat": 18.5204, "lon": 73.8567, "days_ago": 1},
            {"id": "case_02", "pathogen": "Dengue", "lat": 18.5310, "lon": 73.8440, "days_ago": 1},
            {"id": "case_03", "pathogen": "Dengue", "lat": 18.5100, "lon": 73.8600, "days_ago": 2},
            {"id": "case_04", "pathogen": "Dengue", "lat": 18.5400, "lon": 73.8300, "days_ago": 2},
            {"id": "case_05", "pathogen": "Dengue", "lat": 18.5250, "lon": 73.8500, "days_ago": 3},
            {"id": "case_06", "pathogen": "Dengue", "lat": 18.5150, "lon": 73.8700, "days_ago": 3},
            # Pre-seeded Influenza cluster
            {"id": "case_10", "pathogen": "Influenza A (H1N1)", "lat": 28.6139, "lon": 77.2090, "days_ago": 1},
            {"id": "case_11", "pathogen": "Influenza A (H1N1)", "lat": 28.6200, "lon": 77.2150, "days_ago": 2},
            {"id": "case_12", "pathogen": "Influenza A (H1N1)", "lat": 28.6050, "lon": 77.2000, "days_ago": 2},
            {"id": "case_13", "pathogen": "Influenza A (H1N1)", "lat": 28.6300, "lon": 77.2200, "days_ago": 3},
        ]

    def add_case(self, pathogen: str, latitude: float, longitude: float) -> None:
        """Register a new verified infection report."""
        self._reported_cases.append({
            "id": f"case_{len(self._reported_cases)+1:03d}",
            "pathogen": pathogen,
            "lat": latitude,
            "lon": longitude,
            "days_ago": 0,
        })

    def detect_outbreak_clusters(
        self, pathogen_filter: Optional[str] = None
    ) -> list[DiseaseOutbreakCluster]:
        """
        Runs geospatial clustering algorithm across active reported cases.
        Groups nearby cases within radius and calculates reproduction number Rt.
        """
        cases_to_cluster = self._reported_cases
        if pathogen_filter:
            cases_to_cluster = [c for c in cases_to_cluster if pathogen_filter.lower() in c["pathogen"].lower()]

        if not cases_to_cluster:
            return []

        # Partition cases by pathogen
        by_pathogen: dict[str, list[dict[str, Any]]] = {}
        for c in cases_to_cluster:
            by_pathogen.setdefault(c["pathogen"], []).append(c)

        clusters: list[DiseaseOutbreakCluster] = []

        for path, p_cases in by_pathogen.items():
            visited: set[int] = set()

            for i, base_case in enumerate(p_cases):
                if i in visited:
                    continue

                cluster_cases = [base_case]
                visited.add(i)

                for j, target_case in enumerate(p_cases):
                    if j not in visited:
                        dist = haversine_distance_km(
                            base_case["lat"], base_case["lon"], target_case["lat"], target_case["lon"]
                        )
                        if dist <= self.cluster_radius_km:
                            cluster_cases.append(target_case)
                            visited.add(j)

                case_count = len(cluster_cases)
                if case_count >= 2:
                    # Centroid
                    mean_lat = float(np.mean([c["lat"] for c in cluster_cases]))
                    mean_lon = float(np.mean([c["lon"] for c in cluster_cases]))

                    # Estimate Rt based on recent acceleration
                    recent_cases = sum(1 for c in cluster_cases if c["days_ago"] <= 1)
                    older_cases = max(1, sum(1 for c in cluster_cases if c["days_ago"] > 1))
                    rt = round(max(0.8, min(3.2, float(recent_cases) / float(older_cases) * 1.6)), 2)
                    growth_rate = round((rt - 1.0) * 100.0, 1)

                    if case_count >= 5 or rt >= 1.4:
                        severity = OutbreakSeverity.EMERGENT_OUTBREAK
                        actions = [
                            f"Deploy rapid municipal vector-control fogging & source reduction teams for {path}",
                            "Establish dedicated fever triage clinics at primary healthcare centers",
                            "Issue clinician alerts restricting contraindicated NSAID prescribing",
                            "Stockplatelet concentrate supplies at regional tertiary blood banks",
                        ]
                    elif case_count >= 3:
                        severity = OutbreakSeverity.ELEVATED_SURGE
                        actions = [
                            f"Heighten syndromic surveillance for {path} across outpatient networks",
                            "Deploy community awareness advisory and rapid diagnostic testing kits",
                        ]
                    else:
                        severity = OutbreakSeverity.WATCHLIST
                        actions = ["Routine epidemiological monitoring."]

                    clusters.append(
                        DiseaseOutbreakCluster(
                            pathogen=path,
                            latitude=round(mean_lat, 4),
                            longitude=round(mean_lon, 4),
                            radius_km=self.cluster_radius_km,
                            case_count=case_count,
                            reproduction_rate_rt=rt,
                            growth_rate_percent=growth_rate,
                            severity=severity,
                            affected_geohash=lat_lon_to_geohash_approx(mean_lat, mean_lon),
                            recommended_public_health_actions=actions,
                        )
                    )

        # Sort by case count descending
        clusters.sort(key=lambda x: x.case_count, reverse=True)
        return clusters


outbreak_detector = SpatioTemporalOutbreakDetector()

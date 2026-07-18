#!python
"""
Behavioral Analytics and Anomaly Detection
Implements ML-based anomaly detection for security monitoring
"""

import time
import math
import statistics
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import hashlib
import structlog

from utils.redis_client import redis_client
from utils.ip_utils import get_request_ip

logger = structlog.get_logger(__name__)


@dataclass
class BehaviorProfile:
    """User behavior profile."""
    user_id: int
    avg_request_interval: float = 0.0
    avg_session_duration: float = 0.0
    typical_request_count: int = 0
    typical_active_hours: List[int] = field(default_factory=list)
    typical_ips: List[str] = field(default_factory=list)
    risk_score: float = 0.0
    last_updated: datetime = field(default_factory=datetime.utcnow)


class AnomalyDetector:
    """
    Anomaly detection using statistical methods.
    No external ML dependencies - pure Python implementation.
    """

    def __init__(self):
        self.redis = redis_client()
        self.window_size = 100
        self.threshold_multiplier = 2.5

    def detect_anomaly(
        self,
        user_id: int,
        metric: str,
        value: float,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, float, str]:
        """
        Detect anomaly in metric for user.
        Returns: (is_anomaly, score, reason)
        """
        if not self.redis:
            return False, 0.0, ""

        try:
            key = f"behavior:{user_id}:{metric}:history"
            history = self._get_history(key)

            if len(history) < 10:
                self._add_to_history(key, value)
                return False, 0.0, ""

            z_score = self._calculate_z_score(value, history)
            is_anomaly = abs(z_score) > self.threshold_multiplier

            if is_anomaly:
                reason = f"Anomaly detected: {metric}={value}, z_score={z_score:.2f}"
                self._update_risk_score(user_id, metric, value, context)
                return True, abs(z_score), reason

            self._add_to_history(key, value)
            return False, 0.0, ""

        except Exception as e:
            return False, 0.0, ""

    def _get_history(self, key: str) -> List[float]:
        """Get history from Redis."""
        if not self.redis:
            return []

        try:
            history = self.redis.lrange(key, 0, -1)
            return [float(h) for h in history]
        except Exception:
            return []

    def _add_to_history(self, key: str, value: float):
        """Add value to history in Redis."""
        if not self.redis:
            return

        try:
            self.redis.lpush(key, value)
            self.redis.ltrim(key, 0, self.window_size - 1)
        except Exception as e:
            logger.warning(f"Risk score update failed: {e}")
            pass

    def _calculate_z_score(self, value: float, history: List[float]) -> float:
        """Calculate Z-score for value against history."""
        if len(history) < 2:
            return 0.0

        mean = statistics.mean(history)
        stdev = statistics.stdev(history)

        if stdev == 0:
            return 0.0

        return (value - mean) / stdev

    def _update_risk_score(
        self,
        user_id: int,
        metric: str,
        value: float,
        context: Optional[Dict[str, Any]],
    ):
        """Update user risk score."""
        if not self.redis:
            return

        try:
            risk_key = f"risk:{user_id}"
            current_score = float(self.redis.get(risk_key) or 0)
            new_score = min(1.0, current_score + 0.1)
            self.redis.setex(risk_key, 3600, new_score)
        except Exception as e:
            logger.warning(f"Risk score update failed: {e}")
            pass


class BehavioralAnalyzer:
    """
    Analyzes user behavior patterns for anomaly detection.
    """

    def __init__(self, app=None):
        self.app = app
        self.redis = redis_client()
        self.anomaly_detector = AnomalyDetector()

    async def __call__(self, scope, receive, send):
        """ASGI middleware interface."""
        if scope["type"] != "http":
            if self.app:
                await self.app(scope, receive, send)
            return
        if self.app:
            await self.app(scope, receive, send)
        else:
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b""})

    def analyze_request(
        self,
        user_id: Optional[int],
        request,
        response,
    ) -> Dict[str, Any]:
        """Analyze request for behavioral anomalies."""
        if not user_id:
            return {}

        client_ip = get_request_ip(request)
        path = request.url.path
        method = request.method
        timestamp = time.time()

        anomalies = []
        risk_factors = []

        interval_anomaly, interval_score, interval_reason = self.anomaly_detector.detect_anomaly(
            user_id, "request_interval", timestamp
        )
        if interval_anomaly:
            anomalies.append(interval_reason)
            risk_factors.append("rapid_requests")

        path_anomaly, path_score, path_reason = self.anomaly_detector.detect_anomaly(
            user_id, "path_access", hash(path) % 1000
        )
        if path_anomaly:
            anomalies.append(path_reason)
            risk_factors.append("unusual_path_access")

        ip_anomaly, ip_score, ip_reason = self.anomaly_detector.detect_anomaly(
            user_id, "ip_change", hash(client_ip) % 1000
        )
        if ip_anomaly:
            anomalies.append(ip_reason)
            risk_factors.append("ip_change")

        is_suspicious = len(anomalies) > 0
        risk_score = max(interval_score, path_score, ip_score) if anomalies else 0.0

        return {
            "is_suspicious": is_suspicious,
            "anomalies": anomalies,
            "risk_factors": risk_factors,
            "risk_score": risk_score,
        }

    def update_profile(self, user_id: int, analysis: Dict[str, Any]):
        """Update user behavior profile."""
        if not self.redis:
            return

        try:
            profile_key = f"profile:{user_id}"
            self.redis.hset(profile_key, "last_risk_score", analysis.get("risk_score", 0))
            self.redis.hset(profile_key, "last_analysis", str(analysis))
            self.redis.expire(profile_key, 86400)
        except Exception as e:
            logger.warning(f"Risk score update failed: {e}")
            pass


class ImpossibleTravelDetector:
    """
    Detects impossible travel patterns.
    """

    EARTH_RADIUS_KM = 6371.0
    MAX_SPEED_KMH = 1200
    MAX_DISTANCE_KM = 20000

    def __init__(self):
        self.redis = redis_client()

    def check_travel(
        self,
        user_id: int,
        lat: float,
        lon: float,
        timestamp: Optional[float] = None,
    ) -> Tuple[bool, str]:
        """
        Check if travel is physically possible.
        Returns: (is_impossible, reason)
        """
        if not self.redis:
            return False, ""

        try:
            key = f"location:{user_id}:last"
            last_location = self.redis.hgetall(key)

            if not last_location:
                self._store_location(key, lat, lon, timestamp or time.time())
                return False, ""

            last_lat = float(last_location.get("lat", 0))
            last_lon = float(last_location.get("lon", 0))
            last_ts = float(last_location.get("timestamp", 0))

            distance = self._calculate_distance(last_lat, last_lon, lat, lon)
            time_diff = (timestamp or time.time()) - last_ts
            speed = (distance / time_diff) * 3600 if time_diff > 0 else 0

            if speed > self.MAX_SPEED_KMH:
                return True, f"Impossible travel: {speed:.0f} km/h exceeds limit"

            self._store_location(key, lat, lon, timestamp or time.time())
            return False, ""

        except Exception as e:
            logger.warning(f"Anomaly detection failed: {e}")
            return False, ""

    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula."""
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2 +
            math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return self.EARTH_RADIUS_KM * c

    def _store_location(self, key: str, lat: float, lon: float, timestamp: float):
        """Store location in Redis."""
        if not self.redis:
            return

        try:
            self.redis.hmset(key, {
                "lat": lat,
                "lon": lon,
                "timestamp": timestamp,
            })
            self.redis.expire(key, 86400)
        except Exception as e:
            logger.warning(f"Risk score update failed: {e}")
            pass


class RiskScoringEngine:
    """
    Calculates risk scores for users and requests.
    """

    RISK_WEIGHTS = {
        "geo_block": 0.3,
        "rate_limit": 0.2,
        "mfa_failure": 0.25,
        "impossible_travel": 0.25,
    }

    def __init__(self):
        self.redis = redis_client()

    def calculate_risk_score(
        self,
        user_id: Optional[int],
        factors: Dict[str, float],
    ) -> float:
        """Calculate overall risk score."""
        total_score = 0.0
        total_weight = 0.0

        for factor, weight in self.RISK_WEIGHTS.items():
            if factor in factors:
                total_score += factors[factor] * weight
                total_weight += weight

        normalized_score = total_score / total_weight if total_weight > 0 else 0.0
        return min(1.0, normalized_score)

    def should_block(self, risk_score: float, threshold: float = 0.7) -> bool:
        """Determine if request should be blocked based on risk score."""
        return risk_score > threshold

    def update_user_risk(self, user_id: int, score: float):
        """Update user risk score in Redis."""
        if not self.redis:
            return

        try:
            key = f"risk:{user_id}"
            self.redis.setex(key, 3600, score)
        except Exception as e:
            logger.warning(f"Risk score update failed: {e}")
            pass


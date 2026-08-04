"""Zozi Autonomous Fraud Detection & Intelligence Engine (AFDIE).

This service provides real-time fraud scoring, IP intelligence, velocity checks,
and threat feed management for the marketplace.
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
from datetime import datetime, timezone, timedelta
from typing import Any, Optional
import asyncio

import redis
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from data.models import (
    FraudEvent, FraudBlacklist, FraudRule, ManualReviewQueue,
    IPReputation, DeviceFingerprint, User, Order,
    OrderItem, ReturnRequest, PaymentReconciliationRun, SupplierBankAccount,
    UserLoginHistory, CreditCardBin, ReturnAbusePattern,
    SupplierFraudIndicator, LogisticsFraudIndicator, FraudAlert,
    IPAccountLinkage, Shipment, UserDevice
)
from utils.redis_client import get_redis

logger = logging.getLogger(__name__)


class IPIntelligenceService:
    """IP reputation and intelligence using threat feeds and GeoIP data."""
    
    def __init__(self, db: Session, redis_client: Optional[redis.Redis] = None):
        self.db = db
        self.redis = redis_client or get_redis()
        self._asn_cache: dict[str, dict[str, Any]] = {}
        self._geo_cache: dict[str, dict[str, Any]] = {}
    
    def check_ip_reputation(self, ip_address: str) -> dict[str, Any]:
        """Check if IP is in threat feeds or known proxy/VPN ranges."""
        cached = self.redis.get(f"fraud:ip:{ip_address}")
        if cached:
            try:
                return json.loads(cached)
            except (json.JSONDecodeError, TypeError):
                pass
        
        ip_lower = ip_address.lower()
        
        is_proxy = self._check_bloom_filter(ip_lower, "proxies")
        is_tor = self._check_bloom_filter(ip_lower, "tor")
        is_vpn = self._check_bloom_filter(ip_lower, "vpn")
        is_hosting = self._check_bloom_filter(ip_lower, "hosting_asns")
        
        asn_info = self._get_asn_info(ip_address)
        geo_info = self._get_geo_info(ip_address)
        
        result = {
            "ip_address": ip_address,
            "is_proxy": is_proxy,
            "is_vpn": is_vpn,
            "is_tor": is_tor,
            "is_hosting": is_hosting,
            "asn": asn_info.get("asn"),
            "asn_name": asn_info.get("name"),
            "country": geo_info.get("country", "AE"),
            "latitude": geo_info.get("latitude"),
            "longitude": geo_info.get("longitude"),
            "city": geo_info.get("city"),
            "is_blacklisted": is_proxy or is_tor,
            "risk_score": self._calculate_ip_risk(is_proxy, is_tor, is_vpn, is_hosting, asn_info),
        }
        
        self.redis.setex(f"fraud:ip:{ip_address}", 3600, json.dumps(result))
        
        db_record = self.db.query(IPReputation).filter(IPReputation.ip_address == ip_address).first()
        if db_record:
            db_record.is_proxy = is_proxy
            db_record.is_tor = is_tor
            db_record.is_vpn = is_vpn
            db_record.is_hosting = is_hosting
            db_record.asn = asn_info.get("asn")
            db_record.country_code = geo_info.get("country", "AE")
            db_record.last_seen_at = datetime.now(timezone.utc)
            db_record.reputation_score = result["risk_score"]
            db_record.updated_at = datetime.now(timezone.utc)
        else:
            db_record = IPReputation(
                ip_address=ip_address,
                is_proxy=is_proxy,
                is_tor=is_tor,
                is_vpn=is_vpn,
                is_hosting=is_hosting,
                asn=asn_info.get("asn"),
                country_code=geo_info.get("country", "AE"),
                last_seen_at=datetime.now(timezone.utc),
                reputation_score=result["risk_score"],
            )
            self.db.add(db_record)
        self.db.commit()
        
        return result
    
    def _get_geo_info(self, ip_address: str) -> dict[str, Any]:
        """Get GeoIP information for an IP."""
        if ip_address in self._geo_cache:
            return self._geo_cache[ip_address]
        
        return {
            "country": "AE",
            "latitude": 24.0,
            "longitude": 54.0,
            "city": "Dubai",
        }
    
    def _check_bloom_filter(self, ip: str, filter_name: str) -> bool:
        """Check if IP is in Redis Bloom Filter."""
        try:
            key = f"fraud:bloom:{filter_name}"
            return self.redis.execute_command("BF.EXISTS", key, ip) == 1
        except redis.exceptions.ResponseError:
            return False
    
    def _get_asn_info(self, ip_address: str) -> dict[str, Any]:
        """Get ASN information for an IP."""
        try:
            import ipaddress
            ip_obj = ipaddress.ip_address(ip_address)
            ip_int = int(ip_obj)
            
            asn_key = f"asn:{ip_int >> 24}"
            cached = self._asn_cache.get(asn_key)
            if cached:
                return cached
            
            return {"asn": "AS1234", "name": "EXAMPLE-AS", "country": "AE"}
        except ValueError:
            return {}
    
    def _calculate_ip_risk(self, is_proxy: bool, is_tor: bool, is_vpn: bool, 
                           is_hosting: bool, asn_info: dict) -> int:
        """Calculate risk score for an IP address."""
        score = 0
        if is_tor:
            score += 50
        if is_proxy:
            score += 30
        if is_vpn:
            score += 25
        if is_hosting:
            score += 20
        return min(score, 100)


class DeviceFingerprintService:
    """Enhanced device fingerprinting with browser and hardware signals."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def compute_fingerprint(self, request_headers: dict[str, str]) -> Optional[str]:
        """Compute device fingerprint from request headers."""
        parts = []
        fingerprint_headers = [
            "user-agent", "accept-language", "sec-ch-ua",
            "sec-ch-ua-platform", "sec-ch-ua-mobile"
        ]
        for name in fingerprint_headers:
            value = request_headers.get(name, "")
            if value:
                parts.append(f"{name}={value}")
        
        explicit_id = request_headers.get("X-Device-ID", "").strip()
        if explicit_id:
            parts.append(f"x-device-id={explicit_id}")
        
        if not parts:
            return None
        
        raw = "|".join(parts)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
    
    def check_headless_browser(self, user_agent: str, headers: dict[str, str]) -> bool:
        """Detect headless browser automation."""
        headless_indicators = [
            "HeadlessChrome", "HeadlessFirefox", "puppeteer", "playwright",
            "selenium", "webdriver", "phantom", "slimer", "phantomjs"
        ]
        ua_lower = user_agent.lower()
        for indicator in headless_indicators:
            if indicator.lower() in ua_lower:
                return True
        
        if headers.get("sec-ch-ua") is None and "chrome" in ua_lower:
            return True
        
        return False
    
    def get_or_create_device(self, fingerprint: str, user_id: Optional[int] = None,
                             ip_address: Optional[str] = None) -> DeviceFingerprint:
        """Get existing device or create new record."""
        device = self.db.query(DeviceFingerprint).filter(
            DeviceFingerprint.fingerprint_hash == fingerprint
        ).first()
        
        if not device:
            device = DeviceFingerprint(
                fingerprint_hash=fingerprint,
                user_id=user_id,
                risk_score=0,
            )
            self.db.add(device)
        
        if user_id and not device.user_id:
            device.user_id = user_id
        
        if ip_address:
            ips = json.loads(device.ip_addresses) if device.ip_addresses else []
            if ip_address not in ips:
                ips.append(ip_address)
                device.ip_addresses = json.dumps(ips[:100])
        
        device.last_seen_at = datetime.now(timezone.utc)
        self.db.commit()
        return device
    
    def update_device_risk(self, fingerprint: str, headless_detected: bool = False) -> DeviceFingerprint:
        """Update device risk score based on behavior."""
        device = self.db.query(DeviceFingerprint).filter(
            DeviceFingerprint.fingerprint_hash == fingerprint
        ).first()
        
        if not device:
            return None
        
        if headless_detected:
            device.headless_attempts = (device.headless_attempts or 0) + 1
            device.risk_score = min(device.risk_score + 25, 100)
        
        if device.account_count and device.account_count >= 5:
            device.risk_score = min(device.risk_score + 20, 100)
        
        self.db.commit()
        return device


class IPAccountLinkageService:
    """Tracks IP-to-account relationships for fraud detection."""
    
    def __init__(self, db: Session, redis_client: Optional[redis.Redis] = None):
        self.db = db
        self.redis = redis_client or get_redis()
    
    def record_linkage(self, ip_address: str, user_id: int, device_hash: Optional[str] = None,
                       session_id: Optional[str] = None) -> IPAccountLinkage:
        """Record an IP-user linkage."""
        linkage = self.db.query(IPAccountLinkage).filter(
            IPAccountLinkage.ip_address == ip_address,
            IPAccountLinkage.user_id == user_id
        ).first()
        
        if not linkage:
            linkage = IPAccountLinkage(
                ip_address=ip_address,
                user_id=user_id,
                device_fingerprint=device_hash,
                session_id=session_id,
            )
            self.db.add(linkage)
        else:
            linkage.last_seen = datetime.now(timezone.utc)
            linkage.interaction_count += 1
            if device_hash and not linkage.device_fingerprint:
                linkage.device_fingerprint = device_hash
        
        self.db.commit()
        return linkage
    
    def check_ip_multiple_accounts(self, ip_address: str) -> dict[str, Any]:
        """Check how many accounts have used this IP in the last 24 hours."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        
        linkages = self.db.query(IPAccountLinkage).filter(
            IPAccountLinkage.ip_address == ip_address,
            IPAccountLinkage.last_seen >= cutoff
        ).all()
        
        unique_users = set(l.user_id for l in linkages)
        unique_devices = set(l.device_fingerprint for l in linkages if l.device_fingerprint)
        
        is_suspicious = len(unique_users) >= 3
        
        for linkage in linkages:
            if linkage.user_id in unique_users and len(unique_users) >= 3:
                linkage.is_suspicious = True
        self.db.commit()
        
        return {
            "account_count": len(unique_users),
            "device_count": len(unique_devices),
            "is_suspicious": is_suspicious,
            "linkages": [l.id for l in linkages],
        }
    
    def get_suspicious_ips(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get list of IPs flagged for multiple account usage."""
        results = []
        linkages = self.db.query(IPAccountLinkage).filter(
            IPAccountLinkage.is_suspicious == True
        ).group_by(IPAccountLinkage.ip_address).limit(limit).all()
        
        for ip in set(l.ip_address for l in linkages):
            stats = self.check_ip_multiple_accounts(ip)
            stats["ip_address"] = ip
            results.append(stats)
        
        return results


class GraphAnalysisService:
    """Graph-based fraud detection for relationship analysis."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def check_ip_multiple_accounts(self, ip_address: str) -> dict[str, Any]:
        """Check how many accounts have used this IP address."""
        device_count = self.db.query(DeviceFingerprint).filter(
            DeviceFingerprint.ip_addresses.like(f"%{ip_address}%")
        ).count()
        
        user_device_count = self.db.query(UserDevice).filter(
            UserDevice.ip_address == ip_address
        ).count()
        
        ip_events = self.db.query(FraudEvent).filter(
            FraudEvent.ip_address == ip_address
        ).count()
        
        return {
            "account_count": device_count + user_device_count,
            "device_count": device_count,
            "user_device_count": user_device_count,
            "ip_event_count": ip_events,
            "is_suspicious": (device_count + user_device_count) >= 3,
        }
    
    def check_duplicate_bank_accounts(self, bank_account_hash: str, exclude_user_id: Optional[int] = None) -> dict[str, Any]:
        """Check if bank account is used by multiple suppliers."""
        q = self.db.query(SupplierBankAccount).filter(
            SupplierBankAccount.iban == bank_account_hash
        )
        if exclude_user_id:
            q = q.filter(SupplierBankAccount.supplier_id != exclude_user_id)
        existing = q.first()
        return {
            "is_duplicate": existing is not None,
            "existing_supplier_id": existing.supplier_id if existing else None,
        }
    
    def check_device_account_stacking(self, device_hash: str) -> dict[str, Any]:
        """Check how many accounts are linked to a single device."""
        count = self.db.query(UserDevice).filter(
            UserDevice.fingerprint_hash == device_hash
        ).count()
        return {
            "account_count": count,
            "risk_level": "high" if count >= 5 else "medium" if count >= 3 else "low",
        }
    
    def check_return_abuse_pattern(self, user_id: int) -> dict[str, Any]:
        """Analyze return patterns for abuse."""
        total_orders = self.db.query(Order).filter(Order.user_id == user_id).count()
        total_returns = self.db.query(ReturnRequest).filter(ReturnRequest.user_id == user_id).count()
        return_rate = (total_returns / total_orders) if total_orders > 0 else 0
        
        return {
            "return_rate": return_rate,
            "total_orders": total_orders,
            "total_returns": total_returns,
            "is_abuse": return_rate > 0.25,
        }
    
    def check_session_anomaly(self, user_id: int, ip_address: str) -> dict[str, Any]:
        """Check for session anomalies like impossible travel."""
        from data.models import UserLoginHistory
        last_login = self.db.query(UserLoginHistory).filter(
            UserLoginHistory.user_id == user_id
        ).order_by(UserLoginHistory.timestamp.desc()).first()
        
        if not last_login:
            return {"is_anomaly": False}
        
        last_ip_info = self.db.query(IPReputation).filter(
            IPReputation.ip_address == last_login.ip_address
        ).first()
        current_ip_info = self.db.query(IPReputation).filter(
            IPReputation.ip_address == ip_address
        ).first()
        
        if not last_ip_info or not current_ip_info:
            return {"is_anomaly": False}
        
        if last_ip_info.country_code and current_ip_info.country_code:
            if last_ip_info.country_code != current_ip_info.country_code:
                return {
                    "is_anomaly": True,
                    "type": "country_change",
                    "from": last_ip_info.country_code,
                    "to": current_ip_info.country_code,
                }
        
        return {"is_anomaly": False}


class FraudScoringEngine:
    """Real-time fraud scoring engine with velocity checks and rule evaluation."""
    
    def __init__(self, db: Session, redis_client: Optional[redis.Redis] = None):
        self.db = db
        self.redis = redis_client or get_redis()
        self.ip_service = IPIntelligenceService(db, self.redis)
        self.device_service = DeviceFingerprintService(db)
        self.graph_service = GraphAnalysisService(db)
        self.ip_linkage_service = IPAccountLinkageService(db, self.redis)
    
    def calculate_score(self, user_id: Optional[int], ip_address: str, 
                        device_hash: Optional[str], event_type: str,
                        amount: Optional[float] = None,
                        request_headers: Optional[dict[str, str]] = None,
                        additional_signals: Optional[dict[str, Any]] = None,
                        session_id: Optional[str] = None) -> dict[str, Any]:
        """Calculate fraud score for an event with comprehensive detection."""
        score = 0
        triggered_rules: list[str] = []
        details: dict[str, Any] = {}
        additional_signals = additional_signals or {}
        
        ip_info = self.ip_service.check_ip_reputation(ip_address)
        if ip_info.get("is_proxy"):
            score += 40
            triggered_rules.append("ip_proxy")
        if ip_info.get("is_tor"):
            score += 50
            triggered_rules.append("ip_tor")
        if ip_info.get("is_vpn"):
            score += 25
            triggered_rules.append("ip_vpn")
        if ip_info.get("is_hosting"):
            score += 25
            triggered_rules.append("ip_hosting")
        
        if device_hash:
            device = self.device_service.get_or_create_device(device_hash, user_id, ip_address)
            if device and device.is_blocked:
                score += 60
                triggered_rules.append("device_blocked")
            if device and device.risk_score > 70:
                score += device.risk_score // 2
                triggered_rules.append("device_high_risk")
            
            stack_info = self.graph_service.check_device_account_stacking(device_hash)
            if stack_info.get("risk_level") == "high":
                score += 35
                triggered_rules.append("device_account_stacking")
        
        ip_accounts = self.ip_linkage_service.check_ip_multiple_accounts(ip_address)
        if ip_accounts.get("is_suspicious"):
            score += 30
            triggered_rules.append("ip_multiple_accounts")
        
        if user_id and ip_address:
            self.ip_linkage_service.record_linkage(ip_address, user_id, device_hash, session_id)
        
        if self._check_velocity(ip_address, "login"):
            score += 30
            triggered_rules.append("login_velocity")
        
        if self._check_velocity(device_hash or ip_address, "checkout"):
            score += 20
            triggered_rules.append("checkout_velocity")
        
        if request_headers:
            user_agent = request_headers.get("user-agent", "")
            if self.device_service.check_headless_browser(user_agent, request_headers):
                score += 45
                triggered_rules.append("headless_browser")
            
            ip_country = ip_info.get("country", "AE")
            user_country = None
            if user_id:
                user = self.db.query(User).filter(User.id == user_id).first()
                if user:
                    user_country = user.preferred_country
            
            if user_country and ip_country != user_country:
                score += 15
                triggered_rules.append("geographic_mismatch")
        
        if amount and user_id:
            user = self.db.query(User).filter(User.id == user_id).first() if user_id else None
            if user and user.role == "customer":
                if amount > 500:
                    score += 20
                    triggered_rules.append("high_value_order")
        
        if event_type == "checkout" and amount:
            return_rate = self.graph_service.check_return_abuse_pattern(user_id)
            if return_rate.get("is_abuse"):
                score += 40
                triggered_rules.append("return_abuse_pattern")
        
        if additional_signals:
            if additional_signals.get("is_cod") and additional_signals.get("is_new_account"):
                score += 25
                triggered_rules.append("cod_new_account_risk")
            if additional_signals.get("disposable_email"):
                score += 15
                triggered_rules.append("disposable_email")
            if additional_signals.get("invalid_phone"):
                score += 20
                triggered_rules.append("invalid_phone")
            if additional_signals.get("bin_mismatch"):
                score += 15
                triggered_rules.append("bin_country_mismatch")
            if additional_signals.get("copy_paste_card"):
                score += 15
                triggered_rules.append("copy_paste_card")
            if additional_signals.get("form_speed_ms", 9999) < 200:
                score += 20
                triggered_rules.append("bot_form_speed")
        
        if user_id and request_headers:
            session_id_val = session_id or f"{user_id}_{datetime.now(timezone.utc).isoformat()}"
            behavioral = self.analyze_behavioral_biometrics(user_id, session_id_val, additional_signals)
            if behavioral.get("is_bot"):
                score += behavioral.get("confidence", 0)
                triggered_rules.append("behavioral_bot_detected")
            
            session_anomaly = self.analyze_session_anomaly(user_id, ip_address, device_hash, session_id_val)
            if session_anomaly.get("score", 0) > 0:
                score += session_anomaly.get("score", 0)
                triggered_rules.append("session_anomaly")
        
        score = min(score, 100)
        
        fraud_event = FraudEvent(
            user_id=user_id,
            event_type=event_type,
            ip_address=ip_address,
            device_hash=device_hash,
            fraud_score=score,
            triggered_rules=json.dumps(triggered_rules),
            details=json.dumps({**details, **additional_signals}),
        )
        self.db.add(fraud_event)
        self.db.commit()
        
        if score >= 61:
            self.create_fraud_alert(
                entity_type="order" if event_type == "checkout" else "user",
                entity_id=user_id or 0,
                fraud_score=score,
                triggered_rules=triggered_rules,
                priority="urgent" if score >= 86 else "high",
                details=details,
            )
        
        return {
            "score": score,
            "triggered_rules": triggered_rules,
            "is_blocked": score >= 86,
            "is_review": 61 <= score <= 85,
            "action": self._determine_action(score),
        }
    
    def check_impossible_travel(self, user_id: int, ip_address: str) -> dict[str, Any]:
        """Check if user has logged in from geographically impossible locations."""
        from data.models import UserLoginHistory
        last_login = self.db.query(UserLoginHistory).filter(
            UserLoginHistory.user_id == user_id
        ).order_by(UserLoginHistory.timestamp.desc()).first()
        
        if not last_login:
            return {"is_impossible": False}
        
        last_ip_info = self.ip_service.check_ip_reputation(last_login.ip_address)
        current_ip_info = self.ip_service.check_ip_reputation(ip_address)
        
        last_coords = last_ip_info.get("coordinates", {})
        current_coords = current_ip_info.get("coordinates", {})
        
        if not last_coords or not current_coords:
            return {"is_impossible": False}
        
        distance = self._haversine_distance(
            last_coords.get("lat", 0), last_coords.get("lon", 0),
            current_coords.get("lat", 0), current_coords.get("lon", 0)
        )
        time_diff_hours = (datetime.now(timezone.utc) - last_login.timestamp).total_seconds() / 3600
        
        if time_diff_hours > 0:
            speed_kmh = distance / time_diff_hours
            if speed_kmh > 1000:
                return {
                    "is_impossible": True,
                    "distance_km": distance,
                    "speed_kmh": speed_kmh,
                    "previous_ip": last_login.ip_address,
                    "current_ip": ip_address,
                }
        
        return {"is_impossible": False}
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates in km."""
        import math
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
    
    def _check_velocity(self, key: str, event_type: str) -> bool:
        """Check velocity limits using Redis sliding window."""
        window_key = f"fraud:velocity:{event_type}:{key}"
        limits = {
            "login": 5,
            "checkout": 3,
            "payout": 2,
            "password_reset": 3,
        }
        limit = limits.get(event_type, 5)
        try:
            current = self.redis.incr(window_key)
            if current == 1:
                self.redis.expire(window_key, 3600)
            return current > limit
        except redis.exceptions.ConnectionError:
            return False
    
    def check_comprehensive_velocity(self, user_id: Optional[int], ip_address: str,
                                      device_hash: Optional[str], event_type: str) -> dict[str, Any]:
        """Check velocity for all entities with configurable limits."""
        results = {}
        limits = {
            "login_per_ip": {"limit": 5, "window": 3600, "score": 30},
            "login_per_user": {"limit": 10, "window": 28800, "score": 20},
            "checkout_per_ip": {"limit": 3, "window": 3600, "score": 25},
            "checkout_per_user": {"limit": 15, "window": 86400, "score": 15},
            "payout_per_user": {"limit": 2, "window": 86400, "score": 40},
            "password_reset_per_ip": {"limit": 3, "window": 3600, "score": 35},
        }
        
        for velocity_key, config in limits.items():
            if not velocity_key.startswith(event_type):
                continue
            
            entity_key = None
            if "ip" in velocity_key:
                entity_key = ip_address
            elif "user" in velocity_key and user_id:
                entity_key = str(user_id)
            elif "device" in velocity_key and device_hash:
                entity_key = device_hash
            
            if entity_key:
                key = f"velocity:{velocity_key}:{entity_key}"
                try:
                    current = self.redis.incr(key)
                    if current == 1:
                        self.redis.expire(key, config["window"])
                    if current > config["limit"]:
                        results[velocity_key] = {"exceeded": True, "count": current, "score": config["score"]}
                except redis.exceptions.ConnectionError:
                    pass
        
        return results
    
    def _determine_action(self, score: int) -> str:
        """Determine action based on fraud score."""
        if score >= 86:
            return "block"
        elif score >= 61:
            return "review"
        elif score >= 31:
            return "step_up_auth"
        else:
            return "allow"
    
    def analyze_behavioral_biometrics(self, user_id: int, session_id: str,
                                       form_data: Optional[dict] = None) -> dict[str, Any]:
        """Analyze behavioral patterns for bot detection."""
        result = {"is_bot": False, "confidence": 0, "signals": []}
        
        if not form_data:
            return result
        
        typing_speed = form_data.get("typing_speed_wpm", 0)
        if typing_speed < 30 and typing_speed > 0:
            result["is_bot"] = True
            result["confidence"] += 25
            result["signals"].append("extremely_slow_typing")
        
        mouse_movement = form_data.get("mouse_movement", "")
        if mouse_movement == "straight_line":
            result["is_bot"] = True
            result["confidence"] += 20
            result["signals"].append("straight_line_mouse")
        
        copy_paste = form_data.get("copy_paste_events", 0)
        if copy_paste > 3:
            result["is_bot"] = True
            result["confidence"] += 15
            result["signals"].append("excessive_copy_paste")
        
        form_completion = form_data.get("form_completion_ms", 99999)
        if form_completion < 200:
            result["is_bot"] = True
            result["confidence"] += 20
            result["signals"].append("instant_form_completion")
        
        return result
    
    def analyze_session_anomaly(self, user_id: int, ip_address: str,
                                 device_hash: Optional[str], session_id: str) -> dict[str, Any]:
        """Detect session anomalies like hijacking or impossible travel."""
        result = {"anomalies": [], "score": 0}
        
        last_ip_info = self.db.query(UserLoginHistory).filter(
            UserLoginHistory.user_id == user_id
        ).order_by(UserLoginHistory.timestamp.desc()).first()
        
        if last_ip_info:
            try:
                last_ip = last_ip_info.ip_address
                last_time = last_ip_info.timestamp
                current_time = datetime.now(timezone.utc)
                time_diff_hours = (current_time - last_time).total_seconds() / 3600
                
                if time_diff_hours < 24:
                    last_geo = self.ip_service.check_ip_reputation(last_ip)
                    current_geo = self.ip_service.check_ip_reputation(ip_address)
                    
                    if last_geo.get("country") and current_geo.get("country"):
                        if last_geo["country"] != current_geo["country"]:
                            result["anomalies"].append("cross_border_login")
                            result["score"] += 40
            except Exception:
                pass
        
        active_sessions = self.redis.smembers(f"active_sessions:{user_id}")
        if session_id not in active_sessions and len(active_sessions) > 0:
            result["anomalies"].append("concurrent_session")
            result["score"] += 25
        
        self.redis.sadd(f"active_sessions:{user_id}", session_id)
        self.redis.expire(f"active_sessions:{user_id}", 86400)
        
        return result
    
    def get_fraud_dashboard_stats(self) -> dict[str, Any]:
        """Get fraud dashboard statistics."""
        return {
            "total_events_24h": self.db.query(FraudEvent).filter(
                FraudEvent.created_at >= datetime.now(timezone.utc) - timedelta(hours=24)
            ).count(),
            "blocked_events_24h": self.db.query(FraudEvent).filter(
                FraudEvent.created_at >= datetime.now(timezone.utc) - timedelta(hours=24),
                FraudEvent.fraud_score >= 86
            ).count(),
            "review_queue_count": self.db.query(ManualReviewQueue).filter(
                ManualReviewQueue.status == "pending"
            ).count(),
            "blacklisted_ips": self.db.query(FraudBlacklist).filter(
                FraudBlacklist.entity_type == "ip"
            ).count(),
        }
    
    def check_ip_multiple_accounts(self, ip_address: str) -> dict[str, Any]:
        """Check how many accounts have used this IP."""
        device_count = self.db.query(DeviceFingerprint).filter(
            DeviceFingerprint.ip_addresses.like(f"%{ip_address}%")
        ).count()
        
        user_device_count = self.db.query(UserDevice).filter(
            UserDevice.ip_address == ip_address
        ).count()
        
        return {
            "account_count": device_count + user_device_count,
            "device_count": device_count,
            "user_device_count": user_device_count,
            "is_suspicious": (device_count + user_device_count) >= 5,
        }
    
    def check_bin_fraud(self, card_bin: str, country_code: Optional[str] = None) -> dict[str, Any]:
        """Check credit card BIN for fraud indicators."""
        bin_record = self.db.query(CreditCardBin).filter(CreditCardBin.bin == card_bin).first()
        
        result = {
            "is_blacklisted": False,
            "bin_info": None,
            "country_mismatch": False,
        }
        
        if bin_record:
            result["is_blacklisted"] = bin_record.is_blacklisted
            result["bin_info"] = {
                "brand": bin_record.brand,
                "bank": bin_record.bank,
                "country": bin_record.country,
            }
            if country_code and bin_record.country and bin_record.country != country_code:
                result["country_mismatch"] = True
        
        return result
    
    def check_cod_fraud(self, user_id: int, amount: float, payment_method: str) -> dict[str, Any]:
        """Check for COD fraud patterns."""
        result = {"is_ghost_buyer": False, "has_delivery_failures": False, "score": 0}
        
        if payment_method != "cod":
            return result
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return result
        
        if user.created_at and (datetime.now(timezone.utc) - user.created_at).days < 3:
            if amount > 300:
                result["is_ghost_buyer"] = True
                result["score"] += 30
        
        failed_deliveries = self.db.query(Order).filter(
            Order.user_id == user_id,
            Order.status == "delivered",
            Order.delivery_proof_url == None
        ).count()
        
        if failed_deliveries >= 2:
            result["has_delivery_failures"] = True
            result["score"] += 25
        
        return result
    
    def check_logistics_fraud(self, shipment_id: int, delivery_proof: Optional[str] = None,
                               gps_coords: Optional[tuple] = None,
                               scan_time: Optional[datetime] = None) -> dict[str, Any]:
        """Check for logistics fraud patterns."""
        result = {"gps_mismatch": False, "time_anomaly": False, "score": 0}
        
        shipment = self.db.query(Shipment).filter(Shipment.id == shipment_id).first()
        if not shipment:
            return result
        
        if delivery_proof is None:
            result["missing_proof"] = True
            result["score"] += 20
        
        if gps_coords and shipment.delivery_latitude and shipment.delivery_longitude:
            from math import radians, sin, cos, sqrt, atan2
            lat1, lon1 = shipment.delivery_latitude, shipment.delivery_longitude
            lat2, lon2 = gps_coords
            distance = 12742 * sqrt(sin(radians(lat2-lat1)/2)**2 + 
                                     sin(radians(lon2-lon1)/2)**2 * cos(radians(lat1)) * cos(radians(lat2)))
            if distance > 0.5:
                result["gps_mismatch"] = True
                result["score"] += 35
        
        if scan_time:
            order = self.db.query(Order).filter(Order.id == shipment.order_id).first()
            if order and order.created_at:
                time_diff = (scan_time - order.created_at).total_seconds() / 3600
                if time_diff < 1:
                    result["time_anomaly"] = True
                    result["score"] += 25
        
        return result
    
    def create_fraud_alert(self, entity_type: str, entity_id: int, fraud_score: int,
                           triggered_rules: list[str], priority: str = "medium",
                           details: Optional[dict] = None) -> FraudAlert:
        """Create a fraud alert for dashboard."""
        alert = FraudAlert(
            alert_type="score_alert",
            entity_type=entity_type,
            entity_id=entity_id,
            fraud_score=fraud_score,
            triggered_rules=json.dumps(triggered_rules),
            priority=priority,
            details=json.dumps(details or {}),
        )
        self.db.add(alert)
        self.db.commit()
        return alert


class ThreatFeedUpdater:
    """Background job to update threat feeds from open sources."""
    
    def __init__(self, db: Session, redis_client: Optional[redis.Redis] = None):
        self.db = db
        self.redis = redis_client or get_redis()
    
    def update_threat_feeds(self) -> dict[str, int]:
        """Update all threat feeds. Returns counts of updated entries."""
        results = {}
        
        results["tor"] = self._update_tor_list()
        results["proxies"] = self._update_proxy_list()
        results["hosting_asns"] = self._update_hosting_asns()
        
        return results
    
    def _update_tor_list(self) -> int:
        """Update Tor exit node list."""
        try:
            import urllib.request
            url = "https://check.torproject.org/torbulkexitlist"
            with urllib.request.urlopen(url, timeout=30) as response:
                content = response.read().decode("utf-8")
            
            count = 0
            for line in content.strip().split("\n"):
                if line.startswith(""):
                    ip = line
                    key = f"fraud:bloom:tor"
                    try:
                        self.redis.execute_command("BF.ADD", key, ip)
                        count += 1
                    except redis.exceptions.ResponseError:
                        pass
            
            self.db.execute(text("UPDATE ip_reputation SET is_tor = true WHERE ip_address IN (:ips)"), 
                          {"ips": []})
            self.db.commit()
            return count
        except Exception as e:
            logger.error("Failed to update Tor list: " + str(e))
            return 0
    
    def _update_proxy_list(self) -> int:
        """Update proxy IP list."""
        count = 0
        try:
            key = "fraud:bloom:proxies"
            proxies = [
                "1.1.1.1", "8.8.8.8", "9.9.9.9",
            ]
            for ip in proxies:
                try:
                    self.redis.execute_command("BF.ADD", key, ip)
                    count += 1
                except redis.exceptions.ResponseError:
                    pass
        except Exception as e:
            logger.error("Failed to update proxy list: " + str(e))
        return count
    
    def _update_hosting_asns(self) -> int:
        """Update known hosting provider ASN list."""
        count = 0
        try:
            key = "fraud:bloom:hosting_asns"
            asns = ["AS16509", "AS14061", "AS16276", "AS20473"]
            for asn in asns:
                try:
                    self.redis.execute_command("BF.ADD", key, asn)
                    count += 1
                except redis.exceptions.ResponseError:
                    pass
        except Exception as e:
            logger.error("Failed to update hosting ASNs: " + str(e))
        return count


class WebSocketAlertService:
    """Broadcasts real-time fraud alerts via WebSocket."""
    
    _instance = None
    _subscribers: list = []
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._connected = False
        return cls._instance
    
    def add_subscriber(self, websocket):
        """Add a WebSocket subscriber."""
        if websocket not in self._subscribers:
            self._subscribers.append(websocket)
    
    def remove_subscriber(self, websocket):
        """Remove a WebSocket subscriber."""
        if websocket in self._subscribers:
            self._subscribers.remove(websocket)
    
    async def broadcast_alert(self, alert: dict[str, Any]):
        """Broadcast an alert to all subscribers."""
        disconnected = []
        for ws in self._subscribers:
            try:
                await ws.send_json({
                    "type": "fraud_alert",
                    "data": alert,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
            except Exception:
                disconnected.append(ws)
        
        for ws in disconnected:
            self.remove_subscriber(ws)
    
    async def broadcast_score_update(self, score_data: dict[str, Any]):
        """Broadcast score update to all subscribers."""
        disconnected = []
        for ws in self._subscribers:
            try:
                await ws.send_json({
                    "type": "score_update",
                    "data": score_data,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
            except Exception:
                disconnected.append(ws)
        
        for ws in disconnected:
            self.remove_subscriber(ws)


class TransactionPatternAnalyzer:
    """Analyzes transaction patterns for fraud detection."""
    
    def __init__(self, db: Session, redis_client: Optional[redis.Redis] = None):
        self.db = db
        self.redis = redis_client or get_redis()
    
    def analyze_order_pattern(self, user_id: int, amount: float, 
                               category_id: int) -> dict[str, Any]:
        """Analyze order patterns for anomalies."""
        result = {"is_anomaly": False, "score": 0, "signals": []}
        
        recent_orders = self.db.query(Order).filter(
            Order.user_id == user_id,
            Order.created_at >= datetime.now(timezone.utc) - timedelta(hours=24)
        ).all()
        
        if len(recent_orders) >= 5:
            result["signals"].append("high_frequency_orders")
            result["score"] += 20
            result["is_anomaly"] = True
        
        amounts = [o.total_amount for o in recent_orders]
        if amounts:
            avg_amount = sum(amounts) / len(amounts)
            if amount > avg_amount * 3:
                result["signals"].append("amount_spike")
                result["score"] += 25
                result["is_anomaly"] = True
        
        same_category_count = sum(1 for o in recent_orders if o.category_id == category_id)
        if same_category_count >= 3:
            result["signals"].append("category_binge")
            result["score"] += 15
            result["is_anomaly"] = True
        
        return result
    
    def analyze_payout_pattern(self, user_id: int, amount: float) -> dict[str, Any]:
        """Analyze payout patterns for money laundering indicators."""
        result = {"is_anomaly": False, "score": 0, "signals": []}
        
        recent_payouts = self.db.query(Order).filter(
            Order.user_id == user_id,
            Order.payment_method == "payout",
            Order.created_at >= datetime.now(timezone.utc) - timedelta(days=7)
        ).all()
        
        total_payout = sum(o.total_amount for o in recent_payouts)
        if total_payout > 10000:
            result["signals"].append("high_payout_volume")
            result["score"] += 35
            result["is_anomaly"] = True
        
        if len(recent_payouts) >= 5:
            result["signals"].append("frequent_payouts")
            result["score"] += 25
            result["is_anomaly"] = True
        
        return result


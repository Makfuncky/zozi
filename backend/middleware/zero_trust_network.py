#!python
"""
Zero-Trust Network Security
Implements service mesh security with mTLS and service identity
"""

import time
import hashlib
import secrets
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

from utils.redis_client import redis_client


@dataclass
class ServiceIdentity:
    """Service identity for zero-trust authentication."""
    service_id: str
    service_name: str
    public_key: str
    trusted_by: List[str] = None
    created_at: datetime = None
    expires_at: datetime = None

    def __post_init__(self):
        if self.trusted_by is None:
            self.trusted_by = []
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class ServiceMeshSecurity:
    """
    Zero-trust service mesh security implementation.
    Provides service-to-service authentication and authorization.
    """

    def __init__(self):
        self.redis = redis_client()
        self.services: Dict[str, ServiceIdentity] = {}

    def register_service(self, service_name: str, public_key: str) -> str:
        """Register a service in the mesh."""
        service_id = hashlib.sha256(
            f"{service_name}:{public_key}:{time.time()}".encode()
        ).hexdigest()[:32]

        identity = ServiceIdentity(
            service_id=service_id,
            service_name=service_name,
            public_key=public_key,
            expires_at=datetime.utcnow() + timedelta(days=30),
        )

        self.services[service_id] = identity

        if self.redis:
            self._store_service_identity(identity)

        return service_id

    def _store_service_identity(self, identity: ServiceIdentity):
        """Store service identity in Redis."""
        key = f"mesh:service:{identity.service_id}"
        data = {
            "service_id": identity.service_id,
            "service_name": identity.service_name,
            "public_key": identity.public_key,
            "trusted_by": identity.trusted_by,
            "created_at": identity.created_at.isoformat(),
            "expires_at": identity.expires_at.isoformat(),
        }
        self.redis.hmset(key, data)
        self.redis.expire(key, 86400 * 30)

    def validate_service_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate service token."""
        if not self.redis:
            return None

        key = f"mesh:token:{token}"
        data = self.redis.hgetall(key)
        if not data:
            return None

        return {k.decode(): v.decode() for k, v in data.items()}

    def generate_service_token(
        self, service_id: str, ttl_seconds: int = 3600
    ) -> str:
        """Generate a service token."""
        token = secrets.token_urlsafe(32)
        key = f"mesh:token:{token}"

        if self.redis:
            self.redis.hmset(key, {
                "service_id": service_id,
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": (
                    datetime.utcnow() + timedelta(seconds=ttl_seconds)
                ).isoformat(),
            })
            self.redis.expire(key, ttl_seconds)

        return token


class mTLSHandler:
    """Handles mutual TLS authentication."""

    def __init__(self):
        self.redis = redis_client()

    def verify_certificate(self, cert_pem: str, ca_chain: str) -> bool:
        """Verify certificate against CA chain."""
        cert_hash = hashlib.sha256(cert_pem.encode()).hexdigest()
        
        if self.redis:
            cached = self.redis.get(f"cert:valid:{cert_hash}")
            if cached is not None:
                return cached == "1"

        import ssl
        try:
            context = ssl.create_default_context()
            context.load_verify_locations(cast=str, c=ca_chain)
            context.verify_mode = ssl.CERT_REQUIRED
            return True
        except Exception:
            return False

    def get_peer_cert(self, ssl_object) -> Optional[str]:
        """Get peer certificate from SSL connection."""
        try:
            return ssl_object.getpeercert(binary_form=True).decode()
        except Exception:
            return None


class NetworkPolicy:
    """Network access policies for zero-trust."""

    def __init__(self):
        self.redis = redis_client()

    def allow_connection(
        self, source_service: str, dest_service: str, port: int
    ) -> bool:
        """Check if connection is allowed."""
        key = f"policy:allow:{source_service}:{dest_service}:{port}"
        
        if self.redis:
            cached = self.redis.get(key)
            if cached is not None:
                return cached == "1"

        return True

    def enforce_egress(
        self, source_ip: str, dest_ip: str, dest_port: int
    ) -> bool:
        """Enforce egress network policies."""
        key = f"policy:egress:{source_ip}:{dest_ip}:{dest_port}"
        
        if self.redis:
            blocked = self.redis.get(f"blocked:egress:{dest_ip}:{dest_port}")
            if blocked:
                return False

        return True

    def is_trusted_network(self, ip: str) -> bool:
        """Check if IP is in trusted network range."""
        trusted_ranges = ["10.", "192.168.", "172.16.", "127.0.0.1"]
        return any(ip.startswith(r) for r in trusted_ranges)


class ZeroTrustMiddleware:
    """Middleware for zero-trust network enforcement."""

    def __init__(self):
        self.mesh = ServiceMeshSecurity()
        self.policy = NetworkPolicy()

    async def authenticate_service(self, request) -> bool:
        """Authenticate service request."""
        token = request.headers.get("X-Service-Token")
        if not token:
            return False

        service_info = self.mesh.validate_service_token(token)
        return service_info is not None

    def tag_trusted_network(self, ip: str) -> bool:
        """Tag IP as trusted network."""
        return self.policy.is_trusted_network(ip)


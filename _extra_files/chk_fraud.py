import sys, importlib
sys.path.insert(0,'.')
try:
    import routers.public_security_detection as m
    print("OK import; routes:", len(m.router.routes))
except Exception as e:
    import traceback; traceback.print_exc()
from services.fraud_detection_service import FraudScoringEngine, GraphAnalysisService
print("FraudScoringEngine has db attr:", "db" in vars(FraudScoringEngine) or "db" in FraudScoringEngine.__init__.__code__.co_varnames)

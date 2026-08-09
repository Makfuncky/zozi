"""Reproduce the AnalyticsProvider AttributeError by loading the file directly."""
import importlib.util, sys, traceback
sys.path.insert(0, ".")

path = "providers/analytics/analytics.py"
spec = importlib.util.spec_from_file_location("isolated_analytics_provider", path)
mod = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(mod)
    p = mod.AnalyticsProvider()
    print("PROVIDER_INSTANTIATE: ok ->", p._default_period_days)
except Exception as e:
    print("PROVIDER_INSTANTIATE: FAIL", repr(e))
    traceback.print_exc()

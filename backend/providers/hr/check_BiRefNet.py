from __future__ import annotations
from rembg import new_session
import logging
import structlog
logger = structlog.get_logger(__name__)
logger = logging.getLogger(__name__)
try:
    session = new_session('birefnet-general')
    logger.info('✅ BiRefNet is available!')
except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
    logger.info(f'❌ BiRefNet not available: {e}')
    logger.info('\nTrying other models...')
    from rembg.sessions import sessions_class
    logger.info(f'Available models: {list(sessions_class.keys())}')
'\n\n# Test which BiRefNet models are available\nmodel_names = [\n    \'birefnet-general\',\n    \'birefnet-general-lite\', \n    \'birefnet-portrait\',\n    \'birefnet-massive\',\n    \'birefnet-dis\',\n    \'birefnet-hrsod\',\n    \'birefnet-cod\',\n    \'birefnet-mo\',\n]\n\nfrom rembg import new_session\n\nfor model_name in model_names:\n    try:\n        session = new_session(model_name)\n        print(f"✅ {model_name} - AVAILABLE")\n    except Exception as e:\n        print(f"❌ {model_name} - Not available")\n\n'
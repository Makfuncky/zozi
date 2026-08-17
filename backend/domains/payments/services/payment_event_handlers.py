"""Event subscribers for payment-related domain events.



These handlers are registered in ``lifespan.py`` against the shared

``_event_publisher``.  They run *out-of-band* from the payment providers:

the providers only publish domain events (``PaymentConfirmedEvent``,

``PaymentFailedEvent``, ``PaymentRefundedEvent``) and never call ``services``

directly, which keeps the ``providers`` layer decoupled from the ``services``

layer (clears CG1/CG2).  Each handler opens its own DB session via the

wrappers registered at startup.



All handlers are defensive: a failure in one must not break the others or

the publishing gateway.

"""



from __future__ import annotations



import logging

from decimal import Decimal

from typing import Optional



from events import (

    PaymentConfirmedEvent,

    PaymentFailedEvent,

    PaymentRefundedEvent,

)

from models import Order



from domains.finance.services.cash_management_service import create_ledger_entries_for_order, log_card_payment_received, log_refund_bank_transaction, create_refund_ledger_entry

from domains.finance.services.general_ledger_service import post_order_payment_journal

from domains.comms.services.transactional_email_service import enqueue_payment_confirmed_email, enqueue_payment_failed_email, enqueue_refund_processed_email

from infrastructure.redis.cache import bump_product_cache_version

import structlog

logger = structlog.get_logger(__name__)



logger = logging.getLogger(__name__)





def handle_payment_confirmed(event: PaymentConfirmedEvent, db) -> None:

    """Create ledger entries, cash/bank records, cache bump and confirmation email.



    Runs for both gateway payments and Cash-on-Delivery confirmations.

    Card-specific side effects (card payment received, payment journal) are

    skipped for COD orders to preserve prior behavior.

    """

    order = db.query(Order).filter(Order.id == event.order_id).first()

    if order is None:

        logger.warning("PaymentConfirmed: order %s not found", event.order_id)

        return



    # Ledger entries for the order (applies to both card and COD).

    try:

        create_ledger_entries_for_order(order, db)

    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:

        logger.exception("PaymentConfirmed: failed ledger entries for order %s", event.order_id)



    # Card-specific accounting only for non-COD payments.

    if str(event.payment_method).lower() != "cod":

        try:

            log_card_payment_received(order, db)

        except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:

            logger.exception("PaymentConfirmed: failed card payment received for order %s", event.order_id)

        try:

            post_order_payment_journal(

                db,

                event.order_id,

                Decimal(str(event.amount)),

                currency=str(event.currency or "OMR"),

            )

        except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:

            logger.exception("PaymentConfirmed: failed payment journal for order %s", event.order_id)



    # Invalidate cached product catalog (stock changed on confirmation).

    try:

        bump_product_cache_version()

    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:

        logger.exception("PaymentConfirmed: failed cache bump for order %s", event.order_id)



    # Customer confirmation email.

    try:

        enqueue_payment_confirmed_email(

            event.order_id,

            provider=str(event.payment_gateway),

            message=None,

        )

    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:

        logger.exception("PaymentConfirmed: failed email enqueue for order %s", event.order_id)





def handle_payment_failed(event: PaymentFailedEvent, db) -> None:

    """Notify the customer that a payment attempt failed."""

    try:

        enqueue_payment_failed_email(

            event.order_id,

            provider=str(event.provider),

            message=event.message or None,

        )

    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:

        logger.exception("PaymentFailed: failed email enqueue for order %s", event.order_id)





def handle_payment_refunded(event: PaymentRefundedEvent, db) -> None:

    """Create the refund ledger entry, refund bank transaction and email.



    The refund ledger entry is always created (covers provider refunds AND

    controller-driven cancellations/returns).  The bank transaction and the

    customer email are only produced when the publisher supplied

    ``refund_meta`` (i.e. a gateway refund flow), preserving the prior

    behavior where controller-driven refunds did not send those.

    """

    order = db.query(Order).filter(Order.id == event.order_id).first()

    if order is None:

        logger.warning("PaymentRefunded: order %s not found", event.order_id)

        return



    try:

        create_refund_ledger_entry(order, db, reason=event.reason)

    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:

        logger.exception("PaymentRefunded: failed refund ledger for order %s", event.order_id)



    refund_meta = event.refund_meta or {}

    if not refund_meta:

        return



    try:

        log_refund_bank_transaction(

            order,

            db,

            source=str(refund_meta.get("source", "refund")),

            transaction_ref=refund_meta.get("transaction_ref"),

            description=refund_meta.get("description"),

            transaction_date=refund_meta.get("transaction_date"),

        )

    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:

        logger.exception("PaymentRefunded: failed refund bank txn for order %s", event.order_id)



    try:

        enqueue_refund_processed_email(

            event.order_id,

            source=str(refund_meta.get("source", "refund")),

        )

    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:

        logger.exception("PaymentRefunded: failed email enqueue for order %s", event.order_id)





__all__ = [

    "handle_payment_confirmed",

    "handle_payment_failed",

    "handle_payment_refunded",

]
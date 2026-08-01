"""
Seed realistic communication data — DMs, group messages, entity threads,
and internal emails — so the Communication workspace shows real conversations
when logged in as admin (user ID 1).

Usage:
    cd backend && python seed_comms.py
"""

import sys
import os
import logging
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from db.database import SessionLocal
from models.core import (
    EntityChatThread, EntityChatMessage,
    DirectChatRoom, DirectChatMessage,
    GroupChatRoom, GroupChatMember, GroupChatMessage,
)
from models.employee_models import InternalEmail, EmailFolder, Employee
from sqlalchemy import text

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("seed_comms")


def ts(hours_ago: int) -> datetime:
    return datetime.utcnow() - timedelta(hours=hours_ago)


# ── Seed data ──────────────────────────────────────────────────────────────

ENTITY_THREADS = [
    {
        "title": "Q4 Budget Review — Finance Team",
        "entity_type": "admin",
        "entity_id": 1,
        "messages": [
            (1, "Team, please review the attached Q4 budget draft before Friday.", ts(72)),
            (2, "I've reviewed the marketing line items — they look reasonable but we might need to adjust the ad spend.", ts(70)),
            (1, "Good catch. Can you prepare a revised breakdown by region?", ts(68)),
            (2, "Sure, I'll have it ready by tomorrow EOD.", ts(67)),
            (3, "Customer support headcount request is included, right?", ts(65)),
            (1, "Yes, it's in the ops section. We're approving 3 new hires.", ts(64)),
            (2, "Here's the revised breakdown: Eastern region needs +15%, Western stays flat.", ts(48)),
            (1, "Looks good. Let's finalize in tomorrow's standup.", ts(46)),
        ],
    },
    {
        "title": "Product Launch — ZoziPay Integration",
        "entity_type": "admin",
        "entity_id": 2,
        "messages": [
            (1, "Heads up: ZoziPay integration is targeting Nov 15 launch. We need to align comms.", ts(96)),
            (3, "Marketing collateral is ready — landing page, explainer video, email sequence.", ts(94)),
            (2, "Engineering confirmed the API is stable. We're in final QA.", ts(92)),
            (1, "Let's schedule a dry run with 10 beta users next week.", ts(90)),
            (3, "I'll set up the beta cohort. Mostly power users from the UAE region.", ts(89)),
            (1, "Perfect. Loop in the support team for the beta.", ts(87)),
            (2, "QA passed 98%. One minor bug in the notification service — being patched today.", ts(48)),
            (1, "Excellent. Go status for Nov 15 confirmed. Great work everyone.", ts(46)),
        ],
    },
    {
        "title": "Urgent: Server Migration — AWS to Bare Metal",
        "entity_type": "admin",
        "entity_id": 3,
        "messages": [
            (2, "The migration window is scheduled for this Saturday 2 AM UTC. Expected downtime: 4 hours.", ts(24)),
            (1, "Acknowledged. Have we communicated this to all stakeholders?", ts(23)),
            (2, "Email sent to all department heads. Support team will have an autoresponder ready.", ts(22)),
            (4, "Logistics systems should be unaffected — our stack is on a separate cluster. Confirmed?", ts(21)),
            (2, "Confirmed. Logistics cluster is untouched. Only the main app servers are migrating.", ts(20)),
            (1, "Good. I'll be on-call during the window. Ping me if anything goes sideways.", ts(19)),
            (2, "Rollback plan is in place. We'll abort if initial data sync takes > 90 minutes.", ts(18)),
        ],
    },
    {
        "title": "Customer Escalation — Order ZO-48721",
        "entity_type": "admin",
        "entity_id": 4,
        "messages": [
            (3, "We have a VIP customer (Tier 3) whose order has been stuck in customs for 5 days.", ts(12)),
            (1, "Which country? What's the holdup?", ts(11)),
            (3, "Oman. Missing commercial invoice — the supplier didn't attach the Arabic translation.", ts(10)),
            (1, "Contact the supplier directly and get the translated invoice within 2 hours.", ts(9)),
            (3, "Supplier sent the corrected invoice. Forwarded to the broker.", ts(7)),
            (4, "I've expedited the clearance with our broker in Sohar. Should move tonight.", ts(6)),
            (1, "Good. Once cleared, upgrade shipping to express at our cost.", ts(5)),
            (3, "On it. Drafting the apology email now with a 15% discount code.", ts(4)),
            (2, "I can trigger the priority dispatch flag in the system.", ts(3)),
        ],
    },
    {
        "title": "Security Audit — Q4 Penetration Test Results",
        "entity_type": "admin",
        "entity_id": 5,
        "messages": [
            (2, "Pen test results are in. Summary: 2 critical, 5 high, 12 medium findings.", ts(36)),
            (1, "What are the two criticals?", ts(35)),
            (2, "1) SQL injection vector in the search endpoint. 2) Exposed AWS keys in a public repo.", ts(34)),
            (1, "The keys should have been rotated immediately. Who owns that repo?", ts(33)),
            (2, "Legacy repo from the old devops team. Keys already rotated, repo made private.", ts(32)),
            (1, "Good. SQL injection fix — assign to the backend team with a 48-hour SLA.", ts(31)),
            (2, "Done. Patch is in code review now. ETA: tomorrow COB.", ts(30)),
            (1, "Schedule a follow-up scan for next month to confirm closure.", ts(29)),
        ],
    },
]

DIRECT_CONVERSATIONS = [
    {
        "p1": 1, "p2": 2,
        "messages": [
            (1, "Hey, the new product listings are live. Can you review?", ts(48)),
            (2, "Looking now. The electronics category looks good. Fashion needs better images.", ts(47)),
            (2, "Agreed. I'll ask the vendor to resubmit those.", ts(46)),
            (1, "Also, the pricing on item #4401 seems off — double-check?", ts(44)),
            (2, "You're right. Fixed it. Was a currency conversion error.", ts(43)),
            (1, "Great. Everything else is approved. Pushing live.", ts(42)),
        ],
    },
    {
        "p1": 1, "p2": 3,
        "messages": [
            (3, "Hi! I'm having trouble with my recent order — it hasn't shipped yet.", ts(24)),
            (1, "Let me check. Order #ZO-48123, right?", ts(23)),
            (3, "Yes, that's the one. It's been 4 days.", ts(22)),
            (1, "I see the issue — the payment gateway flagged it for review. Let me clear it manually.", ts(21)),
            (3, "Thank you! I really appreciate the quick help.", ts(20)),
            (1, "Done. It's released now. You'll get the tracking number within the hour.", ts(19)),
        ],
    },
    {
        "p1": 1, "p2": 4,
        "messages": [
            (4, "The new delivery route optimizer is reducing transit times by 18% in trials.", ts(72)),
            (1, "That's impressive. Which cities are showing the biggest improvement?", ts(71)),
            (4, "Dubai to Abu Dhabi dropped from 2.5h to 1.8h. Muscat routes are +12% faster.", ts(70)),
            (1, "When can we roll this out across all hubs?", ts(69)),
            (4, "We need 2 more weeks of testing. Then full rollout.", ts(68)),
            (1, "Approved. Keep me posted on the metrics.", ts(67)),
        ],
    },
]

GROUP_CONVERSATIONS = [
    {
        "name": "Operations — All Hands",
        "created_by": 1,
        "members": [1, 2, 3, 4],
        "messages": [
            (1, "Team, great news — we hit our monthly target 3 days early!", ts(48)),
            (2, "Amazing! Everyone's been working really hard on this.", ts(47)),
            (3, "The new onboarding flow definitely helped conversion.", ts(46)),
            (4, "Logistics was a bottleneck but we cleared it this week.", ts(45)),
            (1, "Let's keep this momentum. Q4 targets are ambitious but achievable.", ts(44)),
            (2, "Would it help if we brought the marketing push forward by a week?", ts(43)),
            (1, "Yes — coordinate with the design team and go ahead.", ts(42)),
        ],
    },
    {
        "name": "Tech Team — Standup",
        "created_by": 2,
        "members": [1, 2],
        "messages": [
            (2, "Morning standup — I worked on the search index optimization yesterday.", ts(18)),
            (1, "How's that looking? We've been getting latency complaints.", ts(17)),
            (2, "Improved P95 from 2.3s to 0.8s in staging. Deploying to prod today.", ts(16)),
            (1, "Great. Any blockers?", ts(15)),
            (2, "Need DB migration approval for the new index. Can you sign off?", ts(14)),
            (1, "Approved. Go ahead with the migration during the maintenance window.", ts(13)),
        ],
    },
]

# ── Per-role email content ────────────────────────────────────────────────
# Each entry: (sender_id, recipient_user_id, subject, body_text, hours_ago)

INTERNAL_EMAIL_DATA = [
    # ── Admin inbox (user_id=1) ─────────────────────────────────────
    (1, 1, "Q4 OKR Review — Please Submit by Friday",
     "Hi team,\n\nPlease submit your Q4 OKRs by end of day Friday.\n\nWe'll review them in Monday's all-hands.\n\nBest,\nAdmin", 96),
    (1, 1, "New Compliance Training — Mandatory",
     "All staff are required to complete the new data privacy compliance training.\n\nThe training takes approximately 45 minutes.\n\nRegards,\nCompliance Team", 72),
    (1, 1, "Updated Vendor Agreement — Signature Required",
     "The new vendor agreement terms have been updated.\n\nKey changes:\n- Payment terms: Net 30 to Net 15\n- SLA response time: 4 hours to 2 hours\n- Added data processing addendum\n\nPlease review and sign by end of week.", 24),
    (1, 1, "Weekly Analytics Report",
     "Here's the weekly performance summary:\n\n- Revenue: +12% WoW\n- New users: +8% WoW\n- Avg order value: $42.50\n- Top category: Electronics\n- Support tickets: 142 (resolved: 138)", 12),

    # ── Supplier inbox (user_id=2) ────────────────────────────────
    (1, 2, "New Product Listing Guidelines — Q4 Update",
     "Dear Supplier,\n\nPlease review the updated product listing guidelines for Q4.\n\nKey changes:\n- Image resolution minimum: 1200x1200\n- Mandatory variant data for electronics\n- New prohibited items list attached\n\nPlease ensure all listings comply by Nov 1st.\n\nRegards,\nZozi Marketplace Team", 120),
    (1, 2, "Invoice #INV-2024-08921 — Payment Processed",
     "Your invoice INV-2024-08921 for $12,450.00 has been processed.\n\nExpected settlement: 3-5 business days.\n\nView details in your Supplier Dashboard.\n\nThanks,\nAccounts Payable", 36),
    (2, 2, "Your Product Catalog — October Performance",
     "Hi there,\n\nYour product catalog performed well in October.\n\n- Listed products: 24\n- Active listings: 22\n- Total sales: $18,230\n- Top seller: Wireless Headphones (SKU: WH-2024)\n\nConsider adding more variants to boost visibility.\n\nBest,\nZozi Analytics", 18),

    # ── Customer inbox (user_id=3) ────────────────────────────────
    (1, 3, "Your Order ZO-48123 Has Shipped!",
     "Great news! Your order ZO-48123 has shipped and is on its way.\n\nTracking number: ZO-TRK-7739201\nEstimated delivery: 3-5 business days\n\nTrack your package: http://zozi.com/track/ZO-TRK-7739201\n\nThank you for shopping with Zozi!", 48),
    (1, 3, "We Miss You — 15% Off Your Next Order",
     "Hi there,\n\nIt's been a while since your last visit. Here's a special offer just for you:\n\n🎉 15% OFF your next order of $50+\nCode: COMEBACK15\nExpires: 30 days\n\nShop now at http://zozi.com\n\nYour Zozi Team", 168),
    (3, 3, "Your Wishlist Items Are on Sale!",
     "Good news — 3 items from your wishlist are now on sale!\n\n- Bose QuietComfort Headphones: Now $249 (was $299)\n- Samsung Galaxy Tab S9: Now $649 (was $699)\n- Leather Messenger Bag: Now $79 (was $99)\n\nSale ends Sunday. Don't miss out!\n\nZozi Deals Team", 6),

    # ── Logistics partner inbox (user_id=4) ────────────────────────
    (1, 4, "Weekly Route Optimization Report",
     "Here's the weekly route optimization summary:\n\n- Total deliveries: 1,842\n- On-time rate: 94.2%\n- Average transit time: 2.3 hours\n- Optimized routes saved 128 driving hours\n\nTop improvement area: Muscat morning routes (-12% efficiency).\n\nKeep up the great work!\n\nZozi Operations", 48),
    (1, 4, "New Hub Opening — Al Ain Distribution Center",
     "The new Al Ain distribution center opens next month.\n\nKey details:\n- Location: Al Ain Industrial Area\n- Capacity: 15,000 packages/day\n- Staff needed: 12 warehouse associates\n- Go-live: December 1\n\nPlease coordinate with HR for hiring and training schedule.\n\nRegards,\nOperations Management", 120),
    (4, 4, "Fleet Maintenance Reminder — Q4 Checks Due",
     "Reminder: Q4 fleet maintenance checks are due by Nov 15.\n\nVehicles due:\n- Truck ZO-102 (mileage: 45,000 km)\n- Van ZO-208 (last service: 8 months ago)\n- Truck ZO-115 (brake inspection due)\n\nPlease schedule with the maintenance team this week.\n\nFleet Management", 72),
]


# ── Main ───────────────────────────────────────────────────────────────────

def seed():
    db = SessionLocal()
    try:
        # ── Clear existing seed data ──────────────────────────────────────
        log.info("Clearing existing communication seed data...")
        db.execute(text("DELETE FROM entity_chat_messages"))
        db.execute(text("DELETE FROM entity_chat_threads"))
        db.execute(text("DELETE FROM direct_chat_messages"))
        db.execute(text("DELETE FROM direct_chat_rooms"))
        db.execute(text("DELETE FROM group_chat_messages"))
        db.execute(text("DELETE FROM group_chat_members"))
        db.execute(text("DELETE FROM group_chat_rooms"))
        db.execute(text("DELETE FROM internal_emails"))
        db.commit()
        log.info("Cleared.\n")

        # ── Ensure Employee + EmailFolder for all users ──────────────────
        LOGIN_EMPLOYEES = [
            (1, "ADM-001", "Administration", "System Administrator"),
            (2, "SUP-001", "Supplier Management", "Vendor Relations"),
            (3, "CUS-001", "Customer Service", "Premium Support Agent"),
            (4, "LOG-001", "Logistics", "Fleet Operations Manager"),
        ]
        log.info("Ensuring Employee + EmailFolder for all users...")
        inbox_folders: dict[int, EmailFolder] = {}
        for user_id, emp_code, dept, pos in LOGIN_EMPLOYEES:
            emp = db.query(Employee).filter(Employee.user_id == user_id).first()
            if not emp:
                emp = Employee(
                    user_id=user_id,
                    employee_code=emp_code,
                    department=dept,
                    position=pos,
                    employment_status="active",
                    hire_date=datetime.utcnow().date() - timedelta(days=365),
                )
                db.add(emp)
                db.flush()
                log.info(f"  Created Employee #{emp.id} for user_id={user_id} ({pos})")
            else:
                log.info(f"  Found Employee #{emp.id} for user_id={user_id}")

            folder = db.query(EmailFolder).filter(
                EmailFolder.employee_id == emp.id,
                EmailFolder.name == "inbox",
            ).first()
            if not folder:
                folder = EmailFolder(
                    employee_id=emp.id,
                    name="inbox",
                    folder_type="inbox",
                    is_system=True,
                    sort_order=0,
                )
                db.add(folder)
                db.flush()
                log.info(f"  Created 'inbox' folder #{folder.id} for user_id={user_id}")
            else:
                log.info(f"  Found 'inbox' folder #{folder.id} for user_id={user_id}")

            inbox_folders[user_id] = folder
        log.info("")

        # ── 1. Entity Chat Threads ────────────────────────────────────────
        log.info("Seeding entity chat threads...")
        for tdata in ENTITY_THREADS:
            thread = EntityChatThread(
                entity_type=tdata["entity_type"],
                entity_id=tdata["entity_id"],
                title=tdata["title"],
                is_active=True,
                created_at=tdata["messages"][0][2] - timedelta(minutes=5),
            )
            db.add(thread)
            db.flush()

            for sender_id, msg, created_at in tdata["messages"]:
                db.add(EntityChatMessage(
                    thread_id=thread.id,
                    sender_id=sender_id,
                    message=msg,
                    message_type="text",
                    created_at=created_at,
                ))
            log.info(f"  Thread #{thread.id}: {tdata['title'][:55]}")

        # ── 2. Direct Chat Rooms + Messages ───────────────────────────────
        log.info("\nSeeding direct messages...")
        for conv in DIRECT_CONVERSATIONS:
            p1, p2 = sorted([conv["p1"], conv["p2"]])
            room = DirectChatRoom(
                chat_id=f"dm_seed_{p1}_{p2}",
                participant_one=p1,
                participant_two=p2,
                country_code="AE",
                is_active=True,
                created_at=conv["messages"][0][2] - timedelta(minutes=3),
            )
            db.add(room)
            db.flush()

            for sender_id, msg, created_at in conv["messages"]:
                db.add(DirectChatMessage(
                    room_id=room.id,
                    sender_id=sender_id,
                    message=msg,
                    message_type="text",
                    created_at=created_at,
                ))
            log.info(f"  DM between users {p1} <-> {p2}")

        # ── 3. Group Chat Rooms + Members + Messages ──────────────────────
        log.info("\nSeeding group conversations...")
        for gdata in GROUP_CONVERSATIONS:
            slug = gdata["name"].lower().replace(" ", "_")[:20]
            room = GroupChatRoom(
                chat_id=f"grp_seed_{slug}",
                name=gdata["name"],
                is_active=True,
                created_by=gdata["created_by"],
                created_at=gdata["messages"][0][2] - timedelta(minutes=3),
            )
            db.add(room)
            db.flush()

            for uid in gdata["members"]:
                db.add(GroupChatMember(
                    room_id=room.id,
                    user_id=uid,
                    role="admin" if uid == gdata["created_by"] else "member",
                ))

            for sender_id, msg, created_at in gdata["messages"]:
                db.add(GroupChatMessage(
                    room_id=room.id,
                    sender_id=sender_id,
                    message=msg,
                    message_type="text",
                    created_at=created_at,
                ))
            log.info(f"  Group: {gdata['name']}")

        # ── 4. Internal Emails ────────────────────────────────────────────
        log.info("\nSeeding internal emails...")
        email_count = 0
        # Track per-user email counts for final summary
        email_counts: dict[int, int] = {1: 0, 2: 0, 3: 0, 4: 0}
        for sender_id, recipient_id, subject, body_text, hours_ago in INTERNAL_EMAIL_DATA:
            folder = inbox_folders.get(recipient_id)
            if not folder:
                log.warning(f"  Skipping email to user_id={recipient_id} — no inbox folder")
                continue

            email = InternalEmail(
                subject=subject,
                body_text=body_text,
                sender_id=sender_id,
                recipients=[{"user_id": recipient_id, "email": f"user{recipient_id}@zozi.com"}],
                folder_id=folder.id,
                is_read=False,
                thread_id=f"seed_thread_{hours_ago}_{recipient_id}",
                created_at=ts(hours_ago),
            )
            db.add(email)
            email_count += 1
            email_counts[recipient_id] = email_counts.get(recipient_id, 0) + 1
            log.info(f"  Email to user_id={recipient_id}: {subject[:50]}")

        db.commit()
        msg_count = sum(len(t["messages"]) for t in ENTITY_THREADS)
        dm_count = sum(len(c["messages"]) for c in DIRECT_CONVERSATIONS)
        grp_count = sum(len(g["messages"]) for g in GROUP_CONVERSATIONS)
        total = msg_count + dm_count + grp_count + email_count
        log.info(f"\n{'='*55}")
        log.info(f"Communication data seeded successfully!")
        log.info(f"  {len(ENTITY_THREADS)} entity threads ({msg_count} messages)")
        log.info(f"  {len(DIRECT_CONVERSATIONS)} DM rooms ({dm_count} messages)")
        log.info(f"  {len(GROUP_CONVERSATIONS)} group chats ({grp_count} messages)")
        log.info(f"  {email_count} internal emails:")
        for uid in sorted(email_counts):
            if email_counts[uid] > 0:
                log.info(f"    - user_id={uid}: {email_counts[uid]} email(s)")
        log.info(f"  Total: {total} messages across all channels")
        log.info(f"{'='*55}")

    except Exception:
        log.exception("Seed failed")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()

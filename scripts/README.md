# ZOZI Project Scripts

This directory contains utility scripts organized by purpose.

## Directory Structure

```
scripts/
├── README.md                    # This file
├── audit_recovery.py           # Post-recovery structure audit
├── admin_verification.py       # Admin verification sweep
├── backup_restore_drill.py     # Database backup restore drill
├── deploy.sh                   # Deployment script
├── health-check.sh             # Health check script
├── full_stack_health_check.py  # Full stack health check
├── setup/                      # Setup and startup scripts
│   ├── run_zozi.bat
│   ├── backend_startup_smoke.py
│   └── test_server.py
├── validation/                 # Validation and check scripts
│   ├── check_backups.py
│   ├── check_db.py
│   ├── check_git.py
│   ├── check_node_modules.py
│   ├── check_venv_packages.py
│   ├── validate_stripe_testmode_checkout.py
│   └── probe_backend_import.py
├── recovery/                   # Database recovery scripts
│   ├── recover_remaining_nulls.py
│   ├── recovery_strip_null_bytes.py
│   ├── restore_phase1.py
│   ├── restore_phase2a.py
│   ├── restore_phase2b.py
│   └── restore_phase3.py
├── maintenance/                # Code maintenance scripts
│   ├── cleanup-bak.sh
│   ├── gen_routers.py
│   ├── overwrite_routers.py
│   ├── fix_*.py
│   ├── convert-fontsize-to-theme.js
│   └── ...
└── testing/                    # Testing and smoke test scripts
    ├── full_stack_health_check.py
    ├── _batch_ai_test.py
    ├── _smoke_admin_users.py
    ├── ai_image_group_smoke.py
    ├── finance_cycle_smoke.py
    ├── live_order_tracking_smoke.py
    ├── sqlite_schema_contract_smoke.py
    ├── test_netstat.bat
    └── loadtests/
```

## Core Scripts (run from repository root)

### audit_recovery.py
Run repeatable post-recovery structure checks across maintained trees.

```bash
python scripts/audit_recovery.py
```

### admin_verification.py
Run the widened admin verification sweep across backend/frontend/mobile.

```bash
python scripts/admin_verification.py
```

### backup_restore_drill.py
Run a backup restore drill against the latest or named backup artifact.

```bash
python scripts/backup_restore_drill.py
```

## Maintenance Tools

### cleanup-bak.sh
Remove `.bak` and `.backup` files from the tree.

```bash
./scripts/maintenance/cleanup-bak.sh
```
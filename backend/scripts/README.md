# Backend Scripts

Operational, migration, audit, and seed scripts. Most scripts are run as
`python -m scripts.<name>` from the `backend/` directory.

## Security migrations

### `migrate_passwords_to_argon2id.py`
Re-hashes legacy bcrypt (`$2a$/$2b$/$2y$`) password hashes to Argon2id
per ADR-022.

**Important:** Plaintext passwords are not recoverable from a bcrypt hash,
so the *normal* migration path is *lazy*: `infrastructure/utils/auth.py`
already detects the legacy bcrypt format on `verify_password` and re-hashes
the password under Argon2id on the user's next successful login.

This CLI script exists for **non-login scenarios** (e.g. test fixtures,
seed accounts shipped with the repo) where the original plaintext is
known ahead of time.

```bash
cd backend

# dry-run summary
python -m scripts.migrate_passwords_to_argon2id

# rewrite a single fixture user (requires known plaintext via env)
MIGRATE_PASSWORD_FORCE=1 PLAINTEXTS_FILE=fixtures/plaintexts.txt \
  python -m scripts.migrate_passwords_to_argon2id --user 1 --apply
```

`PLAINTEXTS_FILE` format (one entry per line, `#` for comments):
```
1:admin123
2:supplier123
3:customer123
```

The script is idempotent and safe to re-run.

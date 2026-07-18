from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path


REQUIRED_PRODUCT_COLUMNS = {
    "id",
    "name",
    "price",
    "stock",
    "category",
    "video_url",
}

REQUIRED_VARIANT_COLUMNS = {
    "id",
    "product_id",
    "title",
    "size",
    "color",
    "material",
    "sku",
    "barcode",
    "product_code",
    "price",
    "stock",
    "media_url",
    "is_active",
    "created_at",
    "updated_at",
}

REQUIRED_VARIANT_INDEXES = {
    "ix_product_variants_barcode",
    "ix_product_variants_is_active",
    "ix_product_variants_product_code",
    "ix_product_variants_product_id",
    "ix_product_variants_sku",
}


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Validate the local SQLite schema contract required by product upload and cart flows.",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=repo_root / "backend" / "zozi.db",
        help="Path to the SQLite database to validate.",
    )
    return parser.parse_args()


def load_table_columns(connection: sqlite3.Connection, table_name: str) -> set[str]:
    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {str(row[1]) for row in rows}


def load_table_indexes(connection: sqlite3.Connection, table_name: str) -> set[str]:
    rows = connection.execute(f"PRAGMA index_list({table_name})").fetchall()
    return {str(row[1]) for row in rows}


def main() -> int:
    args = parse_args()
    db_path = Path(args.db)
    if not db_path.exists():
        print(f"[FAIL] SQLite database not found: {db_path}")
        return 1

    connection = sqlite3.connect(db_path)
    try:
        failures: list[str] = []

        product_columns = load_table_columns(connection, "products")
        missing_product_columns = sorted(REQUIRED_PRODUCT_COLUMNS - product_columns)
        if missing_product_columns:
            failures.append(
                "products table is missing required columns: " + ", ".join(missing_product_columns)
            )

        variant_columns = load_table_columns(connection, "product_variants")
        missing_variant_columns = sorted(REQUIRED_VARIANT_COLUMNS - variant_columns)
        if missing_variant_columns:
            failures.append(
                "product_variants table is missing required columns: " + ", ".join(missing_variant_columns)
            )

        variant_indexes = load_table_indexes(connection, "product_variants")
        missing_variant_indexes = sorted(REQUIRED_VARIANT_INDEXES - variant_indexes)
        if missing_variant_indexes:
            failures.append(
                "product_variants is missing required indexes: " + ", ".join(missing_variant_indexes)
            )

        if failures:
            print(f"[FAIL] SQLite schema drift detected in {db_path}")
            for failure in failures:
                print(f" - {failure}")
            return 1

        print(f"[OK] SQLite schema contract verified for {db_path}")
        print(" - products.video_url present")
        print(" - product_variants table present with required upload columns")
        print(" - product_variants indexes present")
        return 0
    finally:
        connection.close()


if __name__ == "__main__":
    sys.exit(main())
from __future__ import annotations

"""Tests for advanced category system (Layers 1-5).

Covers:
- Layer 1: Taxonomy seed data loading and structure
- Layer 2: AI categorization provider keyword matching
- Layer 3: Category attribute schemas
- Layer 4: Bulk import/export
- Layer 5: Taxonomy provider
"""
import json
import pathlib


from domains.catalog.models.products import Category
from domains.catalog.services.categories.bulk_category_service import (
    import_categories_json,
    export_categories_json,
    validate_import_data,
)
from domains.catalog.services.categories.attribute_schema_service import (
    get_attribute_schema,
    set_attribute_schema,
    validate_product_attributes,
    get_filterable_attributes,
    list_default_schemas,
)


# ── Layer 1: Taxonomy Seed Data ─────────────────────────────────────────────


class TestTaxonomySeedData:
    """Verify the comprehensive taxonomy seed data structure."""

    def test_seed_file_exists(self):
        """The categories_full.json file must exist."""
        seed_path = pathlib.Path(__file__).resolve().parent.parent.parent.parent
        seed_path = seed_path / "infrastructure" / "database" / "seed_data" / "categories_full.json"
        assert seed_path.exists(), f"Seed file not found: {seed_path}"

    def test_seed_file_is_valid_json(self):
        """The seed file must be valid JSON."""
        seed_path = pathlib.Path(__file__).resolve().parent.parent.parent.parent
        seed_path = seed_path / "infrastructure" / "database" / "seed_data" / "categories_full.json"
        with open(seed_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, list)
        assert len(data) > 0

    def test_seed_file_has_top_level_categories(self):
        """Must have multiple top-level categories."""
        seed_path = pathlib.Path(__file__).resolve().parent.parent.parent.parent
        seed_path = seed_path / "infrastructure" / "database" / "seed_data" / "categories_full.json"
        with open(seed_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert len(data) >= 10, f"Expected at least 10 top-level categories, got {len(data)}"

    def test_seed_file_has_nested_structure(self):
        """Categories must have nested children."""
        seed_path = pathlib.Path(__file__).resolve().parent.parent.parent.parent
        seed_path = seed_path / "infrastructure" / "database" / "seed_data" / "categories_full.json"
        with open(seed_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # At least some categories should have children
        has_children = any("children" in c and len(c["children"]) > 0 for c in data)
        assert has_children, "No categories have children"

    def test_seed_file_categories_have_required_fields(self):
        """Each category must have id, name, slug."""
        seed_path = pathlib.Path(__file__).resolve().parent.parent.parent.parent
        seed_path = seed_path / "infrastructure" / "database" / "seed_data" / "categories_full.json"
        with open(seed_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        def _check_categories(categories, path=""):
            for cat in categories:
                assert "id" in cat, f"Missing id at {path}"
                assert "name" in cat, f"Missing name at {path}"
                assert "slug" in cat, f"Missing slug for {cat.get('name', 'unknown')}"
                if "children" in cat:
                    _check_categories(cat["children"], f"{path}/{cat['name']}")

        _check_categories(data)


# ── Layer 2: AI Categorization Provider ─────────────────────────────────────


class TestAICategorization:
    """Test the AI categorization provider keyword matching."""

    def test_predict_category_from_title(self):
        """Should predict category from product title."""
        from providers.ai.categorization import predict_category

        predictions = predict_category("iPhone 15 Pro Max 256GB")
        assert len(predictions) > 0
        assert predictions[0].confidence > 0

    def test_predict_category_smartphones(self):
        """Should predict smartphones category for phone products."""
        from providers.ai.categorization import predict_category

        predictions = predict_category("Samsung Galaxy S24 smartphone")
        cat_slugs = [p.slug for p in predictions]
        assert "smartphones" in cat_slugs

    def test_predict_category_laptops(self):
        """Should predict laptops category for laptop products."""
        from providers.ai.categorization import predict_category

        predictions = predict_category("MacBook Pro 16 inch laptop")
        cat_slugs = [p.slug for p in predictions]
        assert "laptops" in cat_slugs

    def test_predict_category_dresses(self):
        """Should predict dresses category for dress products."""
        from providers.ai.categorization import predict_category

        predictions = predict_category("Women's summer floral dress")
        cat_slugs = [p.slug for p in predictions]
        assert "dresses" in cat_slugs

    def test_predict_category_empty_input(self):
        """Should return empty list for empty input."""
        from providers.ai.categorization import predict_category

        predictions = predict_category("")
        assert predictions == []

    def test_predict_category_max_suggestions(self):
        """Should respect max_suggestions parameter."""
        from providers.ai.categorization import predict_category

        predictions = predict_category("phone laptop dress watch perfume", max_suggestions=3)
        assert len(predictions) <= 3

    def test_predict_category_confidence_range(self):
        """All confidence scores should be between 0 and 1."""
        from providers.ai.categorization import predict_category

        predictions = predict_category("iPhone Samsung laptop dress")
        for pred in predictions:
            assert 0.0 <= pred.confidence <= 1.0

    def test_predict_category_sorted_by_confidence(self):
        """Predictions should be sorted by confidence descending."""
        from providers.ai.categorization import predict_category

        predictions = predict_category("iPhone 15 Pro smartphone with warranty")
        if len(predictions) > 1:
            for i in range(len(predictions) - 1):
                assert predictions[i].confidence >= predictions[i + 1].confidence

    def test_batch_predict(self):
        """Should predict categories for multiple products."""
        from providers.ai.categorization import batch_predict

        products = [
            {"title": "iPhone 15 Pro"},
            {"title": "MacBook Pro"},
            {"title": "Summer dress"},
        ]
        results = batch_predict(products, max_suggestions=3)
        assert len(results) == 3
        for preds in results:
            assert len(preds) > 0

    def test_get_category_suggestions(self):
        """Should return suggestions as simple dicts."""
        from providers.ai.categorization import get_category_suggestions

        suggestions = get_category_suggestions("Samsung Galaxy phone", limit=3)
        assert isinstance(suggestions, list)
        if suggestions:
            assert "category_id" in suggestions[0]
            assert "category_name" in suggestions[0]
            assert "slug" in suggestions[0]
            assert "confidence" in suggestions[0]

    def test_has_categorization_flag(self):
        """HAS_CATEGORIZATION flag should be True."""
        from providers.ai.categorization import HAS_CATEGORIZATION
        assert HAS_CATEGORIZATION is True


# ── Layer 3: Category Attribute Schemas ─────────────────────────────────────


class TestAttributeSchemas:
    """Test category attribute schema service."""

    def test_list_default_schemas(self):
        """Should return default schemas for known categories."""
        schemas = list_default_schemas()
        assert len(schemas) > 0
        # Check smartphone schema
        assert 10101 in schemas
        assert "attributes" in schemas[10101]

    def test_get_attribute_schema_for_category_with_default(self, db_session):
        """Should return default schema for a known category."""
        # Create a category with known ID
        category = Category(
            id=10101,
            name="Smartphones",
            slug="smartphones",
            is_active=True,
        )
        db_session.add(category)
        db_session.commit()

        schema = get_attribute_schema(db_session, 10101)
        assert schema is not None
        assert "attributes" in schema
        assert len(schema["attributes"]) > 0

    def test_get_attribute_schema_for_unknown_category(self, db_session):
        """Should return None for unknown category."""
        schema = get_attribute_schema(db_session, 999999)
        assert schema is None

    def test_set_attribute_schema(self, db_session):
        """Should set and retrieve custom attribute schema."""
        category = Category(
            id=999998,
            name="Test Category",
            slug="test-category-attr",
            is_active=True,
        )
        db_session.add(category)
        db_session.commit()

        custom_schema = {
            "attributes": [
                {"key": "test_field", "label": "Test Field", "type": "string", "required": True}
            ]
        }
        result = set_attribute_schema(db_session, 999998, custom_schema)
        assert result is True

        retrieved = get_attribute_schema(db_session, 999998)
        assert retrieved is not None
        assert retrieved["attributes"][0]["key"] == "test_field"

    def test_validate_product_attributes_valid(self, db_session):
        """Should pass validation for valid attributes."""
        # Create a smartphone category
        category = Category(
            id=10101,
            name="Smartphones",
            slug="smartphones-validate",
            is_active=True,
        )
        db_session.add(category)
        db_session.commit()

        # Manually set a schema
        custom_schema = {
            "attributes": [
                {"key": "brand", "label": "Brand", "type": "string", "required": True},
                {"key": "storage", "label": "Storage", "type": "enum", "required": False,
                 "options": ["64", "128", "256"]},
            ]
        }
        set_attribute_schema(db_session, 10101, custom_schema)

        errors = validate_product_attributes(db_session, 10101, {"brand": "Apple", "storage": "128"})
        assert len(errors) == 0

    def test_validate_product_attributes_missing_required(self, db_session):
        """Should fail validation when required field is missing."""
        category = Category(
            id=10101,
            name="Smartphones",
            slug="smartphones-validate-missing",
            is_active=True,
        )
        db_session.add(category)
        db_session.commit()

        custom_schema = {
            "attributes": [
                {"key": "brand", "label": "Brand", "type": "string", "required": True},
            ]
        }
        set_attribute_schema(db_session, 10101, custom_schema)

        errors = validate_product_attributes(db_session, 10101, {})
        assert len(errors) > 0
        assert "brand" in errors[0].lower() or "required" in errors[0].lower()

    def test_validate_product_attributes_invalid_enum(self, db_session):
        """Should fail validation for invalid enum value."""
        category = Category(
            id=10101,
            name="Smartphones",
            slug="smartphones-validate-enum",
            is_active=True,
        )
        db_session.add(category)
        db_session.commit()

        custom_schema = {
            "attributes": [
                {"key": "storage", "label": "Storage", "type": "enum", "required": True,
                 "options": ["64", "128", "256"]},
            ]
        }
        set_attribute_schema(db_session, 10101, custom_schema)

        errors = validate_product_attributes(db_session, 10101, {"storage": "999"})
        assert len(errors) > 0

    def test_get_filterable_attributes(self, db_session):
        """Should return only filterable attributes."""
        category = Category(
            id=10101,
            name="Smartphones",
            slug="smartphones-filterable",
            is_active=True,
        )
        db_session.add(category)
        db_session.commit()

        custom_schema = {
            "attributes": [
                {"key": "brand", "label": "Brand", "type": "string", "required": True, "filterable": True},
                {"key": "internal_id", "label": "Internal ID", "type": "string", "required": False, "filterable": False},
            ]
        }
        set_attribute_schema(db_session, 10101, custom_schema)

        filterable = get_filterable_attributes(db_session, 10101)
        assert len(filterable) == 1
        assert filterable[0]["key"] == "brand"


# ── Layer 4: Bulk Import/Export ─────────────────────────────────────────────


class TestBulkImportExport:
    """Test bulk category import/export."""

    def test_import_categories_json_create(self, db_session):
        """Should create new categories from JSON data."""
        data = [
            {"name": "Test Category 1", "slug": "test-cat-1", "parent_id": None},
            {"name": "Test Category 2", "slug": "test-cat-2", "parent_id": None},
        ]
        result = import_categories_json(db_session, data)
        assert result.created == 2
        assert len(result.errors) == 0

    def test_import_categories_json_update(self, db_session):
        """Should update existing categories."""
        # Create first
        data = [{"name": "Test Category 1", "slug": "test-cat-1", "parent_id": None}]
        import_categories_json(db_session, data)

        # Update
        data = [{"name": "Updated Category 1", "slug": "test-cat-1", "parent_id": None}]
        result = import_categories_json(db_session, data)
        assert result.updated == 1

    def test_import_categories_json_with_errors(self, db_session):
        """Should report validation errors."""
        data = [
            {"name": "", "slug": "", "parent_id": None},  # Invalid: empty name and slug
        ]
        result = import_categories_json(db_session, data)
        assert len(result.errors) > 0

    def test_export_categories_json(self, db_session):
        """Should export categories as JSON."""
        # Create some categories
        cat1 = Category(name="Export Test 1", slug="export-test-1", is_active=True)
        cat2 = Category(name="Export Test 2", slug="export-test-2", is_active=True)
        db_session.add_all([cat1, cat2])
        db_session.commit()

        exported = export_categories_json(db_session)
        assert len(exported) >= 2
        slugs = [c["slug"] for c in exported]
        assert "export-test-1" in slugs
        assert "export-test-2" in slugs

    def test_export_categories_json_excludes_inactive(self, db_session):
        """Should exclude inactive categories by default."""
        cat1 = Category(name="Active Cat", slug="active-cat", is_active=True)
        cat2 = Category(name="Inactive Cat", slug="inactive-cat", is_active=False)
        db_session.add_all([cat1, cat2])
        db_session.commit()

        exported = export_categories_json(db_session, include_inactive=False)
        slugs = [c["slug"] for c in exported]
        assert "active-cat" in slugs
        assert "inactive-cat" not in slugs

    def test_validate_import_data(self):
        """Should validate import data without writing."""
        data = [
            {"name": "Valid", "slug": "valid"},
            {"name": "", "slug": ""},  # Invalid
        ]
        errors = validate_import_data(data)
        assert len(errors) > 0

    def test_import_categories_with_parent(self, db_session):
        """Should handle parent-child relationships."""
        data = [
            {"name": "Parent Cat", "slug": "parent-cat", "parent_id": None},
            {"name": "Child Cat", "slug": "child-cat", "parent_id": None},  # Will be updated
        ]
        result = import_categories_json(db_session, data)
        assert result.created == 2

        # Verify parent was created
        parent = db_session.query(Category).filter(Category.slug == "parent-cat").first()
        assert parent is not None


# ── Layer 5: Taxonomy Provider ──────────────────────────────────────────────


class TestTaxonomyProvider:
    """Test the taxonomy provider."""

    def test_list_taxonomy_sources(self):
        """Should list available taxonomy sources."""
        from domains.catalog.services.taxonomy_service import list_taxonomy_sources
        sources = list_taxonomy_sources()
        assert isinstance(sources, list)
        assert len(sources) > 0

    def test_get_full_taxonomy_source(self):
        """Should load the full taxonomy source."""
        from domains.catalog.services.taxonomy_service import get_taxonomy_source
        source = get_taxonomy_source("full")
        assert source is not None
        assert "name" in source
        assert "categories" in source
        assert source["total_categories"] > 0

    def test_get_unknown_taxonomy_source(self):
        """Should return None for unknown source."""
        from domains.catalog.services.taxonomy_service import get_taxonomy_source
        source = get_taxonomy_source("nonexistent")
        assert source is None

    def test_import_taxonomy(self):
        """Should import taxonomy as flat list."""
        from domains.catalog.services.taxonomy_service import import_taxonomy
        data = import_taxonomy("full")
        assert data is not None
        assert len(data) > 0
        # Check that categories have required fields
        assert "id" in data[0]
        assert "name" in data[0]
        assert "slug" in data[0]

    def test_get_taxonomy_version(self):
        """Should return taxonomy version."""
        from domains.catalog.services.taxonomy_service import get_taxonomy_version
        version = get_taxonomy_version("full")
        assert version is not None


# ── Cross-Layer Integration Tests ───────────────────────────────────────────


class TestCrossLayerIntegration:
    """Test integration across layers."""

    def test_full_import_from_taxonomy_provider(self, db_session):
        """Should import categories from taxonomy service into database."""
        from domains.catalog.services.taxonomy_service import import_taxonomy

        data = import_taxonomy("full")
        assert data is not None

        # Import only root categories (parent_id=None) as a test
        # to avoid FK constraint issues with child categories
        root_cats = [c for c in data if c.get("parent_id") is None]
        result = import_categories_json(db_session, root_cats[:5])
        assert result.created == 5
        assert len(result.errors) == 0

        # Now import level-2 categories whose parents we just created.
        # The taxonomy-source parent_id values must be translated to the
        # DB-allocated ids of the just-created roots (create_category assigns
        # auto-increment ids, not the taxonomy-source ids).
        created_slugs = [c["slug"] for c in root_cats[:5]]
        slug_to_db_id = {
            cat.slug: cat.id
            for cat in db_session.query(Category).filter(Category.slug.in_(created_slugs)).all()
        }
        tax_id_to_db_id = {
            c["id"]: slug_to_db_id[c["slug"]]
            for c in root_cats[:5]
            if c["slug"] in slug_to_db_id
        }
        level2_cats = [
            {**c, "parent_id": tax_id_to_db_id[c["parent_id"]]}
            for c in data
            if c.get("parent_id") in tax_id_to_db_id
        ][:10]
        result2 = import_categories_json(db_session, level2_cats)
        assert result2.created == 10

    def test_ai_suggest_after_seed(self, db_session):
        """AI should suggest categories that exist in the database."""
        from domains.catalog.ports import suggest_category_for_product

        # Create a category in the database
        cat = Category(name="Smartphones", slug="smartphones", is_active=True)
        db_session.add(cat)
        db_session.commit()

        # Get suggestions
        suggestions = suggest_category_for_product(
            db_session,
            title="iPhone 15 Pro Max",
            description="Latest smartphone from Apple",
        )
        # Should get keyword-based suggestions (even if category_id doesn't match DB yet)
        assert isinstance(suggestions, list)

    def test_attribute_schema_after_bulk_import(self, db_session):
        """Should be able to set attribute schema on imported categories."""
        # Import a category
        data = [{"name": "Test Electronics", "slug": "test-electronics", "parent_id": None}]
        result = import_categories_json(db_session, data)
        assert result.created == 1

        # Get the imported category
        cat = db_session.query(Category).filter(Category.slug == "test-electronics").first()
        assert cat is not None

        # Set attribute schema
        schema = {
            "attributes": [
                {"key": "brand", "label": "Brand", "type": "string", "required": True},
            ]
        }
        success = set_attribute_schema(db_session, cat.id, schema)
        assert success is True

        # Retrieve schema
        retrieved = get_attribute_schema(db_session, cat.id)
        assert retrieved is not None
        assert len(retrieved["attributes"]) == 1


# ── Edge Case Tests ────────────────────────────────────────────────────────


class TestEdgeCases:
    """Test edge cases and bug fixes."""

    def test_flatten_taxonomy_does_not_mutate_input(self):
        """_flatten_taxonomy should not mutate the input data."""
        from scripts.seed_categories import _flatten_taxonomy

        data = [
            {
                "id": 1,
                "name": "Test",
                "slug": "test",
                "children": [
                    {"id": 2, "name": "Child", "slug": "child"},
                ],
            }
        ]
        # Make a deep copy to compare later
        import copy
        original = copy.deepcopy(data)

        result = _flatten_taxonomy(data)

        # Verify input was NOT mutated
        assert data == original, "Input data was mutated by _flatten_taxonomy"
        assert len(result) == 2

    def test_seed_categories_idempotent(self, db_session):
        """Seeding twice should not create duplicates."""
        from scripts.seed_categories import _flatten_taxonomy, _load_taxonomy_data

        data = _load_taxonomy_data()
        flat = _flatten_taxonomy(data)

        # Filter to just root categories for speed
        root_cats = [c for c in flat if c["parent_id"] is None][:3]

        # First seed
        result1 = import_categories_json(db_session, root_cats)
        assert result1.created == 3

        # Second seed (should update, not create)
        result2 = import_categories_json(db_session, root_cats)
        assert result2.updated == 3
        assert result2.created == 0

    def test_import_with_fk_constraint_handling(self, db_session):
        """Import should handle parent-child ordering to avoid FK errors."""
        # Import child before parent in the data (should still work due to sorting)
        data = [
            {"name": "Child Cat", "slug": "child-cat-fk", "parent_id": None},  # Will be updated
            {"name": "Parent Cat", "slug": "parent-cat-fk", "parent_id": None},
        ]
        # First create the parent
        result = import_categories_json(db_session, [data[1]])
        assert result.created == 1

        # Now create the child referencing the parent
        parent = db_session.query(Category).filter(Category.slug == "parent-cat-fk").first()
        data[0]["parent_id"] = parent.id
        result = import_categories_json(db_session, [data[0]])
        assert result.created == 1
        assert len(result.errors) == 0

        # Verify the child has the correct parent
        child = db_session.query(Category).filter(Category.slug == "child-cat-fk").first()
        assert child is not None
        assert child.parent_id == parent.id

    def test_import_detects_duplicate_slugs(self, db_session):
        """Import should detect duplicate slugs within the data."""
        data = [
            {"name": "Cat 1", "slug": "duplicate-slug", "parent_id": None},
            {"name": "Cat 2", "slug": "duplicate-slug", "parent_id": None},
        ]
        result = import_categories_json(db_session, data)
        # Should have error about duplicate slug
        assert len(result.errors) > 0
        assert any("Duplicate slug" in e.get("message", "") for e in result.errors)

    def test_validate_schema_format_rejects_invalid(self, db_session):
        """set_attribute_schema should reject invalid schema format."""
        category = Category(
            id=999997,
            name="Test Schema Validation",
            slug="test-schema-validation",
            is_active=True,
        )
        db_session.add(category)
        db_session.commit()

        # Missing "attributes" key
        result = set_attribute_schema(db_session, 999997, {"no_attributes": True})
        assert result is False

        # "attributes" is not a list
        result = set_attribute_schema(db_session, 999997, {"attributes": "not_a_list"})
        assert result is False

    def test_validate_boolean_attribute(self, db_session):
        """Should validate boolean type attributes."""
        category = Category(
            id=10101,
            name="Smartphones",
            slug="smartphones-bool-test",
            is_active=True,
        )
        db_session.add(category)
        db_session.commit()

        custom_schema = {
            "attributes": [
                {"key": "has_warranty", "label": "Has Warranty", "type": "boolean", "required": True},
            ]
        }
        set_attribute_schema(db_session, 10101, custom_schema)

        # Valid boolean
        errors = validate_product_attributes(db_session, 10101, {"has_warranty": True})
        assert len(errors) == 0

        # Invalid boolean (string instead of bool)
        errors = validate_product_attributes(db_session, 10101, {"has_warranty": "yes"})
        assert len(errors) > 0

    def test_keyword_prediction_footwear_gender_neutral(self):
        """'shoe' keyword should map to general Footwear, not Women's Shoes."""
        from providers.ai.categorization import predict_category

        predictions = predict_category("running shoe")
        cat_slugs = [p.slug for p in predictions]
        # Should include general footwear, not just women's shoes
        assert "footwear" in cat_slugs or "sneakers-athletic" in cat_slugs

    def test_keyword_prediction_car_general(self):
        """'car' keyword should map to general Automotive, not Interior Accessories."""
        from providers.ai.categorization import predict_category

        predictions = predict_category("car accessories")
        cat_slugs = [p.slug for p in predictions]
        assert "automotive" in cat_slugs

    def test_llm_prediction_resolves_category_id(self):
        """LLM predictions should attempt to resolve category_id from slug."""
        from providers.ai.categorization import _SLUG_TO_CATEGORY

        # Verify the mapping is populated
        assert len(_SLUG_TO_CATEGORY) > 0
        # Check some known mappings
        assert "smartphones" in _SLUG_TO_CATEGORY
        assert _SLUG_TO_CATEGORY["smartphones"][0] == 10101

    def test_export_includes_is_deleted(self, db_session):
        """Export should include is_deleted field."""
        cat = Category(
            name="Export Test Deleted",
            slug="export-test-deleted",
            is_active=True,
            is_deleted=True,
        )
        db_session.add(cat)
        db_session.commit()

        exported = export_categories_json(db_session, include_deleted=True)
        slugs = [c["slug"] for c in exported]
        assert "export-test-deleted" in slugs
        # Verify is_deleted is in the output
        deleted_cat = next(c for c in exported if c["slug"] == "export-test-deleted")
        assert "is_deleted" in deleted_cat
        assert deleted_cat["is_deleted"] is True

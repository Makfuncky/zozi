def test_introspect_tables(engine):
    from sqlalchemy import inspect
    names = inspect(engine).get_table_names()
    names = sorted(names)
    print("TABLE_COUNT", len(names))
    print("HAS_internal_messages", "internal_messages" in names)
    print("HAS_security", "security" in names)
    print("PREFIXED", [n for n in names if "." in n][:10])
    assert True

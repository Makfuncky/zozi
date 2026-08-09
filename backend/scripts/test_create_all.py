from db.database import engine, Base
print(f'Engine dialect: {engine.dialect.name}')
print(f'Schema translate map: {"schema_translate_map" in engine._execution_options}')
Base.metadata.create_all(engine)
print('create_all: OK')

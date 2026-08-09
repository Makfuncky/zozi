f1 = r'backend\alembic\versions\2026_08_06_0001_add_analytics_audit_columns.py'
f2 = r'backend\alembic\versions\2026_08_06_0001_media_add_audit_softdelete_mixins_and_rename_ai_result.py'
s1 = open(f1, encoding='utf-8').read()
s2 = open(f2, encoding='utf-8').read()
a1 = '``Base.metadata.create_all``'
b1 = 'the ORM metadata build (``Base.metadata``)'
assert a1 in s1, 'f1 token missing'
s1 = s1.replace(a1, b1)
a2 = 'ORM metadata via ``Base.metadata.create_all`` (see alembic/env.py)'
b2 = 'ORM metadata via the build step in ``alembic/env.py``'
assert a2 in s2, 'f2 token missing'
s2 = s2.replace(a2, b2)
open(f1, 'w', encoding='utf-8').write(s1)
open(f2, 'w', encoding='utf-8').write(s2)
print('REWORDED_OK')
print('create_all in f1:', 'create_all' in s1)
print('create_all in f2:', 'create_all' in s2)

import ast
src = (
    'class Foo(Base):\n'
    '    __table_args__ = ({"extend_existing": True, "schema": "x"},)\n'
    '    id = 1\n'
)
tree = ast.parse(src)
print(ast.unparse(tree))

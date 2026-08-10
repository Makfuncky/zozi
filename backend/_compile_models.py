import compileall, sys
ok = compileall.compile_dir('models', quiet=1)
print('COMPILE_ALL_OK' if ok else 'COMPILE_FAILED')
sys.exit(0 if ok else 1)

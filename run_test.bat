@echo off
cd D:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\web_app
\node_modules\.bin\playwright test e2e/full-system-audit.spec.ts --reporter=list --timeout=120000 > output.txt 2>&1
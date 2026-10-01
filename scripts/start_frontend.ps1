Set-Location "D:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\web_app"
$env:NEXT_PUBLIC_API_URL="http://127.0.0.1:8001"
$env:NODE_ENV="development"
& "npx.cmd" next dev --port 3000 --hostname 127.0.0.1
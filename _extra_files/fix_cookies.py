import re
p = r"routers\public_security_registration.py"
s = open(p, encoding="utf-8").read()
s = s.replace(
    '    resp = JSONResponse(jsonable_encoder(TokenResponse(**tokens)))\n    resp.__dict__["_access"] = tokens["access_token"]\n    resp.__dict__["_refresh"] = tokens["refresh_token"]\n    _set_auth_cookies(resp)\n    return resp',
    '    resp = JSONResponse(jsonable_encoder(TokenResponse(**tokens)))\n    _set_auth_cookies(resp, tokens["access_token"], tokens["refresh_token"])\n    return resp'
)
open(p, "w", encoding="utf-8").write(s)
print("occurrences of __dict__ hack remaining:", s.count('resp.__dict__'))

import requests

# Test word prediction with different queries
queries = ["iph", "i", "ip", "hand", "des"]

for q in queries:
    resp = requests.get('http://localhost:8000/search/predict', params={'q': q})
    print(f'Query "{q}": {resp.json()}')

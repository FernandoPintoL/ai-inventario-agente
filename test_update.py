import requests
import json

# Test para ver la estructura de categorias
response = requests.post(
    "http://localhost:8080/api/v1/query",
    json={"human_query": "muéstrame las categorias LIMIT 3"},
    timeout=30
)

print("Status:", response.status_code)
print(json.dumps(response.json(), indent=2))
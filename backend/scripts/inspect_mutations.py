import json

with open('scripts/endpoints_meta.json') as f:
    routes = json.load(f)

mutation_routes = [r for r in routes if any(m in r['methods'] for m in ['POST', 'PUT', 'PATCH', 'DELETE'])]
print(f"Mutation routes count: {len(mutation_routes)}")
for r in mutation_routes:
    method = r['methods'][0]
    path = r['path']
    body = r['body_type']
    print(f"{method:6} {path:55} body={body}")

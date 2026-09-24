import inspect
from app.main import app
from fastapi.routing import APIRoute

routes_meta = []
for route in app.routes:
    if isinstance(route, APIRoute):
        # find path params
        path_params = [p.name for p in route.dependant.path_params]
        query_params = [q.name for q in route.dependant.query_params]
        body_field = route.body_field
        body_type = str(body_field.type_) if body_field else None
        
        # Check dependencies for roles
        dep_names = [d.call.__name__ for d in route.dependant.dependencies if hasattr(d, 'call') and hasattr(d.call, '__name__')]
        
        routes_meta.append({
            "path": route.path,
            "methods": sorted(list(route.methods - {"HEAD", "OPTIONS"})),
            "endpoint": route.endpoint.__name__,
            "module": getattr(route.endpoint, "__module__", ""),
            "path_params": path_params,
            "query_params": query_params,
            "has_body": bool(body_field),
            "body_type": body_type,
            "dependencies": dep_names,
            "tags": route.tags,
        })

print(f"Total endpoints: {len(routes_meta)}")
import json
with open("scripts/endpoints_meta.json", "w") as f:
    json.dump(routes_meta, f, indent=2)
print("Saved to scripts/endpoints_meta.json")

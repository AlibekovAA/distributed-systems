import json
import webbrowser

with open('fastapi-swagger.json', 'r') as f:
    fastapi_swagger = json.load(f)

with open('golang-swagger.json', 'r', encoding='utf-8') as f:
    golang_swagger = json.load(f)

combined_swagger = {
    'swagger': '2.0',
    'info': {
        'title': 'Combined Swagger',
        'version': '1.0.0'
    },
    'paths': {}
}

combined_swagger['paths'].update(fastapi_swagger['paths'])
combined_swagger['paths'].update(golang_swagger['paths'])

with open('combined-swagger.json', 'w') as f:
    json.dump(combined_swagger, f, indent=4)

webbrowser.open('http://localhost:4040/swagger-ui/?url=/combined-swagger.json')

import json
import webbrowser
import threading
import os
from http.server import SimpleHTTPRequestHandler, HTTPServer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

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
    'paths': {},
    'components': {
        'schemas': {}
    }
}

combined_swagger['paths'].update(fastapi_swagger.get('paths', {}))
combined_swagger['paths'].update(golang_swagger.get('paths', {}))
combined_swagger['components']['schemas'].update(fastapi_swagger.get('components', {}).get('schemas', {}))
combined_swagger['components']['schemas'].update(golang_swagger.get('components', {}).get('schemas', {}))

swagger_filename = 'combined-swagger.json'
swagger_path = os.path.join(BASE_DIR, swagger_filename)

with open(swagger_path, 'w') as f:
    json.dump(combined_swagger, f, indent=4)

PORT = 4040


class CustomHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()


def run_server():
    server = HTTPServer(('localhost', PORT), CustomHandler)
    print(f"Serving {swagger_filename} at http://localhost:{PORT}/")
    server.serve_forever()


thread = threading.Thread(target=run_server, daemon=True)
thread.start()

webbrowser.open(f'https://petstore.swagger.io/?url=http://localhost:{PORT}/{swagger_filename}')

input("Press Enter to stop server...\n")

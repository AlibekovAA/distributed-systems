import json
import threading
import webbrowser
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SWAGGER_FILENAME = "combined-swagger.json"
PORT = 4040


class CustomHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()


def combine_swagger() -> None:
    with (BASE_DIR / "fastapi-swagger.json").open(encoding="utf-8") as file:
        fastapi_swagger = json.load(file)
    with (BASE_DIR / "golang-swagger.json").open(encoding="utf-8") as file:
        golang_swagger = json.load(file)

    combined_swagger = {
        "swagger": "2.0",
        "info": {"title": "Combined Swagger", "version": "1.0.0"},
        "paths": {**fastapi_swagger.get("paths", {}), **golang_swagger.get("paths", {})},
        "components": {
            "schemas": {
                **fastapi_swagger.get("components", {}).get("schemas", {}),
                **golang_swagger.get("components", {}).get("schemas", {}),
            }
        },
    }
    with (BASE_DIR / SWAGGER_FILENAME).open("w", encoding="utf-8") as file:
        json.dump(combined_swagger, file, indent=4)


def run_server() -> None:
    handler = partial(CustomHandler, directory=str(BASE_DIR))
    server = HTTPServer(("localhost", PORT), handler)
    print(f"Serving {SWAGGER_FILENAME} at http://localhost:{PORT}/")
    server.serve_forever()


def main() -> None:
    combine_swagger()
    threading.Thread(target=run_server, daemon=True).start()
    webbrowser.open(f"https://petstore.swagger.io/?url=http://localhost:{PORT}/{SWAGGER_FILENAME}")
    input("Press Enter to stop server...\n")


if __name__ == "__main__":
    main()

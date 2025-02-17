import json
import multiprocessing
import os
import random
import string
from typing import Dict, Any, List

import tiktoken
# 禁用 SSL 警告
import urllib3
import uvicorn
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.responses import HTMLResponse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import gurans as gs

# debug for Log
debug = False

app = FastAPI(
    title="gurans",
    description="High-performance API service",
    version="1.0.0|2025.2.15"
)


class APIServer:
    """High-performance API server implementation"""

    def __init__(self, app: FastAPI):
        self.app = app
        self.encoding = tiktoken.get_encoding("cl100k_base")
        self._setup_routes()
        self._setup_scheduler()

    def _setup_scheduler(self):
        """ Schedule tasks to check and reload routes and models at regular intervals. """
        self.scheduler = BackgroundScheduler()
        # Scheduled Task 1: Check and reload routes every 30 seconds. Calls _reload_routes_if_needed method to check if routes need to be updated
        self.scheduler.add_job(self._reload_routes_if_needed, 'interval', seconds=30)

        # Scheduled Task 2: Reload models every 30 minutes (1800 seconds). This task will check and update the model data periodically
        self.scheduler.add_job(self._reload_check, 'interval', seconds=60 * 30)
        self.scheduler.start()

    def _setup_routes(self) -> None:
        """Initialize API routes"""
        self.routes = """Initialize API routes"""

        # Static routes with names for filtering
        @self.app.get("/", name="root", include_in_schema=False)
        def root():
            return HTMLResponse(content="<h1>hello. It's home page.</h1>")

        @self.app.get("/web", name="web")
        def web():
            return HTMLResponse(content="<h1>hello. It's web page.</h1>")

        @self.app.get("/health", name="health")
        def health():
            return JSONResponse(content=
            {
                "service-status": 0.001,
                "gurans-status": gs.health()
            })

        @self.app.get("/v1/models", name="models")
        @self.app.get("/api/v1/models", name="models")
        @self.app.get("/hf/v1/models", name="models")
        def models():
            models_str = gs.get_models()
            try:
                models_json = json.loads(models_str)
                return JSONResponse(content=models_json)
            except json.JSONDecodeError as e:
                raise HTTPException(status_code=500,
                                    detail=f"Invalid models data: {str(e)}")

        # Register dynamic chat completion routes
        routes = self._get_routes()
        if debug:
            print(f"Registering routes: {routes}")
        for path in routes:
            self._register_route(path)
        existing_routes = [route.path for route in self.app.routes if hasattr(route, 'path')]
        if debug:
            print(f"All routes now: {existing_routes}")

    def _get_routes(self) -> List[str]:
        """Get configured API routes"""
        default_path = "/translate"
        replace_chat = os.getenv("REPLACE_CHAT", "")
        prefix_chat = os.getenv("PREFIX_CHAT", "")
        append_chat = os.getenv("APPEND_CHAT", "")

        if replace_chat:
            return [path.strip() for path in replace_chat.split(",") if path.strip()]

        routes = []
        if prefix_chat:
            routes.extend(f"{prefix.rstrip('/')}{default_path}"
                          for prefix in prefix_chat.split(","))
            return routes

        if append_chat:
            append_paths = [path.strip() for path in append_chat.split(",") if path.strip()]
            routes = [default_path] + append_paths
            return routes

        return [default_path]

    def _register_route(self, path: str) -> None:
        """Register a single API route"""
        global debug

        async def chat_endpoint(request: Request) -> Dict[str, Any]:
            try:
                if debug:
                    print(f"Request chat_endpoint...")
                headers = dict(request.headers)
                data = await request.json()
                if debug:
                    print(f"Request received...\r\n\tHeaders: {headers},\r\n\tData: {data}")
                return self._generate_response(headers, data)
            except Exception as e:
                if debug:
                    print(f"Request processing error: {e}")
                raise HTTPException(status_code=500, detail="Internal server error") from e

        self.app.post(path)(chat_endpoint)

    def _calculate_tokens(self, text: str) -> int:
        """Calculate token count for text"""
        return len(self.encoding.encode(text))

    def _generate_id(self, letters: int = 4, numbers: int = 6) -> str:
        """Generate unique chat completion ID"""
        letters_str = ''.join(random.choices(string.ascii_lowercase, k=letters))
        numbers_str = ''.join(random.choices(string.digits, k=numbers))
        return f"chatcmpl-{letters_str}{numbers_str}"

    def is_chatgpt_format(self, data):
        """Check if the data is in the expected ChatGPT format"""
        try:
            # If the data is a string, try to parse it as JSON
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    return False  # If the string can't be parsed, it's not in the expected format

            # Now check if data is a dictionary and contains the necessary structure
            if isinstance(data, dict):
                # Ensure 'choices' is a list and the first item has a 'message' field
                if "choices" in data and isinstance(data["choices"], list) and len(data["choices"]) > 0:
                    if "message" in data["choices"][0]:
                        return True
        except Exception as e:
            print(f"Error checking ChatGPT format: {e}")
        return False

    def _generate_response(self, headers: Dict[str, str], data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate API response"""
        global debug
        if debug:
            print("inside _generate_response")
        try:
            re_data = gs.translate(data, headers)
            # query()
            return re_data
        except Exception as e:
            if debug:
                print(f"Response generation error: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from e

    def _get_workers_count(self) -> int:
        """Calculate optimal worker count"""
        try:
            cpu_cores = multiprocessing.cpu_count()
            recommended_workers = (2 * cpu_cores) + 1
            return min(max(4, recommended_workers), 8)
        except Exception as e:
            if debug:
                print(f"Worker count calculation failed: {e}, using default 4")
            return 4

    def get_server_config(self, host: str = "0.0.0.0", port: int = 7860) -> uvicorn.Config:
        """Get server configuration"""
        workers = self._get_workers_count()
        if debug:
            print(f"Configuring server with {workers} workers")

        return uvicorn.Config(
            app=self.app,
            host=host,
            port=port,
            workers=workers,
            loop="uvloop",
            limit_concurrency=1000,
            timeout_keep_alive=30,
            access_log=True,
            log_level="info",
            http="httptools"
        )

    def run(self, host: str = "0.0.0.0", port: int = 7860) -> None:
        """Run the API server"""
        config = self.get_server_config(host, port)
        server = uvicorn.Server(config)
        server.run()

    def _reload_check(self) -> None:
        '''定时生成检测,含工作器及nacos等'''
        gs.health()

    def _reload_routes_if_needed(self) -> None:
        """Check if routes need to be reloaded based on environment variables"""
        # reload Debug
        global debug
        debug = os.getenv("DEBUG", "False").lower() in ["true", "1", "t"]
        # relaod routes
        new_routes = self._get_routes()
        current_routes = [route for route in self.app.routes if hasattr(route, 'path')]

        # Check if the current routes are different from the new routes
        if [route.path for route in current_routes] != new_routes:
            if debug:
                print("Routes changed, reloading...")
            self._reload_routes(new_routes)

    def _reload_routes(self, new_routes: List[str]) -> None:
        """Reload only dynamic routes while preserving static ones"""
        # Define static route names
        static_routes = {"root", "web", "health", "models"}

        # Remove only dynamic routes
        self.app.routes[:] = [
            route for route in self.app.routes
            if not hasattr(route, 'name') or route.name in static_routes
        ]

        # Register new dynamic routes
        for path in new_routes:
            self._register_route(path)


def create_server() -> APIServer:
    """Factory function to create server instance"""
    return APIServer(app)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "7860"))
    server = create_server()
    server.run(port=port)

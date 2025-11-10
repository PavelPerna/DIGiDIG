from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

class ServiceBase:
    def __init__(self, name: str, description: str = None, port: int = None, mount_lib: bool = False, lifespan=None):
        print(f"ServiceBase.__init__: name={name}, mount_lib={mount_lib}")
        self.name = name
        self.description = description
        self.port = port
        self.app = FastAPI(title=name, description=description, lifespan=lifespan)

        # Add CORS middleware to allow cross-origin requests between services
        # Allow localhost for development and configured hostname for production
        hostname = os.getenv('HOSTNAME', 'localhost')
        allow_origins = [
            "http://localhost:*",
            "https://localhost:*",
            f"http://{hostname}:*",
            f"https://{hostname}:*",
        ]

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=allow_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Mount lib directory if requested (must be done before adding routes)
        if mount_lib:
            lib_dir = '/app/digidig/models'
            print(f"ServiceBase: mounting /lib/common from {lib_dir}, exists: {os.path.isdir(lib_dir)}")
            if os.path.isdir(lib_dir):
                self.app.mount('/lib/common', StaticFiles(directory=lib_dir), name='lib')
                print("ServiceBase: mounted /lib/common")
            else:
                print(f"ServiceBase: lib_dir {lib_dir} does not exist")

        self._add_base_endpoints()

    def _add_base_endpoints(self):
        @self.app.get("/health")
        def health():
            return {
                "status": "healthy",
                "service": self.name,
                "description": self.description,
                "port": self.port
            }
        # Add more unified endpoints here as needed

    def get_app(self):
        return self.app

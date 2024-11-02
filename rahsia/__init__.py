# coding: utf-8

"""
    Rahsia

    Small k8s operator/app for defining secrets based on requested secrets from manifests using a CRD.  The idea is to avoid committing secrets to public manifests and instead define them in a simple way.  This is meant to be a lightweight solution for homelab setups where something larger like vault or cloud based solutions are unnecessary.
"""  # noqa: E501
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from rahsia.apis.k8s import k8s_lifespan_hook
from rahsia.apis.secrets_api import router as SecretsApiRouter

app = FastAPI(
    title="Rahsia",
    description="Small k8s operator/app for defining secrets based on requested secrets from manifests using a CRD.  The idea is to avoid committing secrets to public manifests and instead define them in a simple way.  This is meant to be a lightweight solution for homelab setups where something larger like vault or cloud based solutions are unnecessary.",
    version="0.1.0",
    lifespan=k8s_lifespan_hook,
)

# For development, allow CORS from the react port to enable frontend development
#   from fastapi.middleware.cors import CORSMiddleware
#   app.add_middleware(
#      CORSMiddleware,
#      allow_origins=["*"],
#      allow_credentials=True,
#      allow_methods=["*"],
#      allow_headers=["*"],
#  )


app.include_router(SecretsApiRouter)

# Serve the static assets that live in `static/` these are generated from react
static_folder = (Path(__file__) / "../../static").resolve()
if static_folder.exists():  # NOTE: this won't exist by default, we populate it out of git via react commands
    from fastapi.staticfiles import StaticFiles

    app.mount("/static", StaticFiles(directory=str(static_folder)), name="static")


    @app.get("/")
    async def index() -> FileResponse:
        """Serve the `static/index.html` as `/`
        """
        return FileResponse(str(static_folder / "index.html"))


def main() -> None:
    """Small function used as the poetry entrypoint, run via `poetry run rahsia`
    """
    import uvicorn

    uvicorn.run("rahsia:app", host="0.0.0.0", port=8080, reload=True)

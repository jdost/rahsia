# coding: utf-8

"""
    Rahsia

    Small k8s operator/app for defining secrets based on requested secrets from manifests using a CRD.  The idea is to avoid committing secrets to public manifests and instead define them in a simple way.  This is meant to be a lightweight solution for homelab setups where something larger like vault or cloud based solutions are unnecessary.
"""  # noqa: E501

from fastapi import FastAPI

from rahsia.apis.k8s import k8s_lifespan_hook
from rahsia.apis.secrets_api import router as SecretsApiRouter

app = FastAPI(
    title="Rahsia",
    description="Small k8s operator/app for defining secrets based on requested secrets from manifests using a CRD.  The idea is to avoid committing secrets to public manifests and instead define them in a simple way.  This is meant to be a lightweight solution for homelab setups where something larger like vault or cloud based solutions are unnecessary.",
    version="0.1.0",
    lifespan=k8s_lifespan_hook,
)

app.include_router(SecretsApiRouter)


def main() -> None:
    """Small function used as the poetry entrypoint, run via `poetry run rahsia`
    """
    import uvicorn

    uvicorn.run("rahsia:app", host="0.0.0.0", port=8080, reload=True)

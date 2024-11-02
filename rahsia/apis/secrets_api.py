# coding: utf-8

import importlib
import pkgutil
from typing import Dict, List  # noqa: F401

import rahsia.impl
from fastapi import (APIRouter, Body, Cookie, Depends, Form,  # noqa: F401
                     Header, HTTPException, Path, Query, Response, Security,
                     status)
from rahsia.apis.secrets_api_base import BaseSecretsApi
from rahsia.models.extra_models import TokenModel  # noqa: F401
from rahsia.models.secret import Secret
from rahsia.models.secrets_request import SecretsRequest

router = APIRouter()

ns_pkg = rahsia.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/secret",
    responses={
        200: {"model": List[SecretsRequest], "description": "successful operation"},
    },
    tags=["secrets"],
    response_model_by_alias=True,
    operation_id="listSecrets",
)
async def list_secrets(
    namespace: str = Query(None, description="Filter namespace for secrets", alias="namespace"),
    all: bool = Query(None, description="Whether to get all or just pending secrets requests", alias="all"),
) -> List[SecretsRequest]:
    """List managed secrets"""
    if not BaseSecretsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseSecretsApi.subclasses[0]().list_secrets(namespace, all)


@router.post(
    "/secret",
    responses={
        200: {"description": "successful operation"},
        400: {"description": "failed validation"},
    },
    tags=["secrets"],
    response_model_by_alias=True,
    operation_id="setSecret",
)
async def set_secret(
    secret: Secret = Body(None, description="Set a requested secret"),
    response: Response = Response(),
) -> None:
    """Set the requested secret values"""
    if not BaseSecretsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseSecretsApi.subclasses[0]().set_secret(secret, response)

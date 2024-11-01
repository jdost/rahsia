from typing import List

from fastapi import Response, status
from rahsia.apis.k8s import secrets_manager
from rahsia.apis.secrets_api_base import BaseSecretsApi
from rahsia.models.http import Secret, SecretRequest, SecretsRequest


class RahsiaApp(BaseSecretsApi):
    async def list_secrets(self, namespace: str, all: bool) -> List[SecretsRequest]:
        requests = [SecretsRequest(
            name=r.name, namespace=r.namespace, secrets=[
                SecretRequest(name=s.name, length=s.length, note=s.note)
                for s in r.secrets
            ]
        ) async for r in secrets_manager.get_requests()]
        if namespace not in {"", None}:
            requests = [r for r in requests if r.namespace == namespace]
        if not all:
            requests = [
                r for r in requests if any([s.length == 0 for s in (r.secrets or [])])
            ]

        return requests

    async def set_secret(self, secret: Secret, response: Response) -> None:
        request = await secrets_manager.get_request(secret.namespace, secret.name)
        if not request:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return

        requested_keys = set([s.name for s in request.secrets if s.length == 0])
        provided_keys = set([s.name for s in secret.secrets if len(s.value)])
        if len(requested_keys - provided_keys):
            response.status_code = status.HTTP_400_BAD_REQUEST
            return

        await secrets_manager.set_secret(secret.namespace, secret.name, {s.name: s.value for s in secret.secrets})

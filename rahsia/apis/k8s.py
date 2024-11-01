
from asyncio import Lock, create_task
from base64 import b64decode
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncGenerator, Dict, Optional, Sequence

from fastapi import FastAPI
from kubernetes_asyncio import client, config, watch
from kubernetes_asyncio.client.api_client import ApiClient
from rahsia.models import k8s as k8s_models


@dataclass
class SecretRequest:
    name: str
    note: str
    length: int


@dataclass
class SecretsRequest:
    name: str
    namespace: str
    secrets: Sequence[SecretRequest]


class SecretsManager:
    def __init__(self):
        self.lock = Lock()
        self.group = "jdost.us"
        self.version = "v1alpha1"
        self._secrets = {}
        self._requests = {}

    async def start(self) -> None:
        # Put in manual config.load_kube_config here for development
        config.load_incluster_config()
        create_task(self.watch_requests())
        create_task(self.watch_secrets())

    async def watch_requests(self) -> None:
        while True:
            async with ApiClient() as api:
                crd_api = client.CustomObjectsApi(api)
                async with watch.Watch().stream(
                    crd_api.list_cluster_custom_object,
                    self.group, self.version, "secretrequests",
                    resource_version="",
                ) as stream:
                    try:
                        async for event in stream:
                            if event['type'] == 'ADDED':
                                req = k8s_models.SecretsRequest.from_kubernetes(event['object'])
                                async with self.lock:
                                    self._requests[f"{req.namespace}.{req.name}"] = req
                            elif event['type'] == 'DELETED':
                                async with self.lock:
                                    k = (
                                        f"{event['object']['metadata']['namespace']}."
                                        f"{event['object']['metadata']['name']}"
                                    )
                                    if k in self._requests:
                                        del self._requests[k]
                                    if k in self._secrets:
                                        # TODO: Figure out how the lifecycle between request and secret should be
                                        #   handled, delete secret alongside request? or preserve?
                                        print(f"Secret {k} exists but request removed.")
                            else:
                                # TODO: Remove these, ensure all event types handled
                                print("Unhandled SecretRequest event:")
                                print(event)
                    except client.exceptions.ApiException:
                        pass

    async def watch_secrets(self) -> None:
        async with ApiClient() as api:
            core_api = client.CoreV1Api(api)
            async with watch.Watch().stream(
                core_api.list_secret_for_all_namespaces
            ) as stream:
                async for event in stream:
                    if event['type'] == 'ADDED' or event['type'] == 'MODIFIED':
                        req = k8s_models.Secret.from_kubernetes(event['object'])
                        async with self.lock:
                            secrets = req.secrets
                            req.secrets = {k: b64decode(v).decode() for k, v in secrets.items()}
                            self._secrets[f"{req.namespace}.{req.name}"] = req
                    elif event['type'] == 'DELETED':
                        req = k8s_models.Secret.from_kubernetes(event['object'])
                        async with self.lock:
                            k = f"{req.namespace}.{req.name}"
                            if k in self._secrets:
                                del self._secrets[k]
                    else:
                        # TODO: Remove these, ensure all event types handled
                        print("Unhandled Secret event:")
                        print(event)

    def gen_secrets_request(self, key: str, req) -> SecretsRequest:
        existing_secret = self._secrets.get(key)
        return SecretsRequest(
            name=req.name,
            namespace=req.namespace,
            secrets=[
                SecretRequest(
                    name=s.name,
                    note=s.note,
                    length=(
                        0 if (
                            not existing_secret or s.name not in existing_secret.secrets
                        ) else len(existing_secret.secrets[s.name])
                    )
                ) for s in req.secrets
            ]
        )

    async def get_requests(self) -> AsyncGenerator[SecretsRequest, None]:
        async with self.lock:
            for k, req in self._requests.items():
                yield self.gen_secrets_request(k, req)

    async def get_request(self, namespace: str, name: str) -> Optional[SecretsRequest]:
        async with self.lock:
            k = f"{namespace}.{name}"
            request = self._requests.get(k)
            return self.gen_secrets_request(k, request) if request else None

    async def set_secret(self, namespace: str, name: str, secrets: Dict[str, str]) -> bool:
        key = f"{namespace}.{name}"
        async with ApiClient() as api:
            core_api = client.CoreV1Api(api)
            if key in self._secrets:
                await core_api.replace_namespaced_secret(name, namespace, client.V1Secret(
                    api_version="v1",
                    kind="Secret",
                    metadata=client.V1ObjectMeta(
                        name=name,
                    ),
                    string_data=self._secrets[key].secrets | {k: v for k, v in secrets.items() if len(v)},
                ))
            else:
                await core_api.create_namespaced_secret(namespace, client.V1Secret(
                    api_version="v1",
                    kind="Secret",
                    metadata=client.V1ObjectMeta(
                        name=name,
                    ),
                    string_data={**secrets},
                ))

        return True

secrets_manager = SecretsManager()


@asynccontextmanager
async def k8s_lifespan_hook(app: FastAPI):
    await secrets_manager.start()
    yield

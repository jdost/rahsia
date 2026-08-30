from asyncio import Lock, TimeoutError, create_task, wait_for
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, AsyncGenerator, AsyncIterator, Sequence

import aiohttp.client_exceptions
import aiohttp.http_exceptions
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
    SERVER_TIMEOUT: timedelta = timedelta(seconds=300)
    IDLE_TIMEOUT: timedelta = timedelta(seconds=360)

    def __init__(self):
        self.lock = Lock()
        self.group = "jdost.us"
        self.version = "v1alpha1"
        self._secrets = {}
        self._requests = {}

    async def start(self) -> None:
        # Put in manual config.load_kube_config here for development, eg:
        #  from pathlib import Path
        #  await config.load_kube_config(
        #      config_file=str(Path.home() / ".kube/config"),
        #      context="default",
        #  )
        config.load_incluster_config()
        create_task(self.watch_requests())
        create_task(self.watch_secrets())

    @staticmethod
    def _resource_version(obj: Any | dict[str, Any]) -> str | None:
        meta = obj["metadata"] if isinstance(obj, dict) else obj.metadata
        return (
            meta.get("resourceVersion")
            if isinstance(meta, dict)
            else getattr(meta, "resource_version", None)
        )

    async def _watchdog(
        self, stream: AsyncIterator[dict[str, Any]]
    ) -> AsyncGenerator[dict[str, Any], None]:
        stream_iter = stream.__aiter__()
        while True:
            try:
                yield await wait_for(
                    stream_iter.__anext__(), self.IDLE_TIMEOUT.total_seconds()
                )
            except TimeoutError:
                return
            except StopAsyncIteration:
                return

    async def watch_requests(self) -> None:
        resource_version = ""
        while True:
            async with ApiClient() as api:
                crd_api = client.CustomObjectsApi(api)
                async with watch.Watch().stream(
                    crd_api.list_cluster_custom_object,
                    self.group,
                    self.version,
                    "secretrequests",
                    resource_version=resource_version,
                    allow_watch_bookmarks=True,
                    timeout_seconds=self.SERVER_TIMEOUT.total_seconds(),
                    _request_timeout=self.IDLE_TIMEOUT.total_seconds(),
                ) as stream:
                    try:
                        async for event in self._watchdog(stream):
                            resource_version = (
                                self._resource_version(event["object"])
                                or resource_version
                            )
                            if event["type"] == "ADDED" or event["type"] == "MODIFIED":
                                req = k8s_models.SecretsRequest.from_kubernetes(
                                    event["object"]
                                )
                                async with self.lock:
                                    self._requests[f"{req.namespace}.{req.name}"] = req
                            elif event["type"] == "DELETED":
                                async with self.lock:
                                    k = (
                                        f"{event['object']['metadata']['namespace']}."
                                        f"{event['object']['metadata']['name']}"
                                    )
                                    if k in self._requests:
                                        del self._requests[k]
                                    if k in self._secrets:
                                        # We shouldn't cull the secret if the request gets deleted
                                        #   as in some tests, we get false deletes w/ a quick
                                        #   create, probably something weird with etcd?
                                        print(f"Secret {k} exists but request removed.")
                            elif event["type"] == "BOOKMARK":
                                pass  # heartbeat/refresh
                            else:
                                # TODO: Remove these, ensure all event types handled
                                print("Unhandled SecretRequest event:")
                                print(event)
                    except client.exceptions.ApiException as err:
                        if err.status == 410:
                            resource_version = ""
                    except aiohttp.client_exceptions.ClientPayloadError:
                        pass
                    except aiohttp.http_exceptions.TransferEncodingError:
                        pass

    async def watch_secrets(self) -> None:
        resource_version = ""
        while True:
            async with ApiClient() as api:
                core_api = client.CoreV1Api(api)
                async with watch.Watch().stream(
                    core_api.list_secret_for_all_namespaces,
                    resource_version=resource_version,
                    allow_watch_bookmarks=True,
                    timeout_seconds=self.SERVER_TIMEOUT.total_seconds(),
                    _request_timeout=self.IDLE_TIMEOUT.total_seconds(),
                ) as stream:
                    try:
                        async for event in self._watchdog(stream):
                            resource_version = (
                                self._resource_version(event["object"])
                                or resource_version
                            )
                            if event["type"] == "ADDED" or event["type"] == "MODIFIED":
                                req = k8s_models.Secret.from_kubernetes(event["object"])
                                async with self.lock:
                                    self._secrets[f"{req.namespace}.{req.name}"] = req
                            elif event["type"] == "DELETED":
                                req = k8s_models.Secret.from_kubernetes(event["object"])
                                async with self.lock:
                                    k = f"{req.namespace}.{req.name}"
                                    if k in self._secrets:
                                        del self._secrets[k]
                            elif event["type"] == "BOOKMARK":
                                pass
                            else:
                                # TODO: Remove these, ensure all event types handled
                                print("Unhandled Secret event:")
                                print(event)
                    except client.exceptions.ApiException as err:
                        if err.status == 410:
                            resource_version = ""
                    except aiohttp.client_exceptions.ClientPayloadError:
                        pass
                    except aiohttp.http_exceptions.TransferEncodingError:
                        pass

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
                        0
                        if (
                            not existing_secret or s.name not in existing_secret.secrets
                        )
                        else len(existing_secret.secrets[s.name])
                    ),
                )
                for s in req.secrets
            ],
        )

    async def get_requests(self) -> AsyncGenerator[SecretsRequest, None]:
        async with self.lock:
            for k, req in self._requests.items():
                yield self.gen_secrets_request(k, req)

    async def get_request(self, namespace: str, name: str) -> SecretsRequest | None:
        async with self.lock:
            k = f"{namespace}.{name}"
            request = self._requests.get(k)
            return self.gen_secrets_request(k, request) if request else None

    async def set_secret(
        self, namespace: str, name: str, secrets: dict[str, str]
    ) -> bool:
        key = f"{namespace}.{name}"
        async with ApiClient() as api:
            core_api = client.CoreV1Api(api)
            if key in self._secrets:
                await core_api.replace_namespaced_secret(
                    name,
                    namespace,
                    client.V1Secret(
                        api_version="v1",
                        kind="Secret",
                        metadata=client.V1ObjectMeta(
                            name=name,
                        ),
                        string_data=self._secrets[key].secrets
                        | {k: v for k, v in secrets.items() if len(v)},
                    ),
                )
            else:
                await core_api.create_namespaced_secret(
                    namespace,
                    client.V1Secret(
                        api_version="v1",
                        kind="Secret",
                        metadata=client.V1ObjectMeta(
                            name=name,
                        ),
                        string_data={**secrets},
                    ),
                )

        return True


secrets_manager = SecretsManager()


@asynccontextmanager
async def k8s_lifespan_hook(app: FastAPI):
    await secrets_manager.start()
    yield

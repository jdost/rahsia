from base64 import b64decode
from typing import Any, Dict, Mapping, Sequence

import pydantic


class SecretRequest(pydantic.BaseModel):
    name: str
    note: str


class SecretsRequest(pydantic.BaseModel):
    name: str
    namespace: str
    secrets: Sequence[SecretRequest]

    @classmethod
    def from_kubernetes(cls, data: Dict[str, Any]) -> 'SecretsRequest':
        return cls(
            name=data['metadata']['name'],
            namespace=data['metadata']['namespace'],
            secrets=[
                SecretRequest(name=s['name'], note=s['note']) for
                s in data['spec']['secrets']
            ]
        )

    def __hash__(self) -> int:
        return hash((self.namespace, self.name))


class Secret(pydantic.BaseModel):
    name: str
    namespace: str
    secrets: Mapping[str, str]

    @classmethod
    def from_kubernetes(cls, data) -> 'Secret':
        secrets = {}
        for k, v in (data.data.items() if data.data else []):
            try:
                secrets[k] = b64decode(v).decode()
            except UnicodeDecodeError:
                # Some secrets are just raw data (like compressed files?) so
                # preserve if they fail to decode, could decode the byte string
                # but it breaks typing and we really don't care about these
                # (they shouldn't be managed via our requests)
                secrets[k] = v

        return cls(
            name=data.metadata.name,
            namespace=data.metadata.namespace,
            secrets=secrets,
        )

    def __repr__(self) -> str:
        return f"<Secret({self.namespace}.{self.name}) - {','.join(self.secrets.keys())}>"

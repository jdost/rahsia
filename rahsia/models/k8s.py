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
        return cls(
            name=data.metadata.name,
            namespace=data.metadata.namespace,
            secrets={**data.data} if data.data else {},
        )

    def __repr__(self) -> str:
        return f"<Secret({self.namespace}.{self.name}) - {','.join(self.secrets.keys())}>"

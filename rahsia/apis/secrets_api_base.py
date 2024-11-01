# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from rahsia.models.secret import Secret
from rahsia.models.secrets_request import SecretsRequest


class BaseSecretsApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseSecretsApi.subclasses = BaseSecretsApi.subclasses + (cls,)
    async def list_secrets(
        self,
        namespace: str,
        all: bool,
    ) -> List[SecretsRequest]:
        """List managed secrets"""
        ...


    async def set_secret(
        self,
        secret: Secret,
    ) -> None:
        """Set the requested secret values"""
        ...

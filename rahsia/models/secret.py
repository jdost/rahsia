# coding: utf-8

"""
    Rahsia

    Small k8s operator/app for defining secrets based on requested secrets from manifests using a CRD.  The idea is to avoid committing secrets to public manifests and instead define them in a simple way.  This is meant to be a lightweight solution for homelab setups where something larger like vault or cloud based solutions are unnecessary.

    The version of the OpenAPI document: 0.1.0
    Generated by OpenAPI Generator (https://openapi-generator.tech)

    Do not edit the class manually.
"""  # noqa: E501


from __future__ import annotations
import pprint
import re  # noqa: F401
import json




from pydantic import BaseModel, ConfigDict, Field, StrictStr
from typing import Any, ClassVar, Dict, List
from rahsia.models.secret_field import SecretField
try:
    from typing import Self
except ImportError:
    from typing_extensions import Self

class Secret(BaseModel):
    """
    Secret
    """ # noqa: E501
    name: StrictStr = Field(description="Name of the group of secrets being set")
    namespace: StrictStr = Field(description="Location/namespace for the target secret")
    secrets: List[SecretField]
    __properties: ClassVar[List[str]] = ["name", "namespace", "secrets"]

    model_config = {
        "populate_by_name": True,
        "validate_assignment": True,
        "protected_namespaces": (),
    }


    def to_str(self) -> str:
        """Returns the string representation of the model using alias"""
        return pprint.pformat(self.model_dump(by_alias=True))

    def to_json(self) -> str:
        """Returns the JSON representation of the model using alias"""
        # TODO: pydantic v2: use .model_dump_json(by_alias=True, exclude_unset=True) instead
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> Self:
        """Create an instance of Secret from a JSON string"""
        return cls.from_dict(json.loads(json_str))

    def to_dict(self) -> Dict[str, Any]:
        """Return the dictionary representation of the model using alias.

        This has the following differences from calling pydantic's
        `self.model_dump(by_alias=True)`:

        * `None` is only added to the output dict for nullable fields that
          were set at model initialization. Other fields with value `None`
          are ignored.
        """
        _dict = self.model_dump(
            by_alias=True,
            exclude={
            },
            exclude_none=True,
        )
        # override the default output from pydantic by calling `to_dict()` of each item in secrets (list)
        _items = []
        if self.secrets:
            for _item in self.secrets:
                if _item:
                    _items.append(_item.to_dict())
            _dict['secrets'] = _items
        return _dict

    @classmethod
    def from_dict(cls, obj: Dict) -> Self:
        """Create an instance of Secret from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate({
            "name": obj.get("name"),
            "namespace": obj.get("namespace"),
            "secrets": [SecretField.from_dict(_item) for _item in obj.get("secrets")] if obj.get("secrets") is not None else None
        })
        return _obj



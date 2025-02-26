from typing import Any, NamedTuple, Optional, Union


class DummyOntologyType:
    @staticmethod
    def api_name() -> str:
        return "DummyOntologyType"


class ObjectLocator(NamedTuple):
    object_api_name: str
    primary_key: Any


class AddObject(NamedTuple):
    locator: ObjectLocator
    fields: dict[str, Any]


class ModifyObject(NamedTuple):
    locator: ObjectLocator
    fields: dict[str, Optional[Any]]


class DeleteObject(NamedTuple):
    locator: ObjectLocator


class AddLink(NamedTuple):
    relationship_api_name: str
    source: ObjectLocator
    target: ObjectLocator


class RemoveLink(NamedTuple):
    relationship_api_name: str
    source: ObjectLocator
    target: ObjectLocator


OntologyEdit = Union[AddObject, ModifyObject, DeleteObject, AddLink, RemoveLink]

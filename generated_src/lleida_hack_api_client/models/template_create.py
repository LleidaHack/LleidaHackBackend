from typing import Any, Dict, List, Type, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="TemplateCreate")


@_attrs_define
class TemplateCreate:
    """
    Attributes:
        name (str):
        description (str):
        html (str):
        creator_id (int):
    """

    name: str
    description: str
    html: str
    creator_id: int
    additional_properties: Dict[str, Any] = _attrs_field(init=False,
                                                         factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        name = self.name

        description = self.description

        html = self.html

        creator_id = self.creator_id

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "name": name,
            "description": description,
            "html": html,
            "creator_id": creator_id,
        })

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name")

        description = d.pop("description")

        html = d.pop("html")

        creator_id = d.pop("creator_id")

        template_create = cls(
            name=name,
            description=description,
            html=html,
            creator_id=creator_id,
        )

        template_create.additional_properties = d
        return template_create

    @property
    def additional_keys(self) -> List[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties

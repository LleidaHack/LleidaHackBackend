import datetime
from typing import Any, Dict, List, Type, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

T = TypeVar("T", bound="TemplateGet")


@_attrs_define
class TemplateGet:
    """
    Attributes:
        name (str):
        description (str):
        html (str):
        created_date (datetime.date):
    """

    name: str
    description: str
    html: str
    created_date: datetime.date
    additional_properties: Dict[str, Any] = _attrs_field(init=False,
                                                         factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        name = self.name

        description = self.description

        html = self.html

        created_date = self.created_date.isoformat()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "name": name,
            "description": description,
            "html": html,
            "created_date": created_date,
        })

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name")

        description = d.pop("description")

        html = d.pop("html")

        created_date = isoparse(d.pop("created_date")).date()

        template_get = cls(
            name=name,
            description=description,
            html=html,
            created_date=created_date,
        )

        template_get.additional_properties = d
        return template_get

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

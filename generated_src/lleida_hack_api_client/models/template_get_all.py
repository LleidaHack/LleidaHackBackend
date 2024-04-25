import datetime
from typing import Any, Dict, List, Type, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

T = TypeVar("T", bound="TemplateGetAll")


@_attrs_define
class TemplateGetAll:
    """
    Attributes:
        name (str):
        description (str):
        html (str):
        created_date (datetime.date):
        id (int):
        creator_id (int):
        is_active (bool):
    """

    name: str
    description: str
    html: str
    created_date: datetime.date
    id: int
    creator_id: int
    is_active: bool
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        name = self.name

        description = self.description

        html = self.html

        created_date = self.created_date.isoformat()

        id = self.id

        creator_id = self.creator_id

        is_active = self.is_active

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "description": description,
                "html": html,
                "created_date": created_date,
                "id": id,
                "creator_id": creator_id,
                "is_active": is_active,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name")

        description = d.pop("description")

        html = d.pop("html")

        created_date = isoparse(d.pop("created_date")).date()

        id = d.pop("id")

        creator_id = d.pop("creator_id")

        is_active = d.pop("is_active")

        template_get_all = cls(
            name=name,
            description=description,
            html=html,
            created_date=created_date,
            id=id,
            creator_id=creator_id,
            is_active=is_active,
        )

        template_get_all.additional_properties = d
        return template_get_all

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

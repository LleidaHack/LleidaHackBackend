from typing import Any, Dict, List, Type, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="TemplateUpdate")


@_attrs_define
class TemplateUpdate:
    """
    Attributes:
        name (Union[None, str]):
        description (Union[None, str]):
        html (Union[None, str]):
    """

    name: Union[None, str]
    description: Union[None, str]
    html: Union[None, str]
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        name: Union[None, str]
        name = self.name

        description: Union[None, str]
        description = self.description

        html: Union[None, str]
        html = self.html

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "description": description,
                "html": html,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()

        def _parse_name(data: object) -> Union[None, str]:
            if data is None:
                return data
            return cast(Union[None, str], data)

        name = _parse_name(d.pop("name"))

        def _parse_description(data: object) -> Union[None, str]:
            if data is None:
                return data
            return cast(Union[None, str], data)

        description = _parse_description(d.pop("description"))

        def _parse_html(data: object) -> Union[None, str]:
            if data is None:
                return data
            return cast(Union[None, str], data)

        html = _parse_html(d.pop("html"))

        template_update = cls(
            name=name,
            description=description,
            html=html,
        )

        template_update.additional_properties = d
        return template_update

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

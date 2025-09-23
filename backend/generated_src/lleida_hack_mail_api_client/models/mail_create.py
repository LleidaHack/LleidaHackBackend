from typing import Any, Dict, List, Type, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="MailCreate")


@_attrs_define
class MailCreate:
    """
    Attributes:
        template_id (int):
        subject (str):
        fields (str):
        sender_id (Union[None, Unset, int]):  Default: 0.
        receiver_id (Union[None, Unset, str]):  Default: ''.
        receiver_mail (Union[None, Unset, str]):  Default: ''.
    """

    template_id: int
    subject: str
    fields: str
    sender_id: Union[None, Unset, int] = 0
    receiver_id: Union[None, Unset, str] = ""
    receiver_mail: Union[None, Unset, str] = ""
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        template_id = self.template_id

        subject = self.subject

        fields = self.fields

        sender_id: Union[None, Unset, int]
        if isinstance(self.sender_id, Unset):
            sender_id = UNSET
        else:
            sender_id = self.sender_id

        receiver_id: Union[None, Unset, str]
        if isinstance(self.receiver_id, Unset):
            receiver_id = UNSET
        else:
            receiver_id = self.receiver_id

        receiver_mail: Union[None, Unset, str]
        if isinstance(self.receiver_mail, Unset):
            receiver_mail = UNSET
        else:
            receiver_mail = self.receiver_mail

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "template_id": template_id,
                "subject": subject,
                "fields": fields,
            }
        )
        if sender_id is not UNSET:
            field_dict["sender_id"] = sender_id
        if receiver_id is not UNSET:
            field_dict["receiver_id"] = receiver_id
        if receiver_mail is not UNSET:
            field_dict["receiver_mail"] = receiver_mail

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        template_id = d.pop("template_id")

        subject = d.pop("subject")

        fields = d.pop("fields")

        def _parse_sender_id(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        sender_id = _parse_sender_id(d.pop("sender_id", UNSET))

        def _parse_receiver_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        receiver_id = _parse_receiver_id(d.pop("receiver_id", UNSET))

        def _parse_receiver_mail(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        receiver_mail = _parse_receiver_mail(d.pop("receiver_mail", UNSET))

        mail_create = cls(
            template_id=template_id,
            subject=subject,
            fields=fields,
            sender_id=sender_id,
            receiver_id=receiver_id,
            receiver_mail=receiver_mail,
        )

        mail_create.additional_properties = d
        return mail_create

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

from typing import Any, Dict, List, Type, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="MailGet")


@_attrs_define
class MailGet:
    """
    Attributes:
        id (int):
        sender_id (int):
        receiver_id (str):
        template_id (int):
        subject (str):
        receiver_mail (Union[None, str]):
        fields (str):
        sent (bool):
    """

    id: int
    sender_id: int
    receiver_id: str
    template_id: int
    subject: str
    receiver_mail: Union[None, str]
    fields: str
    sent: bool
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        id = self.id

        sender_id = self.sender_id

        receiver_id = self.receiver_id

        template_id = self.template_id

        subject = self.subject

        receiver_mail: Union[None, str]
        receiver_mail = self.receiver_mail

        fields = self.fields

        sent = self.sent

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "sender_id": sender_id,
                "receiver_id": receiver_id,
                "template_id": template_id,
                "subject": subject,
                "receiver_mail": receiver_mail,
                "fields": fields,
                "sent": sent,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        id = d.pop("id")

        sender_id = d.pop("sender_id")

        receiver_id = d.pop("receiver_id")

        template_id = d.pop("template_id")

        subject = d.pop("subject")

        def _parse_receiver_mail(data: object) -> Union[None, str]:
            if data is None:
                return data
            return cast(Union[None, str], data)

        receiver_mail = _parse_receiver_mail(d.pop("receiver_mail"))

        fields = d.pop("fields")

        sent = d.pop("sent")

        mail_get = cls(
            id=id,
            sender_id=sender_id,
            receiver_id=receiver_id,
            template_id=template_id,
            subject=subject,
            receiver_mail=receiver_mail,
            fields=fields,
            sent=sent,
        )

        mail_get.additional_properties = d
        return mail_get

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

from enum import Enum


class RegistrationStatus(Enum):
    PENDING = (1, 'pending')
    ACCEPTED = (2, 'accepted')
    CONFIRMED = (3, 'confirmed')
    PARTICIPATING = (4, 'partcipating')

    @property
    def status(self):
        return self.value[1]

    def succ(self):
        v = self.value[0] * 2
        if v > 16:
            raise ValueError('Enumeration ended')
        return RegistrationStatus(v)

    def pred(self):
        v = self.value[0] // 2
        if v == 0:
            raise ValueError('Enumeration ended')
        return RegistrationStatus(v)

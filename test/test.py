class T1:

    def __init__(self, f1, f2):
        self.f1 = f1
        self.f2 = f2


class T2(T1):

    def __init__(self, f1, f2, f3):
        super().__init__(f1, f2)
        self.f3 = f3


def test(inp: T1):
    print(inp.__dict__)


t = T2(1, 2, 3)
test(t)

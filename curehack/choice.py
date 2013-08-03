class InvalidChoice(Exception):
    pass


class Choice(str):
    """Class for choice value of some schema
    """
    choices = ()
    IsInvalidChoice = InvalidChoice

    def __init__(self, string=''):
        self.validate(string)
        self.choice = string

    @property
    def choice_keys(self):
        return [choice[0] for choice in self.choices]

    def validate(self, value):
        if not value in self.choice_keys:
            raise self.IsInvalidChoice


class LikingChoice(Choice):
    choices = (('like', 'Like'),
               ('soso', 'Soso'),
               ('unlike', 'Unlike'))

    int_mapping = {
        'like': 1,
        'soso': 0,
        'unlike': -1,
    }

    def __int__(self):
        return self.int_mapping[self]

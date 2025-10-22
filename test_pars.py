from dataclasses import dataclass
import inspect

@dataclass
class User:
    """ Define a user """
    id: int
    username: str
    get_full_name: str
    email: str
    is_staff: bool
    is_superuser: bool
    is_active: bool
    last_login: str
    
    def validate(self):
        """
        Validate the instance based on field annotations
        """
        annotations = self.__annotations__
        for field_name, expected_type in annotations.items():
            value = getattr(self, field_name)
            if not isinstance(value, expected_type):
                raise TypeError(f"Field {field_name} should be of type {expected_type}, got {type(value)}")
        return True
    
    def __post_init__(self):
        """
        Automatically validate after initialization
        """
        self.validate()

# Test with valid data
try:
    a = User(1, 'test', "hi", 'test@example.com', True, True, True, '2020-01-01')
    print("Valid user:", a)
except TypeError as e:
    print("Validation error:", e)

# Test with invalid data
try:
    b = User("not_an_int", 'test', "hi", 'test@example.com', True, True, True, '2020-01-01')
    print("Valid user:", b)
except TypeError as e:
    print("Validation error:", e)
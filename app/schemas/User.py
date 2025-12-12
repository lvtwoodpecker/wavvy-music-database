from pydantic import BaseModel, ConfigDict

        
class UserCreateSchema():
    
    def __init__(
        self,
        user_orm_object: object
    ) -> None:
        self.email = user_orm_object.email
        self.username = user_orm_object.username
        self.first_name = user_orm_object.first_name
        self.last_name = user_orm_object.last_name
        self.password = user_orm_object.password
        self.country = user_orm_object.country
        self.role = user_orm_object.role
        
class UserUpdateSchema():
    
    def __init__(
        self,
        user_orm_object: object
    ) -> None:
        self.email = user_orm_object.email
        self.username = user_orm_object.username
        self.first_name = user_orm_object.first_name
        self.last_name = user_orm_object.last_name
        self.password = user_orm_object.password
        self.country = user_orm_object.country
        self.role = user_orm_object.role
        self.status = user_orm_object.status
        
        
class UserResponseSchema():
    
    def __init__(
        self,
        user_orm_object: object
    ) -> None:
        self.user_id = user_orm_object.user_id
        self.email = user_orm_object.email
        self.username = user_orm_object.username
        self.first_name = user_orm_object.first_name
        self.last_name = user_orm_object.last_name
        self.country = user_orm_object.country
        self.role = user_orm_object.role
        self.status = user_orm_object.status
        
        
class AuthResponseSchema():
    
    def __init__(
        self,
        token: str,
        user: UserResponseSchema
    ) -> None:
        self.token = token
        self.user = user

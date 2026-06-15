from pydantic_settings import BaseSettings


class Setting(BaseSettings):
    database_hostname:str
    database_username:str
    database_password:str
    database_port:str
    database_name:str
    secret_key:str
    algorithm:str
    access_token_expire_minutes:int
    resend_api_key:str
    class Config:
        env_file = ".env"



        
setting = Setting()

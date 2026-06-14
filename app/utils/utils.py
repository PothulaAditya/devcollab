from passlib.context import CryptContext

pwdcontext = CryptContext(schemes=['bcrypt'],deprecated = "auto")

def hash_password(password:str):
    return pwdcontext.hash(password)


def verify_password(hashed_password:str,password:str):
    return pwdcontext.verify(password,hashed_password)






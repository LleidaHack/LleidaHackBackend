import os
import time
import jwt
from configparser import ConfigParser

 
def set_up():
    """Sets up configuration for the app"""

    env = os.getenv("ENV", ".config")

    if env == ".config":
        config = ConfigParser()
        config.read(".config")
        config = config["AUTH0"]
    else:
        config = {
            "DOMAIN": os.getenv("DOMAIN", "your.domain.com"),
            "API_AUDIENCE": os.getenv("API_AUDIENCE", "your.audience.com"),
            "ISSUER": os.getenv("ISSUER", "https://your.domain.com/"),
            "ALGORITHMS": os.getenv("ALGORITHMS", "RS256"),
        }
    return config

class VerifyToken():
    """Verifies the token"""
    def __init__(self):
        self.config = set_up()

    def verify_token(self, token):
        """Verifies the token"""
        try:
            payload = jwt.decode(token, self.config["ALGORITHMS"],
                                 audience=self.config["API_AUDIENCE"],
                                 issuer=self.config["ISSUER"],
                                 algorithms=[self.config["ALGORITHMS"]])
        except jwt.ExpiredSignatureError:
            return False, "token_expired"
        except jwt.InvalidTokenError:
            return False, "invalid_token"
        return True, payload
        

    def create_token(self, email):
        """Creates a token"""
        try:
            payload = {
                "sub": email,
                "iat": time.time(),
                "exp": time.time() + 3600
            }
            token = jwt.encode(payload, self.config["ALGORITHMS"],
                               issuer=self.config["ISSUER"],
                               audience=self.config["API_AUDIENCE"])
            return token
        except Exception as e:
            return e
import os
import requests
import random
import string
import uuid
from authgateway import *
import secrets
from pathlib import Path
import sys
from dotenv import load_dotenv

class SMSAuthException(BaseException):
    pass

class TinderSMSAuth(object):

    def __init__(self, email=None, phonenumber=None):
        load_dotenv()  # Cargar variables de entorno desde el archivo .env
        self.installid = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=11))
        self.session = requests.Session()
        self.session.headers.update({"user-agent": "Tinder Android Version 14.9.0"})
        self.url = "https://api.gotinder.com"
        self.funnelid = str(uuid.uuid4())
        self.appsessionid = str(uuid.uuid4())
        self.deviceid = secrets.token_hex(8)
        self.authtoken = None
        self.refreshtoken = None
        self.userid = None
        self.email = email or os.environ.get("EMAIL")
        self.phonenumber = phonenumber or os.environ.get("PHONE_NUMBER")
        if os.getenv("TINDER_API_TOKEN") and os.getenv("TINDER_REFRESH_TOKEN"):
            print(".env file found with TINDER_API_TOKEN and TINDER_REFRESH_TOKEN")
            self.authtoken = os.getenv("TINDER_API_TOKEN")
            self.refreshtoken = os.getenv("TINDER_REFRESH_TOKEN")
            print("authToken found: " + self.authtoken)
        self.login()

    def _postloginreq(self, body, headers=None):
        if headers is not None:
            self.session.headers.update(headers)
        r = self.session.post(self.url + "/v3/auth/login", data=bytes(body))
        response = AuthGatewayResponse().parse(r.content).to_dict()
        return response

    def loginwrapper(self, body, seconds, headers=None):
        response = self._postloginreq(body, headers)
        print(response)
        if "validatePhoneOtpState" in response.keys() and response["validatePhoneOtpState"]["smsSent"]:
            otpresponse = input("OTP Response from SMS: ")
            resp = PhoneOtp(phone=self.phonenumber, otp=otpresponse)
            messageresponse = AuthGatewayRequest(phone_otp=resp)
            seconds += random.uniform(30, 90)
            header_timer = {"app-session-time-elapsed": format(seconds, ".3f")}
            return self.loginwrapper(messageresponse, seconds, header_timer)
        elif "getPhoneState" in response.keys():
            self.refreshtoken = response['getPhoneState']['refreshToken']
            messageresponse = AuthGatewayRequest(refresh_auth=RefreshAuth(refresh_token=self.refreshtoken))
            seconds += random.uniform(30, 90)
            header_timer = {"app-session-time-elapsed": format(seconds, ".3f")}
            return self.loginwrapper(messageresponse, seconds, header_timer)
        elif "validateEmailOtpState" in response.keys() and response["validateEmailOtpState"]["emailSent"]:
            emailoptresponse = input("Check your email and input the verification code just sent to you: ")
            refreshtoken = response["validateEmailOtpState"]["refreshToken"]
            if self.email is None:
                self.email = input("Input your email: ")
            messageresponse = AuthGatewayRequest(email_otp=EmailOtp(otp=emailoptresponse, email=self.email, refresh_token=refreshtoken))
            seconds += random.uniform(30, 90)
            header_timer = {"app-session-time-elapsed": format(seconds, ".3f")}
            return self.loginwrapper(messageresponse, seconds, header_timer)
        elif "getEmailState" in response.keys():
            refreshtoken = response['getEmailState']['refreshToken']
            if self.email is None:
                self.email = input("Input your email: ")
            seconds += random.uniform(30, 90)
            header_timer = {"app-session-time-elapsed": format(seconds, ".3f")}
            messageresponse = AuthGatewayRequest(email=Email(email=self.email, refresh_token=refreshtoken))
            return self.loginwrapper(messageresponse, seconds, header_timer)
        elif "error" in response.keys() and response["error"]["message"] == 'INVALID_REFRESH_TOKEN':
            print("Refresh token error, restarting auth")
            phonenumber = input("phone number (starting with 1, numbers only): ")
            self.phonenumber = phonenumber
            messageresponse = AuthGatewayRequest(phone=Phone(phone=self.phonenumber))
            seconds += random.uniform(30, 90)
            header_timer = {"app-session-time-elapsed": format(seconds, ".3f")}
            return self.loginwrapper(messageresponse, seconds, header_timer)
        elif "loginResult" in response.keys() and "authToken" in response["loginResult"].keys():
            return response
        else:
            raise SMSAuthException

    def login(self):
        payload = {
            "device_id": self.installid,
            "experiments": ["default_login_token", "tinder_u_verification_method", "tinder_rules",
                            "user_interests_available"]
        }
        self.session.post(self.url + "/v2/buckets", json=payload)
        if self.refreshtoken is not None:
            print("Attempting to refresh auth token with saved refresh token")
            messageout = AuthGatewayRequest(get_initial_state=GetInitialState(refresh_token=self.refreshtoken))
        else:
            if self.phonenumber is None:
                self.phonenumber = input("phone number (starting with 1, numbers only): ")
            messageout = AuthGatewayRequest(phone=Phone(phone=self.phonenumber))
        seconds = random.uniform(100, 250)
        headers = {
            'user-agent': "Tinder Android Version 14.9.0", 
            'os-version': "29",
            'app-version': "4467", 
            'platform': "android", 
            'platform-variant': "Google-Play", 
            'x-supported-image-formats': "webp",
            'accept-language': "en-US",
            'tinder-version': "14.9.0", 
            'Store-Variant': 'Play-Store',
            'persistent-device-id': self.deviceid,
            'content-type': "application/x-protobuf",
            'Host': 'api.gotinder.com',
            'connection': "close",
            'accept-encoding': "gzip",
        }
        response = self.loginwrapper(messageout, seconds, headers)
        self.refreshtoken = response["loginResult"]["refreshToken"]
        self.authtoken = response["loginResult"]["authToken"]
        self.session.headers.update({"X-AUTH-TOKEN": self.authtoken})
        
        # Guardar los tokens en el archivo .env sin comillas
        self.save_tokens_to_env("TINDER_API_TOKEN", self.authtoken)
        self.save_tokens_to_env("TINDER_REFRESH_TOKEN", self.refreshtoken)
        print("Auth token saved to .env")

    def save_tokens_to_env(self, key, value):
        env_path = dotenv.find_dotenv()
        if not env_path:
            env_path = '.env'
        with open(env_path, 'r') as file:
            lines = file.readlines()
        with open(env_path, 'w') as file:
            for line in lines:
                if line.startswith(key + '='):
                    file.write(f"{key}={value}\n")
                else:
                    file.write(line)
            if not any(line.startswith(key + '=') for line in lines):
                file.write(f"{key}={value}\n")

def main():
    print("This script will use the sms login to obtain the auth token, which will be saved to .env")
    emailaddy = os.environ.get("EMAIL")
    phonenumber = os.environ.get("PHONE_NUMBER")
    TinderSMSAuth(email=emailaddy, phonenumber=phonenumber)

if __name__ == "__main__":
    main()
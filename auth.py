import requests
import random
import string
import uuid
import secrets
from pathlib import Path
import dotenv
import os
from authgateway import *
from dotenv import load_dotenv

class SMSAuthException(BaseException):
    pass

class TinderSMSAuth:
    def __init__(self, email=None):
        dotenv.load_dotenv()  # Cargar las variables de entorno del archivo .env
        self.installid = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=11))
        self.session = requests.Session()
        self.session.headers.update({"user-agent": "Tinder Android Version 11.24.0"})
        self.url = "https://api.gotinder.com"
        self.funnelid = str(uuid.uuid4())
        self.appsessionid = str(uuid.uuid4())
        self.deviceid = secrets.token_hex(8)
        self.authtoken = None
        self.refreshtoken = None
        self.userid = None
        self.email = email
        self.phonenumber = None

        # Cargar tokens del archivo .env si existen
        if os.getenv("TINDER_API_TOKEN") and os.getenv("TINDER_REFRESH_TOKEN"):
            print(".env file found with TINDER_API_TOKEN and TINDER_REFRESH_TOKEN")
            self.authtoken = os.getenv("TINDER_API_TOKEN")
            self.refreshtoken = os.getenv("TINDER_REFRESH_TOKEN")
            print("authToken found: " + self.authtoken)

    def _postloginreq(self, body, headers=None):
        if headers is not None:
            self.session.headers.update(headers)
        r = self.session.post(self.url + "/v3/auth/login", data=bytes(body))
        response = AuthGatewayResponse().parse(r.content).to_dict()
        return response

    def loginwrapper(self, body, seconds, headers=None, phone_otp=None, email_otp=None):
        response = self._postloginreq(body, headers)
        print(response)
        if "validatePhoneOtpState" in response.keys() and response["validatePhoneOtpState"]["smsSent"]:
            if phone_otp is None:
                return {"otp_needed": "phone", "response": response}  # Indicar que se necesita OTP del teléfono
            resp = PhoneOtp(phone=self.phonenumber, otp=phone_otp)
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
            if email_otp is None:
                return {"otp_needed": "email", "response": response}  # Indicar que se necesita OTP del correo electrónico
            refreshtoken = response["validateEmailOtpState"]["refreshToken"]
            messageresponse = AuthGatewayRequest(email_otp=EmailOtp(otp=email_otp, email=self.email, refresh_token=refreshtoken))
            seconds += random.uniform(30, 90)
            header_timer = {"app-session-time-elapsed": format(seconds, ".3f")}
            return self.loginwrapper(messageresponse, seconds, header_timer)
        elif "getEmailState" in response.keys():
            refreshtoken = response['getEmailState']['refreshToken']
            seconds += random.uniform(30, 90)
            header_timer = {"app-session-time-elapsed": format(seconds, ".3f")}
            messageresponse = AuthGatewayRequest(email=Email(email=self.email, refresh_token=refreshtoken))
            return self.loginwrapper(messageresponse, seconds, header_timer)
        elif "error" in response.keys() and response["error"]["message"] == 'INVALID_REFRESH_TOKEN':
            raise SMSAuthException("Invalid refresh token")
        elif "loginResult" in response.keys() and "authToken" in response["loginResult"].keys():
            return response
        else:
            raise SMSAuthException("Unknown authentication error")

    def login(self, phonenumber=None, phone_otp=None, email_otp=None):
        payload = {
            "device_id": self.installid,
            "experiments": ["default_login_token", "tinder_u_verification_method", "tinder_rules", "user_interests_available"]
        }
        self.session.post(self.url + "/v2/buckets", json=payload)
        if self.refreshtoken is not None:
            print("Attempting to refresh auth token with saved refresh token")
            messageout = AuthGatewayRequest(get_initial_state=GetInitialState(refresh_token=self.refreshtoken))
        else:
            if phonenumber is None:
                raise SMSAuthException("Phone number required")
            self.phonenumber = phonenumber
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
        response = self.loginwrapper(messageout, seconds, headers, phone_otp, email_otp)
        if isinstance(response, dict) and "otp_needed" in response:
            return response  # Devolver la respuesta para manejar OTPs
        if "loginResult" in response.keys():
            self.refreshtoken = response["loginResult"]["refreshToken"]
            self.authtoken = response["loginResult"]["authToken"]
            self.session.headers.update({"X-AUTH-TOKEN": self.authtoken})
            
            # Guardar los tokens en el archivo .env
            dotenv.set_key(dotenv.find_dotenv(), "TINDER_API_TOKEN", self.authtoken)
            dotenv.set_key(dotenv.find_dotenv(), "TINDER_REFRESH_TOKEN", self.refreshtoken)
            print("Auth token saved to .env")
            return self.authtoken, self.refreshtoken
        return response  # Devolver la respuesta para manejar OTPs

def authenticate_tinder(email=None, phonenumber=None, phone_otp=None, email_otp=None):
    tinder_auth = TinderSMSAuth(email=email)
    return tinder_auth.login(phonenumber=phonenumber, phone_otp=phone_otp, email_otp=email_otp)

# Ejemplo de uso
def main():
    load_dotenv()
    email = os.environ("EMAIL")
    phonenumber = os.environ("PHONE_NUMBER")
    try:
        response = authenticate_tinder(email=email, phonenumber=phonenumber)
        if response.get("otp_needed") == "phone":
            print("SMS enviado. Por favor ingrese el OTP recibido.")
            phone_otp = input("Ingrese el OTP del SMS: ")
            response = authenticate_tinder(email=email, phonenumber=phonenumber, phone_otp=phone_otp)
        if response.get("otp_needed") == "email":
            print("Correo electrónico enviado. Por favor ingrese el OTP recibido.")
            email_otp = input("Ingrese el OTP del correo electrónico: ")
            response = authenticate_tinder(email=email, phonenumber=phonenumber, phone_otp=phone_otp, email_otp=email_otp)
        if "loginResult" in response:
            print("Autenticación completada.")
            auth_token = response["loginResult"]["authToken"]
            refresh_token = response["loginResult"]["refreshToken"]
            print(f"Auth Token: {auth_token}")
            print(f"Refresh Token: {refresh_token}")
    except SMSAuthException as e:
        print(f"Error durante la autenticación: {e}")

# Config variables
API_URL = 'https://api.gotinder.com'

# get value from config.py
def get_config_value(key):
    return globals().get(key)

# set value in config.py
def set_config_value(key, value):
    globals()[key] = value
# Please rename this file to config_80.py and adapt it to your needs

# Selenium

# Time till the next command is executed
SELENIUM_DELAY = 0

# How long a "Wait Until ..." command should wait
SELENIUM_TIMEOUT = 5


# Odoo
SERVER = "localhost"
PORT = "8069"
# no port if you test with workers
ODOO_URL = "http://" + SERVER + ":" + PORT
ODOO_URL_LOGIN = "http://" + SERVER + ":" + PORT
ODOO_DB = "sales_s"
ODOO_USER = "salesmanager@gmail.com"
ODOO_PASSWORD = "admin"
BROWSER = "chrome"
ALIAS = "Chrome"

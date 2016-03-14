# Please rename this file to config_80.py and adapt it to your needs

# Selenium

# Time till the next command is executed
SELENIUM_DELAY = 0

# How long a "Wait Until ..." command should wait
SELENIUM_TIMEOUT = 20


# Odoo
SERVER = "localhost"
PORT = "8069"
# no port if you test with workers
ODOO_URL = "http://" + SERVER + ":" + PORT
ODOO_URL_LOGIN = "http://" + SERVER + ":" + PORT + "/web/login"
ODOO_PORTAL_URL = "http://portal." + SERVER + ":" + PORT
ODOO_PORTAL_URL_LOGIN = "http://portal." + SERVER + ":" + PORT + "/web/login"
ODOO_DB = "leaserad"
ODOO_USER = "rainer.brand"
ODOO_PASSWORD = "rainer.brand"
BROWSER = "phantomjs"
ALIAS = "PhantomJS"
BAMBOO = "yes"

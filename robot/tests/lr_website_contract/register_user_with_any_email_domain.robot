*** Settings ***
Documentation  Register a Portal User with specific email domain
Resource       ../../../robot/keywords_8_0.robot


*** Test Cases ***
Register a User with random domain in idupa portal what should be allowed
    Open Browser    ${ODOO_PORTAL_URL}  ${BROWSER}  ${ALIAS}
    Maximize Browser Window
    Run Keyword If    '${bamboo}' != 'yes'    Wait Until Page Contains Element    xpath=//select[@id='db']
    Run Keyword If    '${bamboo}' != 'yes'    Select From List By Value           xpath=//select[@id='db']    ${ODOO_DB}
    WebsitePortalPage    idupa/signup/JIJ433IBJ
    Input Text    name=name    Test User
    Input Text    name=login    testuser01@example.com
    Select From List By Label    email_type    Geschäftlich
    Input Password    name=password   MyPassword_123
    Wait Until Page Contains Element    xpath=//div[contains(@class,'lr_password-success-message')]
    Click Button    submit_signup
    Wait Until Page Contains Element    xpath=//div[contains(@class,'lr_message-logsign')]/p[contains(@class,'alert-success')]

Close Browser 1
    Close Browser

Register a User with random domain in bahn portal what should be not allowed
    Open Browser    ${ODOO_PORTAL_URL}  ${BROWSER}  ${ALIAS}
    Maximize Browser Window
    Run Keyword If    '${bamboo}' != 'yes'    Wait Until Page Contains Element    xpath=//select[@id='db']
    Run Keyword If    '${bamboo}' != 'yes'    Select From List By Value           xpath=//select[@id='db']    ${ODOO_DB}
    WebsitePortalPage    bahn/signup/547GJU56JG
    Input Text    name=name    Test User 2
    Input Text    name=login    testuser02@example.com
    Input Password    name=password   MyPassword_123
    Wait Until Page Contains Element    xpath=//div[contains(@class,'lr_password-success-message')]
    Click Button    submit_signup
    Wait Until Page Contains Element    xpath=//div[contains(@class,'lr_message-logsign')]/div[contains(@class,'alert-danger')]

Close Browser 2
    Close Browser

Login in Backend and check created Users
    Login    ${ODOO_URL_LOGIN}    admin    admin
    Sleep    3
    MainMenu    Einstellungen
    Sleep    3
    SubMenu    Benutzer
    Sleep    3
    ClearFilter
    SearchFilter    Inaktive Benutzer
    Page Should Contain Element    xpath=//div[contains(@class,'openerp')][last()]//table[contains(@class, 'oe_list_content')]//td[@data-bt-testing-model_name='res.users' and @data-field='login'][contains(text(), 'testuser01@example.com')]
    Page Should Not Contain Element    xpath=//div[contains(@class,'openerp')][last()]//table[contains(@class, 'oe_list_content')]//td[@data-bt-testing-model_name='res.users' and @data-field='login'][contains(text(), 'testuser02@example.com')]

Close Browser 3
    Close Browser

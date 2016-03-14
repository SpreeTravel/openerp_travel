*** Settings ***
Documentation  Register a Portal User
Resource       ../../../robot/keywords_8_0.robot


*** Test Cases ***
Register a Portal User
    Open Browser                        ${ODOO_PORTAL_URL}  ${BROWSER}  ${ALIAS}
    Maximize Browser Window
    Run Keyword If                      '${bamboo}' != 'yes'                   Wait Until Page Contains Element    xpath=//select[@id='db']
    Run Keyword If                      '${bamboo}' != 'yes'                   Select From List By Value           xpath=//select[@id='db']    ${ODOO_DB}
    WebsitePortalPage  bahn/signup/547GJU56JG
    Input Text                           name=name  Farid Shahy
    Input Text                           name=login  fshahy@bloopark.de
    Input Password                       name=password   MyPassword_123
    Wait Until Page Contains Element    xpath=//div[contains(@class,'lr_password-success-message')]

Close Browser
    Close Browser


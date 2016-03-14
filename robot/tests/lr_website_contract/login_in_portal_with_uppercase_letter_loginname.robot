*** Settings ***
Documentation  Login in portal with uppercase letter in email
Resource       ../../../robot/keywords_8_0.robot


*** Test Cases ***
Register a Portal User
    Open Browser                        ${ODOO_PORTAL_URL}  ${BROWSER}  ${ALIAS}
    Maximize Browser Window
    Run Keyword If                      '${bamboo}' != 'yes'                   Wait Until Page Contains Element    xpath=//select[@id='db']
    Run Keyword If                      '${bamboo}' != 'yes'                   Select From List By Value           xpath=//select[@id='db']    ${ODOO_DB}
    WebsitePortalPage                   bahn/login/547GJU56JG
    Input Text                          name=login  DEMO
    Input Password                      name=password   demo
    Click Button                        xpath=//button[contains(@id,'submit_login')]
    Wait Until Page Contains Element    xpath=//h2[contains(@id,'account_main')]

Close Browser
    Close Browser


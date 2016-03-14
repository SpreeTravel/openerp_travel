*** Settings ***
Documentation  Publishing from Contract landing page
Resource       ../keywords_8_0.robot

*** Test Cases ***
Valid Login
    Login    ${ODOO_PORTAL_URL_LOGIN}

Access Contract URL for Website
    MainMenu    Verkauf
    SubMenu    Rahmenverträge
    TreeViewSelectRecord    lr.contract    partner_id    Lenovo Thinkpad
    NotebookPage    Portal

Landing Page
    ${portal}=    Get Text      xpath=//div[contains(@class, 'tab-pane active')]//a[contains(@class, 'oe_form_uri')]
    ${portallink}=    Get Substring    ${portal}    -20
    Go To    ${ODOO_PORTAL_URL}${portallink}
    Execute Javascript    $($('button[data-dismiss="modal"]')[0]).trigger('click');
    Sleep    3
    # Run Keyword And Continue On Failure    Click Link    xpath=//a[contains(@class, 'cc-cookie-accept')]
    # Sleep    5

Publish
    Click Button    xpath=//div[contains(@class, 'js_publish_management')]//button[contains(@class, 'dropdown-toggle')]
    Click Link    xpath=//a[contains(@class, 'js_publish_btn')]
    Input Text    name=confirmation_word    publish
    Execute Javascript    $($('button[data-action="publish"]')[0]).trigger('click');

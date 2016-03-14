*** Settings ***
Documentation  Publishing from Contract landing page
Resource       ../keywords_8_0.robot

*** Test Cases ***
Valid Login
    Login    ${ODOO_PORTAL_URL_LOGIN}

Open Contract
    Sleep    3
    MainMenu    Verkauf
    SubMenu    Rahmenverträge
    TreeViewSelectRecord    lr.contract    partner_id    Lenovo Thinkpad
    Button     lr.contract   oe_form_button_edit
    NotebookPage    Portal
    # Char    lr.contract    slug    thinkpad
    # the above keyword does work for this field! So I do it another way.
    Wait Until Page Contains Element    xpath=//input[contains(@placeholder,'nur a-z, 0-9, _ , - darf nicht mit einem Sonderzeichen beginnen')]
    Input Text    xpath=//input[contains(@placeholder,'nur a-z, 0-9, _ , - darf nicht mit einem Sonderzeichen beginnen')]    thinkpad
    Button    lr.contract    oe_form_button_save

Landing Page
    Sleep    3
    ${portal}=    Get Text      xpath=//div[contains(@class, 'tab-pane active')]//a[contains(@class, 'oe_form_uri')]
    ${portallink}=    Get Substring    ${portal}    -20
    Go To    ${ODOO_PORTAL_URL}${portallink}
    Sleep    3
    # Run Keyword And Continue On Failure    Click Link    xpath=//a[contains(@class, 'cc-cookie-accept')]
    # Sleep    5

Preview Mode
    Sleep    3
    Click Button    xpath=//div[contains(@class, 'js_publish_management')]//button[contains(@class, 'dropdown-toggle')]
    Click Link    xpath=//a[contains(@class, 'js_preview_btn')]
    Execute Javascript    $($('button[data-dismiss="modal"]')[0]).trigger('click');
    Page Should Contain Element    xpath=//div[@id='preview_mode_warning']

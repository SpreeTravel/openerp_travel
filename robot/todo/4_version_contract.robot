*** Settings ***
Documentation  Create versions for the Contract landing page
Resource       ../keywords_8_0.robot


*** Keywords ***
EditHeadline    [Arguments]    ${text}
    Execute Javascript    var section = $('div#wrap');section.attr('data-oe-note', 'note-editor-1');section.addClass('o_editable note-air-editor note-editable o_dirty');section.find('h2.lr_headline')[0].textContent = '${text}';

CheckHeadline    [Arguments]     ${text}
    Page Should Contain Element    xpath=//section[@id='lr_multiple_rows']//h2[contains(@class, 'lr_headline')][contains(text(), '${text}')]

CreateVersion
    WebsiteModalButton    o_create
    Sleep     1
    WebsiteModalButton    o_confirm

PublishVersion
    Click Link    xpath=//a[@id='version-menu-button']
    Click Link    xpath=//ul[contains(@class, 'version_menu')]//a[@data-action='publish_version']
    WebsiteModalButton    o_confirm
    Sleep     1
    WebsiteModalButton    o_confirm


*** Test Cases ***
Template Landing Page
    Login
    Sleep    5
    WebsitePage    edit_page/2/lr_website_contract.company_landing_page
    # Click Link    xpath=//a[contains(@class, 'cc-cookie-accept')]
    # Sleep    5

Edit Master Template
    Wait Until Page Contains Element  xpath=//button[contains(@data-action, 'edit')]
    Click Button    xpath=//button[contains(@data-action, 'edit')]
    EditHeadline    Master Template
    Sleep    3
    Click Button    xpath=//button[contains(@data-action, 'save')]
    CreateVersion
    CheckHeadline    Master Template
    Sleep    5
    PublishVersion

Contract Landing Page
    LoginNoNewBrowser    ${ODOO_PORTAL_URL}
    Sleep     5
    MainMenu    Verkauf
    SubMenu    Rahmenverträge
    TreeViewSelectRecord    lr.contract    partner_id    Lenovo Thinkpad
    NotebookPage    Portal
    ${portal}=    Get Text      xpath=//div[contains(@class, 'tab-pane active')]//a[contains(@class, 'oe_form_uri')]
    ${portallink}=    Get Substring    ${portal}    -20
    Go To    ${ODOO_PORTAL_URL}${portallink}
    Sleep    3
    # Run Keyword And Continue On Failure    Click Link    xpath=//a[contains(@class, 'cc-cookie-accept')]
    # Sleep    5
    CheckHeadline    Master Template

Edit Contract Landing Page
    Wait Until Page Contains Element  xpath=//button[contains(@data-action, 'edit')]
    Click Button    xpath=//button[contains(@data-action, 'edit')]
    EditHeadline    Lenovo Thinkpad Version
    Click Button    xpath=//button[contains(@data-action, 'save')]
    CreateVersion
    CheckHeadline    Lenovo Thinkpad Version
    Sleep     5
    PublishVersion
    Sleep     5
    CheckHeadline    Lenovo Thinkpad Version

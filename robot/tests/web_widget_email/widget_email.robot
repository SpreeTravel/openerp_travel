*** Settings ***
Documentation  Create contract
Resource       ../../../robot/keywords_8_0.robot


*** Test Cases ***
Valid Login
    Login

Set email creating company
    MainMenu    Verkauf
    SubMenu    Kunden
    Sleep    3
    KanbanButton    res.partner    oe_kanban_button_new
    Checkbox    res.partner    is_company
    Char    res.partner    name    Email Company
    Char    res.partner    email    co@mpany@email.....com
    Button    res.partner    oe_form_button_save
    Sleep    1
    Page Should Contain Element    xpath=//span[contains(@class, 'oe_form_field_email oe_form_invalid')]
    Char    res.partner    email    company@email.com
    Button    res.partner    oe_form_button_save
    Sleep    1
    Page Should Contain Element    xpath=//span[contains(@class, 'oe_form_field_email')]/a[contains(@class, 'oe_form_uri')]

Set email creating contact
    MainMenu    Verkauf
    SubMenu    Kunden
    Sleep    3
    KanbanButton    res.partner    oe_kanban_button_new
    Char    res.partner    name    Jhon Email
    Many2OneSelect    res.partner    gender_id    Herr
    NewOne2Many    res.partner    partner_email_ids
    Editable-Select-Option    res.partner.email    type    Privat
    Editable-Char   res.partner.email    name    jh@ñon@email.com
    Button    res.partner    oe_form_button_save
    Sleep    1
    Page Should Contain Element    xpath=//div[contains(@class, 'oe_list_editable')]//span[contains(@class, 'oe_form_field_email oe_form_required oe_form_invalid')]
    Editable-Char  res.partner.email    name    jhon@email.com
    Button    res.partner    oe_form_button_save
    Sleep    1
    Page Should Contain Element    xpath=//div[contains(@class, 'oe_list_editable')]//td[contains(text(), 'jhon@email.com')]

Close Browser
    Close Browser
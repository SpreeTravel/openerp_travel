*** Settings ***
Documentation  Create contract
Resource       ../keywords_8_0.robot


*** Test Cases ***
Valid Login
    Login

Create manager
    MainMenu    Verkauf
    SubMenu    Kunden
    Sleep    3
    KanbanButton    res.partner    oe_kanban_button_new
    Char    res.partner    name    LT Manager 2
    Many2OneSelect    res.partner    parent_id    Lenovo Thinkpad
    Many2OneSelect    res.partner    gender_id    Herr
    #Select-Option    res.partner    preferred_way_of_contract    Geschäftlich
    Char    res.partner    personal_number    12345
    NotebookPage    Adressen
    NewOne2Many    res.partner    child_address_ids
    Editable-Select-Option    res.partner    address_type    Geschäftlich
    Editable-Char    res.partner    email    manager2@lenovothinkpad.com
    Sleep    3
    Button    res.partner    oe_form_button_save

Add manager to a contract
    MainMenu    Verkauf
    SubMenu    Rahmenverträge
    TreeViewSelectRecord    lr.contract    partner_id    Lenovo Thinkpad
    Button     lr.contract   oe_form_button_edit
    NotebookPage    Portal
    NewOne2Many    lr.contract    manager_ids
    Many2OneSelect    lr.contract.manager    partner_id    LT Manager 2
    Many2OneSelect    lr.contract.manager    partner_company_id    Lenovo Thinkpad
    Sleep    3
    Button    lr.contract    oe_form_button_save

Send invitation
    MainMenu    Verkauf
    SubMenu    Rahmenverträge
    TreeViewSelectRecord    lr.contract    partner_id    Lenovo Thinkpad
    TopAction    Mehr    HR Manager einladen
    TreeViewSelectRecord    hr_access.wizard.user    email    manager2@lenovothinkpad.com
    Checkbox    hr_access.wizard.user    sent
    Sleep    3
    Button    hr_access.wizard.user    action_apply
    Sleep    3

Check job for email invitation
    Login    ${ODOO_URL_LOGIN}    admin    admin
    MainMenu    Connector
    Sleep    3
    SubMenu    Arbeitsschritte
    ClearFilter
    Page Should Contain Element     xpath=//div[contains(@class,'openerp')][last()]//table[contains(@class, 'oe_list_content')]//td[@data-bt-testing-model_name='queue.job' and @data-field='name'][contains(text(), 'E-Mail Einladung für Manager LT Manager 2')]

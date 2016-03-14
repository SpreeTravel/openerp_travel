*** Settings ***
Documentation    Using Hyphen '-' in slug field of Frame Contract
Resource       ../../../robot/keywords_8_0.robot


*** Test Cases ***
Valid Login
   Login

Create Contract
    MainMenu    Verkauf
    SubMenu     Rahmenverträge
    Button      lr.contract          oe_list_add
    Many2OneSelect    lr.contract    partner_id                 001 Testkunde AG
    Many2OneSelect    lr.contract    user_id                    Demo User
    Many2OneSelect    lr.contract    contract_editor            Demo User
    Float             lr.contract    number_of_employees        10
    Date              lr.contract    start_date                 26.02.2016 02:31:00
    Select-Option     lr.contract    use_input_tax_deduction    Ja (zzgl. MwSt.)
    Many2ManySelect   lr.contract    allowed_categories         Alle Produkte / JobRad / Fahrrad
    Select-Option     lr.contract    insurance                  AG/AN versichert selbst
    Select-Option     lr.contract    grant_type                 Kein Zuschuss
    NotebookPage      Portal
    #Char              lr.contract    slug                       separated-by-hyphens
    # the above keyword does work for this field! So I do it another way.
    Wait Until Page Contains Element    xpath=//input[contains(@placeholder,'nur a-z, 0-9, _ , - darf nicht mit einem Sonderzeichen beginnen')]
    Input Text    xpath=//input[contains(@placeholder,'nur a-z, 0-9, _ , - darf nicht mit einem Sonderzeichen beginnen')]    separated-by-hyphens
    Sleep    3
    Button            lr.contract    oe_form_button_save

Close Browser
    Close Browser
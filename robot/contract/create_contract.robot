*** Settings ***

Documentation  Create contract
Resource       ../keywords_8_0.robot

*** Test Cases ***
Valid Login
	Login

Create Contract
	MainMenu    67
	SubMenu    548
	Button    lr.contract    oe_list_add
	Many2OneSelect    lr.contract    partner_id    001 Testkunde AG
	Many2OneSelect    lr.contract    user_id    Holger Tumat
	Many2OneSelect    lr.contract    contract_editor    Holger Tumat
	Char    lr.contract    number_of_employees    3
	Date    lr.contract	   start_date    02/15/2016
	Select-Option    lr.contract    use_input_tax_deduction	  Yes (plus VAT)
	Select-Option    lr.contract    insurance    Always LeaseRad
	Select-Option    lr.contract    grant_type    No Grant
	Select-Option    lr.contract    allowed_categories    All / JobRad / Pedelec
	Button    lr.contract    oe_form_button_save

Active Contract
    Button    lr.contract    action_to_check
    Button    lr.contract    action_waiting_accept
    Button    lr.contract    action_active

Publish Contract
    Button     lr.contract   oe_form_button_edit
    NotebookPage    Portal
    Char    lr.contract    slug    testkunde
    Button    lr.contract    oe_form_button_save
    Button    lr.contract    website_publish_button


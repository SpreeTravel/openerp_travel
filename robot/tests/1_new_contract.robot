*** Settings ***
Documentation  Create contract
Resource       ../keywords_8_0.robot


*** Test Cases ***
Valid Login
    Login

Create Company
    MainMenu    Verkauf
    SubMenu    Kunden
    Sleep    3
    KanbanButton    res.partner    oe_kanban_button_new
    Checkbox    res.partner    is_company
    Char    res.partner    name    Lenovo Thinkpad
    Button    res.partner    oe_form_button_save

Create Employee
    MainMenu    Verkauf
    SubMenu    Kunden
    Sleep    3
    KanbanButton    res.partner    oe_kanban_button_new
    Char    res.partner    name    LT Employee 1
    Many2OneSelect    res.partner    parent_id    Lenovo Thinkpad
    Many2OneSelect    res.partner    gender_id    Herr
    Char    res.partner    personal_number    12345
    NotebookPage    Adressen
    NewOne2Many    res.partner    child_address_ids
    Editable-Select-Option    res.partner    address_type    Privat
    Editable-Char    res.partner    email    ltemployee1@lenovothinkpad.com
    Button    res.partner    oe_form_button_save

Create Contract
    MainMenu    Verkauf
    SubMenu    Rahmenverträge
    Button    lr.contract    oe_list_add
    Many2OneSelect    lr.contract    partner_id    Lenovo Thinkpad
    Many2OneSelect    lr.contract    user_id    Holger Tumat
    Many2OneSelect    lr.contract    contract_editor    Holger Tumat
    Char    lr.contract    number_of_employees    3
    Date    lr.contract    start_date    15/02/2016
    Select-Option    lr.contract    use_input_tax_deduction   Ja (zzgl. MwSt.)
    Select-Option    lr.contract    insurance    Leaserad versichert, AN trägt Versicherungsrate
    Select-Option    lr.contract    grant_type    Kein Zuschuss
    Many2ManySelect    lr.contract    allowed_categories    Alle Produkte / JobRad / Fahrrad
    NotebookPage    E-Mail Domains
    NewOne2Many    lr.contract    domain_ids
    Char    lr.contract.domain    domain    lenovothinkpad.com
    Many2OneSelect    lr.contract.domain    partner_id    Lenovo Thinkpad
    Button    lr.contract    oe_form_button_save

Activate Contract
    Button    lr.contract    action_to_check
    Button    lr.contract    action_waiting_accept
    Button    lr.contract    action_active

Create Sale Order
	MainMenu   Verkauf
	SubMenu    Angebote
	Button    sale.order    oe_list_add
	Many2OneSelect    sale.order    contract_id    Lenovo Thinkpad
	NewOne2Many    sale.order    order_line
	Many2OneSelect    product.product    categ_id	Fahrrad
	Float    product.product    lst_price    1200
	Float    product.product    retail_price    2000
	NotebookPage    Attribute
	Many2OneSelect    product.product	product_brand_id	Atlanta
	Char    product.product    attr_model    Atlanta Model
	NotebookPage    Beschaffung
	NewOne2Many    product.product    seller_ids
	Many2OneSelect    product.supplierinfo    name    2Rad Busch
	ModalButton    product.supplierinfo    oe_form_button_save_and_close
	Button	  product.product	   oe_form_button_save_and_close
	Button	  sale.order	   oe_form_button_save

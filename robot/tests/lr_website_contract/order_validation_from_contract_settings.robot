*** Settings ***
Documentation  Create contract
Resource       ../../../robot/keywords_8_0.robot


*** Test Cases ***
Valid Login
    Login

Set personal number not required in Contract
    Sleep    3
    MainMenu    Verkauf
    SubMenu    Rahmenverträge
    Sleep    3
    TreeViewSelectRecord    lr.contract    partner_id    Deutsche Bahn
    Sleep    3
    Button     lr.contract   oe_form_button_edit
    NotebookPage    Konditionen
    Select-Option    lr.contract    personal_number   kein Pflichtfeld
    Button    lr.contract    oe_form_button_save

Create Employee
    Sleep    3
    MainMenu    Verkauf
    SubMenu    Kunden
    Sleep    3
    KanbanButton    res.partner    oe_kanban_button_new
    Char    res.partner    name    Deutsche Bahn User 3
    Many2OneSelect    res.partner    parent_id    Deutsche Bahn
    Many2OneSelect    res.partner    gender_id    Herr
    NotebookPage    Adressen
    NewOne2Many    res.partner    child_address_ids
    Editable-Select-Option    res.partner    address_type    Privat
    Checkbox    res.partner    preferred
    Sleep    2
    NewOne2Many    res.partner    partner_email_ids
    Editable-Select-Option    res.partner.email    type    Privat
    Editable-Char    res.partner.email    name    bahnuser3@lr-deutschebahn.com
    Checkbox    res.partner.email    preferred
    Sleep    2
    Button    res.partner    oe_form_button_save

Create and confirm Sale Order
    Sleep    3
    MainMenu   Verkauf
    SubMenu    Angebote
    Sleep    3
    Button    sale.order    oe_list_add
    Many2OneSelect    sale.order    contract_id    Deutsche Bahn
    Many2OneSelect    sale.order    partner_shipping_id    Deutsche Bahn User 3
    Sleep    3
    NewOne2Many    sale.order    order_line
    Many2OneSelect    product.product    categ_id   Fahrrad
    Float    product.product    lst_price    1200
    Float    product.product    retail_price    2000
    NotebookPage    Attribute
    Many2OneSelect    product.product    product_brand_id    Atlanta
    Char    product.product    attr_model    Atlanta Model
    NotebookPage    Beschaffung
    NewOne2Many    product.product    seller_ids
    Many2OneSelect    product.supplierinfo    name    2Rad Busch
    ModalButton    product.supplierinfo    oe_form_button_save_and_close
    Button    product.product     oe_form_button_save_and_close
    Button    sale.order    oe_form_button_save
    Button    sale.order    action_button_confirm

Set personal number required in Contract
    Sleep    3
    MainMenu    Verkauf
    SubMenu    Rahmenverträge
    Sleep    3
    TreeViewSelectRecord    lr.contract    partner_id    Deutsche Bahn
    Button     lr.contract   oe_form_button_edit
    NotebookPage    Konditionen
    Select-Option    lr.contract    personal_number   Pflichtfeld
    Button    lr.contract    oe_form_button_save

Access related purchase orders from Sale Order
    Sleep    3
    MainMenu   Verkauf
    SubMenu    Aufträge
    Sleep    3
    TreeViewSelectRecord    sale.order    partner_shipping_id    Deutsche Bahn User 3
    Button    sale.order    open_purchase_orders

Close Browser
    Close Browser

*** Settings ***

Documentation  Create Sale Order
Resource       ../keywords_8_0.robot

*** Test Cases ***

Valid Login
	Login

Create Sale Order
	MainMenu   Ventas
	sleep      5
	SubMenu    Pedidos de ventas    1
	sleep      5
	Button     sale.order    oe_list_add
	sleep      5
	Many2OneSelect  sale.order    partner_id    John Smith
	sleep      5
	Date  sale.order    date_order    11/03/2016
	sleep  5
	Date  sale.order    end_date    20/03/2016
	sleep  5
	NewOne2Many  sale.order    order_line

Create Sale Order Line Flight F1
    Many2OneSelect  sale.order.line    category_id    Vuelo
    sleep  5
    Many2OneSelect  sale.order.line    product_id    MADRID-HABANA
    sleep  5
    Date  sale.order.line    start_date    11/03/2016
    sleep  5
    Date  sale.order.line    end_date    11/03/2016
    sleep  5
    Char  sale.order.line    adults    2
    sleep  5
    Char  sale.order.line    children    1
    sleep  5
    Many2OneSelect  sale.order.line    supplier_id    COPA AIRLINES
    sleep  5
    Button  sale.order.line    oe_form_button_save_and_close
    sleep  5
    #add item
    NewOne2Many  sale.order    order_line

Create Sale Order Line Car
    Many2OneSelect  sale.order.line    category_id    Auto
    sleep  5
    Many2OneSelect  sale.order.line    product_id    Peugeot
    sleep  5
    Date  sale.order.line    start_date    11/03/2016
    sleep  5
    Date  sale.order.line    end_date    19/03/2016
    sleep  5
    Char  sale.order.line    adults    2
    sleep  5
    Char  sale.order.line    children    1
    sleep  5
    Many2OneSelect  sale.order.line    supplier_id    CUBACAR
    sleep  5
    Button  sale.order.line    oe_form_button_save_and_close
    sleep  5
    NewOne2Many  sale.order    order_line

Create Sale Order Line Hotel
    Many2OneSelect  sale.order.line    category_id    Hotel
    sleep  5
    Many2OneSelect  sale.order.line    product_id    Hotel Nacional de Cuba
    sleep  5
    Date  sale.order.line    start_date    11/03/2016
    sleep  5
    Date  sale.order.line    end_date    19/03/2016
    sleep  5
    Rooming-Char  sale.rooming    children    1
    sleep  8
    Many2OneSelect  sale.order.line    hotel_2_meal_plan_id    AP
    sleep  5
    Many2OneSelect  sale.order.line    supplier_id    CUBANACAN HOTELES
    sleep  5
    Button  sale.order.line    oe_form_button_save_and_close
    sleep  5
    NewOne2Many  sale.order    order_line

Create Sale Order Line Flight F2
    Many2OneSelect  sale.order.line    category_id    Vuelo
    sleep  5
    Many2OneSelect  sale.order.line    product_id    HABANA-MADRID
    sleep  5
    Date  sale.order.line    start_date    19/03/2016
    sleep  5
    Date  sale.order.line    end_date    20/03/2016
    sleep  5
    Char  sale.order.line    adults    2
    sleep  5
    Char  sale.order.line    children    1
    sleep  5
    Many2OneSelect  sale.order.line    supplier_id    CUBANA DE AVIACION
    sleep  5

Save Sale Order
    Button  sale.order.line    oe_form_button_save_and_close
    sleep  5
    Button  sale.order    oe_form_button_save

Confirm Sale
    Button  sale.order    action_button_confirm
    sleep  5

Create Invoice
    Button  sale.order    303
    sleep  5
    #Button  sale.advance.payment.inv    create_invoices
    Wait Until Page Contains Element    xpath=//div[contains(@class,'openerp')][last()]//*[not(contains(@style,'display:none'))]//button[@data-bt-testing-name='create_invoices']
    Wait Until Element Is Visible    xpath=//div[contains(@class,'openerp')][last()]//*[not(contains(@style,'display:none'))]//button[@data-bt-testing-name='create_invoices']    20
    Click Button           xpath=(//div[contains(@class,'openerp')][last()]//*[not(contains(@style,'display:none'))]//button[@data-bt-testing-name='create_invoices'])[2]
    Wait For Condition     return true;    20.0
    ElementPostCheck
    sleep  5

View Invoice
    MainMenu  Contabilidad
    sleep  5
    TreeViewSelectRecord  account.invoice    origin    SO087
    sleep  5

View Supplier Invoice
    SubMenu  Facturas de proveedor    1
    sleep  5
    TreeViewSelectRecord  account.invoice    origin    SO087
    sleep  5


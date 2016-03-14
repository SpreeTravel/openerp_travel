*** Settings ***

Documentation  Create Sale Order
Resource       ../keywords_8_0.robot

*** Test Cases ***
Valid Login
	Login

Create Sale Order
	MainMenu   67
	SubMenu    512
	Button    sale.order    oe_list_add
	Many2OneSelect    sale.order    contract_id    Deutsche Bahn
	NewOne2Many    sale.order    order_line
	Many2OneSelect    product.product    categ_id	All / JobRad / Pedelec
	Float    product.product    lst_price    32.0
	Float    product.product    retail_price    32.0
	NotebookPage    Attributes
	Many2OneSelect    product.product	product_brand_id	Atlanta
	Char    product.product    attr_model    Atlanta Model
	Button	sale.order.line	   oe_form_button_save_and_close
	Button	sale.order	   oe_form_button_save

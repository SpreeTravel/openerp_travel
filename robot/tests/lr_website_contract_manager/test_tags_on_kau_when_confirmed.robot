*** Settings ***
Documentation  Check JobRadler tag on confirmed KAU
Resource       ../../../robot/keywords_8_0.robot


*** Test Cases ***
Valid Login
    Login

Create Sale Order
	MainMenu   Verkauf
	SubMenu    Angebote
	Button    sale.order    oe_list_add
	Many2OneSelect    sale.order    contract_id    Deutsche Bahn
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
	Button    sale.order    action_button_confirm

Check JobRadler Tag
    Wait Until Page Contains Element    xpath=//div[contains(@class,'oe_form')]//div//div//table//tbody//tr//td[1]//table//tbody//tr[3]//td//span//a[contains(@class,'oe_form_uri')]
    Click Link     xpath=//div[contains(@class,'oe_form')]//div//div//table//tbody//tr//td[1]//table//tbody//tr[3]//td//span//a[contains(@class,'oe_form_uri')]
    Wait Until Page Contains Element    xpath=//span[contains(@class,'oe_tag')]
    Element Should Contain    xpath=//span[contains(@class,'oe_tag')]    JobRad

Close Browser
    Close Browser

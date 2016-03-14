*** Settings ***

Documentation  Create Product Hotel
Resource       ../keywords_8_0.robot

*** Test Cases ***

Valid Login
    sleep  3
	Login

Create Product Hotel
    sleep  4
	MainMenu   Ventas
	sleep      1
	SubMenu    Hoteles    2
	sleep      2
	Button    product.hotel    oe_list_add
	sleep  1
	Char  product.hotel    name    Hotel Nacional de Cuba
	sleep  1
	Select-Option  product.hotel    stars    4
	sleep  1
	Many2OneSelect   product.hotel    destination    HAVANA
	sleep  2
	Many2OneSelect   product.hotel    chain_id    GRAN CARIBE
	sleep  1
	Many2OneSelect   product.hotel    res_partner_id    AGENCIA DE VIAJES COMELY
	sleep  1
	Click Link    xpath=//a[@id='ui-id-2']
	sleep  1
	NewOne2Many  product.hotel    seller_ids
	sleep  1

Create Product SupplierInfo
	Many2OneSelect   product.supplierinfo    name    CUBANACAN HOTELES
	sleep  1
	ElementPreCheck        xpath=//div[contains(@class,'openerp')][last()]//div[contains(@class,'oe_form_field_one2many')]//div[@data-bt-testing-submodel_name='pricelist.partnerinfo' and @data-bt-testing-name='pricelist_ids']//tr/td[contains(@class,'oe_form_field_one2many_list_row_add')]/a
    Click Link             xpath=//div[contains(@class,'openerp')][last()]//div[contains(@class,'oe_form_field_one2many')]//div[@data-bt-testing-submodel_name='pricelist.partnerinfo' and @data-bt-testing-name='pricelist_ids']//tr/td[contains(@class,'oe_form_field_one2many_list_row_add')]/a
    sleep  1

Create Pricelist Partnerinfo
    #Date
    Input Text             xpath=//div[contains(@class,'openerp')][last()]//input[@data-bt-testing-model_name='pricelist.partnerinfo' and @data-bt-testing-name='start_date']    08/03/2016
	sleep  1
	#Date
	Input Text             xpath=//div[contains(@class,'openerp')][last()]//input[@data-bt-testing-model_name='pricelist.partnerinfo' and @data-bt-testing-name='end_date']    18/03/2016
	sleep  1
	#Many2One
	Input Text		    xpath=//div[contains(@class,'openerp')][last()]//input[@data-bt-testing-model_name='pricelist.partnerinfo' and @data-bt-testing-name='room_type_id']    STANDARD
    sleep  1
    Click Link             xpath=//ul[contains(@class,'ui-autocomplete') and not(contains(@style,'display: none'))]/li[1]/a
	sleep  1
	#Many2One
	Input Text		    xpath=//div[contains(@class,'openerp')][last()]//input[@data-bt-testing-model_name='pricelist.partnerinfo' and @data-bt-testing-name='meal_plan_id']    AP
    sleep  1
    Click Link             xpath=//ul[contains(@class,'ui-autocomplete') and not(contains(@style,'display: none'))]/li[1]/a
    sleep  1
    #Float
    Input Text             xpath=//div[contains(@class,'openerp')][last()]//input[@data-bt-testing-model_name='pricelist.partnerinfo' and @data-bt-testing-name='simple']    90.00
    sleep  1
    #Float
    Input Text             xpath=//div[contains(@class,'openerp')][last()]//input[@data-bt-testing-model_name='pricelist.partnerinfo' and @data-bt-testing-name='price']    70.00
    sleep  1
    #Float
    Input Text             xpath=//div[contains(@class,'openerp')][last()]//input[@data-bt-testing-model_name='pricelist.partnerinfo' and @data-bt-testing-name='triple']    60.00
    sleep  1
    #Float
    Input Text             xpath=//div[contains(@class,'openerp')][last()]//input[@data-bt-testing-model_name='pricelist.partnerinfo' and @data-bt-testing-name='extra_adult']    10.0
    sleep  1
    #Float
    Input Text             xpath=//div[contains(@class,'openerp')][last()]//input[@data-bt-testing-model_name='pricelist.partnerinfo' and @data-bt-testing-name='child']    5.0
    sleep  1
    #Float
    Input Text             xpath=//div[contains(@class,'openerp')][last()]//input[@data-bt-testing-model_name='pricelist.partnerinfo' and @data-bt-testing-name='second_child']    3.0
    sleep  1
    #SelectOne2Many
    ElementPreCheck        xpath=//div[contains(@class,'openerp')][last()]//div[contains(@class,'oe_form_field_one2many')]//div[@data-bt-testing-submodel_name='product.rate.supplement' and @data-bt-testing-name='supplement_ids']//tr/td[contains(@class,'oe_form_field_one2many_list_row_add')]/a
    Click Link             xpath=//div[contains(@class,'openerp')][last()]//div[contains(@class,'oe_form_field_one2many')]//div[@data-bt-testing-submodel_name='product.rate.supplement' and @data-bt-testing-name='supplement_ids']//tr/td[contains(@class,'oe_form_field_one2many_list_row_add')]/a

Create Product Rate Supplement
    LineDate  product.rate.supplement    start_date    08/03/2016
	sleep  1
	LineDate  product.rate.supplement    end_date    08/03/2016
	sleep  1
	#LineMany2OneSelect  product.rate.supplement    supplement_id    Aniversario de Bodas
	Input Text		    xpath=//div[contains(@class,'openerp')][last()]//input[@data-bt-testing-model_name='product.rate.supplement' and @data-bt-testing-name='supplement_id']    Aniversario de Bodas
    sleep  1
    Click Link             xpath=//ul[contains(@class,'ui-autocomplete') and not(contains(@style,'display: none'))]/li[3]/a
	sleep  1
	LineFloat  product.rate.supplement    price    20.0
	sleep  1

Save Product
    Button  product.supplierinfo    oe_form_button_save_and_close
    sleep  1
    Button  product.hotel    oe_form_button_save
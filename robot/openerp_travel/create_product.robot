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
	sleep      5
	SubMenu    Hoteles    2
	sleep      5
	Button    product.hotel    oe_list_add
	sleep  5
	Char  product.hotel    name    Hotel Nacional de Cuba
	sleep  5
	Select-Option  product.hotel    stars    4
	sleep  5
	Many2OneSelect   product.hotel    destination    HAVANA
	sleep  5
	Many2OneSelect   product.hotel    chain_id    GRAN CARIBE
	sleep  5
	Many2OneSelect   product.hotel    res_partner_id    AGENCIA DE VIAJES COMELY
	sleep  5
	Click Link    xpath=//a[@id='ui-id-2']
	sleep  5
	NewOne2Many  product.hotel    seller_ids
	sleep  5

Create Product SupplierInfo
	Many2OneSelect   product.supplierinfo    name    CUBANACAN HOTELES
	sleep  1
	ElementPreCheck        xpath=//div[contains(@class,'openerp')][last()]//div[contains(@class,'oe_form_field_one2many')]//div[@data-bt-testing-submodel_name='pricelist.partnerinfo' and @data-bt-testing-name='pricelist_ids']//tr/td[contains(@class,'oe_form_field_one2many_list_row_add')]/a
    Click Link             xpath=//div[contains(@class,'openerp')][last()]//div[contains(@class,'oe_form_field_one2many')]//div[@data-bt-testing-submodel_name='pricelist.partnerinfo' and @data-bt-testing-name='pricelist_ids']//tr/td[contains(@class,'oe_form_field_one2many_list_row_add')]/a
    sleep  5

Create Pricelist Partnerinfo
    #Date
    Input Text             xpath=//div[contains(@class,'openerp')][last()]//input[@data-bt-testing-model_name='pricelist.partnerinfo' and @data-bt-testing-name='start_date']    08/03/2016
	sleep  5
	#Date
	Input Text             xpath=//div[contains(@class,'openerp')][last()]//input[@data-bt-testing-model_name='pricelist.partnerinfo' and @data-bt-testing-name='end_date']    18/03/2016
	sleep  5
	#Many2One
	Input Text		    xpath=//div[contains(@class,'openerp')][last()]//input[@data-bt-testing-model_name='pricelist.partnerinfo' and @data-bt-testing-name='room_type_id']    STANDARD
    sleep  5
    Click Link             xpath=//ul[contains(@class,'ui-autocomplete') and not(contains(@style,'display: none'))]/li[1]/a
	sleep  5
	#Many2One
	Input Text		    xpath=//div[contains(@class,'openerp')][last()]//input[@data-bt-testing-model_name='pricelist.partnerinfo' and @data-bt-testing-name='meal_plan_id']    AP
    sleep  5
    Click Link             xpath=//ul[contains(@class,'ui-autocomplete') and not(contains(@style,'display: none'))]/li[1]/a
    sleep  5
    #Float
    Input Text             xpath=//div[contains(@class,'openerp')][last()]//input[@data-bt-testing-model_name='pricelist.partnerinfo' and @data-bt-testing-name='simple']    90.00
    sleep  5
    #Float
    Input Text             xpath=//div[contains(@class,'openerp')][last()]//input[@data-bt-testing-model_name='pricelist.partnerinfo' and @data-bt-testing-name='price']    70.00
    sleep  5
    #Float
    Input Text             xpath=//div[contains(@class,'openerp')][last()]//input[@data-bt-testing-model_name='pricelist.partnerinfo' and @data-bt-testing-name='triple']    60.00
    sleep  5
    #Float
    Input Text             xpath=//div[contains(@class,'openerp')][last()]//input[@data-bt-testing-model_name='pricelist.partnerinfo' and @data-bt-testing-name='extra_adult']    10.0
    sleep  5
    #Float
    Input Text             xpath=//div[contains(@class,'openerp')][last()]//input[@data-bt-testing-model_name='pricelist.partnerinfo' and @data-bt-testing-name='child']    5.0
    sleep  5
    #Float
    Input Text             xpath=//div[contains(@class,'openerp')][last()]//input[@data-bt-testing-model_name='pricelist.partnerinfo' and @data-bt-testing-name='second_child']    3.0
    sleep  5
    #SelectOne2Many
    ElementPreCheck        xpath=//div[contains(@class,'openerp')][last()]//div[contains(@class,'oe_form_field_one2many')]//div[@data-bt-testing-submodel_name='product.rate.supplement' and @data-bt-testing-name='supplement_ids']//tr/td[contains(@class,'oe_form_field_one2many_list_row_add')]/a
    Click Link             xpath=//div[contains(@class,'openerp')][last()]//div[contains(@class,'oe_form_field_one2many')]//div[@data-bt-testing-submodel_name='product.rate.supplement' and @data-bt-testing-name='supplement_ids']//tr/td[contains(@class,'oe_form_field_one2many_list_row_add')]/a

Create Product Rate Supplement
    LineDate  product.rate.supplement    start_date    08/03/2016
	sleep  5
	LineDate  product.rate.supplement    end_date    08/03/2016
	sleep  5
	#LineMany2OneSelect  product.rate.supplement    supplement_id    Aniversario de Bodas
	Input Text		    xpath=//div[contains(@class,'openerp')][last()]//input[@data-bt-testing-model_name='product.rate.supplement' and @data-bt-testing-name='supplement_id']    Aniversario de Bodas
    sleep  5
    Click Link             xpath=//ul[contains(@class,'ui-autocomplete') and not(contains(@style,'display: none'))]/li[3]/a
	sleep  5
	LineFloat  product.rate.supplement    price    20.0
	sleep  5

Save Product
    Button  product.supplierinfo    oe_form_button_save_and_close
    sleep  5
    Button  product.hotel    oe_form_button_save
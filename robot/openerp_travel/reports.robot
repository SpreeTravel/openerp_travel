*** Settings ***

Documentation  Reports
Resource       ../keywords_8_0.robot

*** Test Cases ***
Valid Login
	Login

See Reservations
	MainMenu   Ventas
	sleep      5
	SubMenu    Hoteles    1
	sleep      5
	SubMenu    Vuelos    1
	sleep      5

See Sale Analysis
    MainMenu  Informes
    sleep  5
    SubMenu  Análisis de ventas    1
    sleep  5
    click element  xpath=(//td[descendant::span/text()[normalize-space()='Total']])[2]/span
    sleep  5
    click element  xpath=(//td[descendant::span/text()[normalize-space()='Total']])[2]/span
    sleep  5
    click element  xpath=//li[descendant::a/text()[normalize-space()='Cliente']]
    sleep  5
    click element  xpath=//ul[descendant::li/text()[normalize-space()='Proveedor']]/li[@data-index=2]
    sleep  5
    click element  xpath=//th[descendant::span/text()[normalize-space()='enero 2016']]
    sleep  5
    click element  xpath=//li[descendant::a/text()[normalize-space()='Categorías']]
    Scroll Page To Location  0
    sleep  6

See Flight Report
    SubMenu  Reporte de Vuelo    1
    sleep  5
    click element  xpath=//div[@class='oe_searchview_unfold_drawer']
    sleep  5
    click element  xpath=//ul[descendant::li/text()[normalize-space()='Proveedor']]/li[@data-index=0]
    sleep  5

See Hotel Report
    SubMenu  Reporte de Hoteles    1
    sleep  5
    click element  xpath=//div[@class='oe_searchview_unfold_drawer']
    sleep  5
    click element  xpath=//ul[descendant::li/text()[normalize-space()='Nombre']]/li[@data-index=5]
    sleep  5


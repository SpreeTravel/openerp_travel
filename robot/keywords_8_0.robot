*** Settings ***

Documentation  Common keywords for OpenERP tests
...            versions of the application. The correct SUT specific resource
...            is imported based on ${SUT} variable. SeleniumLibrary is also
...            imported here so that no other file needs to import it.
Library     Selenium2Library
Library     String
Variables   ${CONFIG}


*** Keywords ***
# checked: 8.0 ok
Login    [Arguments]    ${url}=${ODOO_URL_LOGIN}    ${user}=${ODOO_USER}    ${password}=${ODOO_PASSWORD}    ${db}=${ODOO_DB}
    Open Browser                        ${url}  ${BROWSER}  ${ALIAS}
    Maximize Browser Window
    Go To                               ${url}
    Set Selenium Speed                  ${SELENIUM_DELAY}
    Set Selenium Timeout                ${SELENIUM_TIMEOUT}
    Set Selenium Implicit Wait          ${SELENIUM_TIMEOUT}
    sleep  2
    #select from list by value           name=db  ${db}
    #Wait Until Page Contains Element    name=login
    Input Text                          name=login  ${user}
    Input Password                      name=password   ${password}
    sleep  1
    Click Button                        xpath=//div[contains(@class,'oe_login_buttons')]/button[@type='submit']
    Wait Until Page Contains Element    xpath=//div[@id='oe_main_menu_placeholder']/ul/li/a/span

LoginNoNewBrowser    [Arguments]    ${url}=${ODOO_URL_LOGIN}    ${user}=${ODOO_USER}    ${password}=${ODOO_PASSWORD}    ${db}=${ODOO_DB}
    Go To                               ${url}
    Wait Until Page Contains Element    name=login
    Input Text                          name=login  ${user}
    Input Password                      name=password   ${password}
    Click Button                        xpath=//div[contains(@class,'oe_login_buttons')]/button[@type='submit']
    Wait Until Page Contains Element    xpath=//div[@id='oe_main_menu_placeholder']/ul/li/a/span

# checked: 8.0 ok
MainMenu    [Arguments]    ${menu}
    Wait Until Element Is Visible    xpath=//div[@id='oe_main_menu_placeholder']/ul/li/a[descendant::span/text()[normalize-space()='${menu}']]    ${SELENIUM_TIMEOUT}
	Click Link				xpath=//div[@id='oe_main_menu_placeholder']/ul/li/a[descendant::span/text()[normalize-space()='${menu}']]
	Wait Until Page Contains Element	xpath=//div[contains(@class, 'oe_secondary_menus_container')]/div[contains(@class, 'oe_secondary_menu') and not(contains(@style, 'display: none'))]
	ElementPostCheck

LineDate    [Arguments]    ${model}    ${field}    ${value}
    Input Text             xpath=//div[contains(@class,'openerp')][last()]//input[@data-bt-testing-model_name='${model}' and @data-bt-testing-name='${field}']    ${value}

LineFloat    [Arguments]    ${model}    ${field}    ${value}
    Input Text             xpath=//div[contains(@class,'openerp')][last()]//input[@data-bt-testing-model_name='${model}' and @data-bt-testing-name='${field}']    ${value}

LineMany2OneSelect    [Arguments]    ${model}    ${field}    ${value}
    Input Text		    xpath=//div[contains(@class,'openerp')][last()]//input[@data-bt-testing-model_name='${model}' and @data-bt-testing-name='${field}']    ${value}
    sleep  1
    Click Link             xpath=//ul[contains(@class,'ui-autocomplete') and not(contains(@style,'display: none'))]/li[1]/a


Scroll Page To Location    [Arguments]    ${x_location}
    Execute JavaScript    window.scrollTo(${x_location},document.body.scrollHeight)

SubMenu    [Arguments]    ${menu}    ${pos}
    Wait Until Element Is Visible	xpath=//td[contains(@class,'oe_leftbar')]//ul/li/a[descendant::span/text()[normalize-space()='${menu}']]    ${SELENIUM_TIMEOUT}
    Click Link				xpath=(//td[contains(@class,'oe_leftbar')]//ul/li/a[descendant::span/text()[normalize-space()='${menu}']])[${pos}]
    Wait Until Page Contains Element   xpath=//div[contains(@class,'oe_view_manager_current')]

ChangeView    [Arguments]    ${view}
   Click Link                          xpath=//div[contains(@class,'openerp')][last()]//div[contains(@class,'oe-view-manager-switch')]//button[contains(@data-view-type,'${view}')]
   Wait Until Page Contains Element    xpath=//div[contains(@class,'openerp')][last()]//div[contains(@class,'oe-view-manager-view-${view}') and not(contains(@style, 'display: none'))]
   ElementPostCheck

# Checks that are done always before a element is executed
ElementPreCheck    [Arguments]    ${element}
	Execute Javascript      console.log("${element}");
	# Element may be in a tab. So click the parent tab. If there is no parent tab, forget about the result
    Execute Javascript      var path="${element}".replace('xpath=','');var id=document.evaluate("("+path+")/ancestor::div[contains(@class,'oe_notebook_page')]/@id",document,null,XPathResult.STRING_TYPE,null).stringValue; if(id != ''){ window.location = "#"+id; $("a[href='#"+id+"']").click(); console.log("Clicked at #" + id); } return true;

ElementPostCheck
   # Check that page is not blocked by RPC Call
   Wait Until Page Contains Element    xpath=//body[not(contains(@class, 'oe_wait'))]
   # Wait Until Page Contains Element    xpath=//div[contains(@class,'openerp_webclient_container') and not(contains(@class, 'oe_wait'))]

WriteInField                [Arguments]     ${model}    ${fieldname}    ${value}
    ElementPreCheck         xpath=//div[contains(@class,'openerp')][last()]//input[@data-bt-testing-model_name='${model}' and @data-bt-testing-name='${fieldname}']|textarea[@data-bt-testing-model_name='${model}' and @data-bt-testing-name='${fieldname}']
    Input Text              xpath=//div[contains(@class,'openerp')][last()]//input[@data-bt-testing-model_name='${model}' and @data-bt-testing-name='${fieldname}']|textarea[@data-bt-testing-model_name='${model}' and @data-bt-testing-name='${fieldname}']    ${value}

Button                      [Arguments]     ${model}    ${button_name}
    Wait Until Page Contains Element    xpath=//div[contains(@class,'openerp')][last()]//*[not(contains(@style,'display:none'))]//button[@data-bt-testing-name='${button_name}']
    Wait Until Element Is Visible    xpath=//div[contains(@class,'openerp')][last()]//*[not(contains(@style,'display:none'))]//button[@data-bt-testing-name='${button_name}']    ${SELENIUM_TIMEOUT}
    Click Button           xpath=//div[contains(@class,'openerp')][last()]//*[not(contains(@style,'display:none'))]//button[@data-bt-testing-name='${button_name}']
    Wait For Condition     return true;    20.0
    ElementPostCheck

Many2OneSelect    [Arguments]    ${model}    ${field}    ${value}
    ElementPreCheck	    xpath=//div[contains(@class,'openerp')][last()]//input[@data-bt-testing-model_name='${model}' and @data-bt-testing-name='${field}']
    Input Text		    xpath=//div[contains(@class,'openerp')][last()]//input[@data-bt-testing-model_name='${model}' and @data-bt-testing-name='${field}']    ${value}
    sleep  1
    Click Link             xpath=//ul[contains(@class,'ui-autocomplete') and not(contains(@style,'display: none'))]/li[1]/a
    Textfield Should Contain    xpath=//div[contains(@class,'openerp')][last()]//input[@data-bt-testing-model_name='${model}' and @data-bt-testing-name='${field}']    ${value}
    ElementPostCheck

Date    [Arguments]    ${model}    ${field}    ${value}
    ElementPreCheck        xpath=//div[contains(@class,'openerp')][last()]//input[@data-bt-testing-model_name='${model}' and @data-bt-testing-name='${field}']
    Input Text             xpath=//div[contains(@class,'openerp')][last()]//input[@data-bt-testing-model_name='${model}' and @data-bt-testing-name='${field}']    ${value}
    ElementPostCheck

Char    [Arguments]    ${model}    ${field}    ${value}
    ElementPreCheck        xpath=//div[contains(@class,'openerp')][last()]//input[@data-bt-testing-model_name='${model}' and @data-bt-testing-name='${field}']
    Execute Javascript     $("div.openerp:last input[data-bt-testing-model_name='${model}'][data-bt-testing-name='${field}']").val(''); return true;
    Input Text             xpath=//div[contains(@class,'openerp')][last()]//input[@data-bt-testing-model_name='${model}' and @data-bt-testing-name='${field}']    ${value}
    ElementPostCheck

Float    [Arguments]    ${model}    ${field}    ${value}
    ElementPreCheck        xpath=//div[contains(@class,'openerp')][last()]//input[@data-bt-testing-model_name='${model}' and @data-bt-testing-name='${field}']
    Input Text             xpath=//div[contains(@class,'openerp')][last()]//input[@data-bt-testing-model_name='${model}' and @data-bt-testing-name='${field}']    ${value}
    ElementPostCheck

Text    [Arguments]    ${model}    ${field}    ${value}
    ElementPreCheck        xpath=//div[contains(@class,'openerp')][last()]//textarea[@data-bt-testing-model_name='${model}' and @data-bt-testing-name='${field}']
    Input Text             xpath=//div[contains(@class,'openerp')][last()]//textarea[@data-bt-testing-model_name='${model}' and @data-bt-testing-name='${field}']    ${value}
    ElementPostCheck

Select-Option    [Arguments]    ${model}    ${field}    ${value}    
    ElementPreCheck              xpath=//div[contains(@class,'openerp')][last()]//select[@data-bt-testing-model_name='${model}' and @data-bt-testing-name='${field}']
    Select From List By Label    xpath=//div[contains(@class,'openerp')][last()]//select[@data-bt-testing-model_name='${model}' and @data-bt-testing-name='${field}']    ${value}
    ElementPostCheck

Checkbox    [Arguments]    ${model}    ${field}
    ElementPreCheck        xpath=//div[contains(@class,'openerp')][last()]//input[@type='checkbox' and @data-bt-testing-name='${field}' and @data-bt-testing-model_name='${model}']
    Checkbox Should Not Be Selected	xpath=//div[contains(@class,'openerp')][last()]//input[@type='checkbox' and @data-bt-testing-name='${field}' and @data-bt-testing-model_name='${model}']
    Click Element          xpath=//div[contains(@class,'openerp')][last()]//input[@type='checkbox' and @data-bt-testing-name='${field}' and @data-bt-testing-model_name='${model}']
    ElementPostCheck

NotebookPage    [Arguments]    ${value}
    Click Element    xpath=//div[contains(@class,'openerp')][last()]//ul[@role='tablist']//li/a[@data-bt-testing-original-string='${value}']

NewOne2Many    [Arguments]    ${model}    ${field}
    ElementPreCheck        xpath=//div[contains(@class,'openerp')][last()]//div[contains(@class,'oe_form_field_one2many')]//div[@data-bt-testing-model_name='${model}' and @data-bt-testing-name='${field}']//tr/td[contains(@class,'oe_form_field_one2many_list_row_add')]/a
    Click Link             xpath=//div[contains(@class,'openerp')][last()]//div[contains(@class,'oe_form_field_one2many')]//div[@data-bt-testing-model_name='${model}' and @data-bt-testing-name='${field}']//tr/td[contains(@class,'oe_form_field_one2many_list_row_add')]/a
    ElementPostCheck

One2ManySelectRecord  [Arguments]    ${model}    ${field}    ${submodel}    @{fields}
    ElementPreCheck    xpath=//div[@data-bt-testing-model_name='${model}' and @data-bt-testing-name='${field}']

    # Initialize variable
    ${pre_check_xpath}=    Set Variable
    ${post_check_xpath}=    Set Variable
    ${pre_click_xpath}=    Set Variable
    ${post_click_xpath}=    Set Variable
    ${pre_check_xpath}=    Catenate    (//div[@data-bt-testing-model_name='${model}' and @data-bt-testing-name='${field}']//table[contains(@class,'oe_list_content')]//tr[descendant::td[
    ${post_check_xpath}=    Catenate    ]])[1]
    ${pre_click_xpath}=    Catenate    (//div[@data-bt-testing-model_name='${model}' and @data-bt-testing-name='${field}']//table[contains(@class,'oe_list_content')]//tr[
    ${post_click_xpath}=    Catenate    ]/td)[1]
    ${xpath}=    Set Variable

    # Got throught all field=value and to select the correct record
    : FOR    ${field}    IN  @{fields}
    # Split the string in fieldname=fieldvalue
    \    ${fieldname}    ${fieldvalue}=    Split String    ${field}    separator==    max_split=1
    \    ${fieldxpath}=    Catenate    @data-bt-testing-model_name='${submodel}' and @data-field='${fieldname}'

         # We first check if this field is in the view and visible
         # otherwise a single field can break the whole command

    \    ${checkxpath}=     Catenate    ${pre_check_xpath} ${fieldxpath} ${post_check_xpath}
    \    Log To Console    ${checkxpath}
    \    ${status}    ${value}=    Run Keyword And Ignore Error    Page Should Contain Element    xpath=${checkxpath}

         # In case the field is not there, log a error
    \    Run Keyword Unless     '${status}' == 'PASS'    Log    Field ${fieldname} not in the view or unvisible
         # In case the field is there, add the path to the xpath
    \    ${xpath}=    Set Variable If    '${status}' == 'PASS'    ${xpath} and descendant::td[${fieldxpath} and string()='${fieldvalue}']    ${xpath}

    # remove first " and " again (5 characters)
    ${xpath}=   Get Substring    ${xpath}    5
    ${xpath}=    Catenate    ${pre_click_xpath}    ${xpath}    ${post_click_xpath}
    Click Element    xpath=${xpath}
    ElementPostCheck

SelectListView  [Arguments]    ${model}    @{fields}
    # Initialize variable
    ${xpath}=    Set Variable

    # Got throught all field=value and to select the correct record
    : FOR    ${field}    IN  @{fields}
    # Split the string in fieldname=fieldvalue
    \    ${fieldname}    ${fieldvalue}=    Split String    ${field}    separator==    max_split=1
    \    ${fieldxpath}=    Catenate    @data-bt-testing-model_name='${model}' and @data-field='${fieldname}'

         # We first check if this field is in the view and visible
         # otherwise a single field can break the whole command

    \    ${checkxpath}=     Catenate    (//table[contains(@class,'oe_list_content')]//tr[descendant::td[${fieldxpath}]])[1]
    \    ${status}    ${value}=    Run Keyword And Ignore Error    Page Should Contain Element    xpath=${checkxpath}

         # In case the field is not there, log a error
    \    Run Keyword Unless     '${status}' == 'PASS'    Log    Field ${fieldname} not in the view or unvisible
         # In case the field is there, add the path to the xpath
    \    ${xpath}=    Set Variable If    '${status}' == 'PASS'    ${xpath} and descendant::td[${fieldxpath} and string()='${fieldvalue}']    ${xpath}

    # remove first " and " again (5 characters)
    ${xpath}=   Get Substring    ${xpath}    5
    ${xpath}=    Catenate    (//table[contains(@class,'oe_list_content')]//tr[${xpath}]/td)[1]
    Click Element    xpath=${xpath}
    ElementPostCheck

SidebarAction  [Arguments]    ${type}    ${id}
    Click Element   xpath=//div[contains(@class,'oe_view_manager_sidebar')]/div[not(contains(@style,'display: none'))]//div[contains(@class,'oe_sidebar')]//div[contains(@class,'oe_form_dropdown_section') and descendant::a[@data-bt-type='${type}' and @data-bt-id='${id}']]/button[contains(@class,'oe_dropdown_toggle')]
    Click Link   xpath=//div[contains(@class,'oe_view_manager_sidebar')]/div[not(contains(@style,'display: none'))]//div[contains(@class,'oe_sidebar')]//a[@data-bt-type='${type}' and @data-bt-id='${id}']
    ElementPostCheck

MainWindowButton            [Arguments]     ${button_text}
    Click Button            xpath=//td[@class='oe_application']//div[contains(@class,'oe_view_manager_current')]//button[contains(text(), '${button_text}')]
    ElementPostCheck

MainWindowNormalField       [Arguments]     ${field}    ${value}
    Input Text              xpath=//td[contains(@class, 'view-manager-main-content')]//input[@name='${field}']  ${value}
    ElementPostCheck

MainWindowSearchTextField   [Arguments]     ${field}    ${value}
    Input Text              xpath=//div[@id='oe_app']//div[contains(@id, '_search')]//input[@name='${field}']   ${value}
    ElementPostCheck
    
MainWindowMany2One          [Arguments]     ${field}    ${value}
    Click Element           xpath=//td[contains(@class, 'view-manager-main-content')]//input[@name='${field}']  don't wait
    Input Text              xpath=//td[contains(@class, 'view-manager-main-content')]//input[@name='${field}']      ${value}
    Click Element           xpath=//td[contains(@class, 'view-manager-main-content')]//input[@name='${field}']/following-sibling::span[contains(@class, 'oe-m2o-drop-down-button')]/img don't wait
    Click Link              xpath=//ul[contains(@class, 'ui-autocomplete') and not(contains(@style, 'display: none'))]//a[self::*/text()='${value}']    don't wait
    ElementPostCheck


# New Backend Keywords

SubMenuGroup    [Arguments]    ${menu}
    Wait Until Element Is Visible    xpath=//div[contains(@class,'oe_leftbar')]//ul/li/a[contains(@class, 'oe_menu_toggler')][descendant::span/text()[normalize-space()='${menu}']]    ${SELENIUM_TIMEOUT}
    Click Link				xpath=//div[contains(@class,'oe_leftbar')]//ul/li/a[contains(@class, 'oe_menu_toggler')][descendant::span/text()[normalize-space()='${menu}']]

KanbanButton                      [Arguments]     ${model}    ${button_name}
    Wait Until Page Contains Element    xpath=//div[contains(@class,'openerp')][last()]//*[not(contains(@style,'display:none'))]//button[@data-bt-testing-button='${button_name}']
    Wait Until Element Is Visible    xpath=//div[contains(@class,'openerp')][last()]//*[not(contains(@style,'display:none'))]//button[@data-bt-testing-button='${button_name}']    ${SELENIUM_TIMEOUT}
    Click Button           xpath=//div[contains(@class,'openerp')][last()]//*[not(contains(@style,'display:none'))]//button[@data-bt-testing-button='${button_name}']
    Wait For Condition     return true;    20.0
    ElementPostCheck

Many2ManySelect    [Arguments]    ${model}    ${field}    ${value}
    ElementPreCheck    xpath=//div[contains(@class,'openerp')][last()]//div[@data-bt-testing-name='${field}']
    Click Element    xpath=//div[contains(@class,'openerp')][last()]//div[@data-bt-testing-name='${field}']//div[@class='text-arrow']
    Click Element    xpath=//div[contains(@class,'openerp')][last()]//div[@data-bt-testing-name='${field}']//div[@class='text-list']//span[contains(text(), '${value}')]

ModalButton    [Arguments]    ${model}    ${button_name}
    Execute Javascript    var buttons=$('div.modal-content.openerp button[data-bt-testing-name="${button_name}"]');$(buttons[buttons.length-1]).trigger('click');

TreeViewSelectRecord    [Arguments]   ${model}    ${field}    ${value}
    Click Element    xpath=//div[contains(@class,'openerp')][last()]//table[contains(@class, 'oe_list_content')]//td[@data-bt-testing-model_name='${model}' and @data-field='${field}'][contains(text(), '${value}')]
    ElementPostCheck

TreeViewShouldContain    [Arguments]   ${model}    ${field}    ${value}
    Element Should Be Visible    xpath=//div[contains(@class,'openerp')][last()]//table[contains(@class, 'oe_list_content')]//td[@data-bt-testing-model_name='${model}' and @data-field='${field}'][contains(text(), '${value}')]

ListViewButton    [Arguments]    ${model}    ${action}
    Click Button    xpath=//div[contains(@class,'openerp')][last()]//td[@data-bt-testing-model_name='${model}' and @data-field='${action}']/button

Editable-Select-Option    [Arguments]    ${model}    ${field}    ${value}
    ElementPreCheck        xpath=//div[contains(@class,'openerp')][last()]//div[contains(@class, 'oe_list_editable')]//select[@data-bt-testing-model_name='${model}' and @data-bt-testing-name='${field}']
    Select From List By Label	xpath=//div[contains(@class,'openerp')][last()]//div[contains(@class, 'oe_list_editable')]//select[@data-bt-testing-model_name='${model}' and @data-bt-testing-name='${field}']    ${value}
    ElementPostCheck

Rooming-Char    [Arguments]    ${model}    ${field}    ${value}
    click element  xpath=//td[@data-bt-testing-model_name='${model}' and @data-field='${field}']
    sleep  1
    ElementPreCheck        xpath=//div[contains(@class,'openerp')][last()]//div[contains(@class, 'oe_list_editable')]//input[@data-bt-testing-model_name='${model}' and @data-bt-testing-name='${field}']
    Input Text  xpath=//div[contains(@class,'openerp')][last()]//div[contains(@class, 'oe_list_editable')]//input[@data-bt-testing-model_name='${model}' and @data-bt-testing-name='${field}']    ${value}
    ElementPostCheck

Editable-Char    [Arguments]    ${model}    ${field}    ${value}
    ElementPreCheck        xpath=//div[contains(@class,'openerp')][last()]//div[contains(@class, 'oe_list_editable')]//input[@data-bt-testing-model_name='${model}' and @data-bt-testing-name='${field}']
    Execute Javascript     $("div.openerp:last div.oe_list_editable input[data-bt-testing-model_name='${model}'][data-bt-testing-name='${field}']").val(''); return true;
    Input Text             xpath=//div[contains(@class,'openerp')][last()]//div[contains(@class, 'oe_list_editable')]//input[@data-bt-testing-model_name='${model}' and @data-bt-testing-name='${field}']    ${value}
    ElementPostCheck

Editable-Many2OneCreate    [Arguments]    ${model}    ${field}    ${value}
    ElementPreCheck     xpath=//div[contains(@class,'openerp')][last()]//td[@data-bt-testing-model_name='${model}' and @data-field='${field}']
    Click Element          xpath=//div[contains(@class,'openerp')][last()]//td[@data-bt-testing-model_name='${model}' and @data-field='${field}']
    Input Text          xpath=//div[contains(@class,'openerp')][last()]//input[@data-bt-testing-model_name='${model}' and @data-bt-testing-name='${field}']    ${value}
    Click Link             xpath=//ul[contains(@class,'ui-autocomplete') and not(contains(@style,'display: none'))]/li[1]/a
    ElementPostCheck

TopAction    [Arguments]    ${action}    ${text}
    Click Element    xpath=//div[contains(@class,'oe-view-manager-sidebar')]/div[not(contains(@style,'display: none'))]//button[contains(@class,'dropdown-toggle')][contains(text(), '${action}')]
    Click Link   xpath=//div[contains(@class,'oe-view-manager-sidebar')]/div[not(contains(@style,'display: none'))]//li[contains(@class, 'oe_sidebar_action')]/a[contains(text(), '${text}')]
    ElementPostCheck

Logout
    Click Link    xpath=//div[@id='oe_main_menu_placeholder']/ul[contains(@class, 'oe_user_menu_placeholder')]/li/a
    Click Link    xpath=//div[@id='oe_main_menu_placeholder']/ul[contains(@class, 'oe_user_menu_placeholder')]/li/ul/li/a[contains(@data-menu, 'logout')]
    Wait Until Page Contains Element    name=login

SearchField    [Arguments]    ${field}    ${value}
    Input Text    xpath=//div[contains(@class,'oe-view-manager-search-view')]//div[contains(@class, 'oe_searchview_input')][last()]    ${value}
    Click Element    xpath=//div[contains(@class,'oe-view-manager-search-view')]//div[contains(@class, 'oe-autocomplete')]/ul/li/span/em[contains(text(), '${field}')]

SearchFilter    [Arguments]    ${filter}
    Click Element    xpath=//div[contains(@class,'oe-view-manager-search-view')]//div[contains(@class, 'oe_searchview_unfold_drawer')]
    Click Button    xpath=//div[contains(@class,'oe-search-options')]//div[contains(@class, 'btn-group')][1]/button[@data-toggle='dropdown']
    Click Link    xpath=//div[contains(@class,'oe-search-options')]//ul[contains(@class, 'filters-menu')]/li/a[contains(text(), '${filter}')]
    Click Button    xpath=//div[contains(@class,'oe-search-options')]//div[contains(@class, 'btn-group')][1]/button[@data-toggle='dropdown']
   
ClearFilter
    Click Element    xpath=//div[contains(@class,'oe-view-manager-search-view')]//div[contains(@class, 'oe_searchview_facets')]//span[contains(@class, 'oe_facet_remove')]
    Wait Until Page Does Not Contain Element  xpath=//div[contains(@class,'oe-view-manager-search-view')]//div[contains(@class, 'oe_searchview_facets')]//span[contains(@class, 'oe_facet_remove')]

# New Frontend Keywords

WebsitePage    [Arguments]    ${path}
    Go To    ${ODOO_URL}/${path}

WebsitePortalPage    [Arguments]    ${path}
    Go To    ${ODOO_PORTAL_URL}/${path}

WebsiteModalButton    [Arguments]    ${button_name}
    Wait Until Page Contains Element    xpath=//div[contains(@class, 'modal-content')]//button[contains(@class, '${button_name}')]
    Execute Javascript    var buttons=$('div.modal-content button.${button_name}').trigger('click');
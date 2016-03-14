*** Settings ***
Documentation  Publishing from Contract landing page
Resource       ../../../robot/keywords_8_0.robot

*** Test Cases ***
Valid Login
    Login

Look for partners without company
    MainMenu    Verkauf
    Sleep    3
    SubMenu    Bereinigung starten
    Sleep    3
    Select-Option  cleanup.data    cleanup_rule    Kontakte ohne Unternehmen
    Button    cleanup.data    find_data
    Sleep    3
    TreeViewShouldContain    res.partner    display_name    Achim Kraus

Look for partners without address
    MainMenu    Verkauf
    Sleep    3
    SubMenu    Bereinigung starten
    Sleep    3
    Select-Option  cleanup.data    cleanup_rule    Kontakte ohne Adressen
    Button    cleanup.data    find_data
    Sleep    3
    TreeViewShouldContain    res.partner    display_name    LeaseRad GmbH, Anne Verroen

Look for address without email
    MainMenu    Verkauf
    Sleep    3
    SubMenu    Bereinigung starten
    Sleep    3
    Select-Option  cleanup.data    cleanup_rule    Kontakte ohne E-Mail Adresse
    Button    cleanup.data    find_data
    Sleep    3
    TreeViewShouldContain    res.partner    display_name    LeaseRad GmbH, Leaserad Demo User 10

Look for partners without company inside contract
    MainMenu    Verkauf
    SubMenu    Rahmenverträge
    Sleep    3
    TreeViewSelectRecord    lr.contract    partner_id    Deutsche Bahn
    Sleep    3
    TopAction    Mehr    Bereinigung starten
    Select-Option  cleanup.data    cleanup_rule    Kontakte ohne Unternehmen
    Button    cleanup.data    find_data
    Sleep    3
    Page Should Contain Element    xpath=//span[contains(text(), 'Keine Einträge gefunden.')]
    Click Button    xpath=//footer//button[contains(@class, 'oe_link')]

Look for partners with duplicate email
    MainMenu    Verkauf
    SubMenu    Rahmenverträge
    Sleep    3
    TreeViewSelectRecord    lr.contract    partner_id    Deutsche Bahn
    Sleep    3
    TopAction    Mehr    Bereinigung starten
    Select-Option  cleanup.data    cleanup_rule    Kontakte mit duplizierten E-Mail Adressen
    Button    cleanup.data    find_data
    Sleep    3
    Page Should Contain Element    xpath=//span[contains(text(), 'Keine Einträge gefunden.')]
    Click Button    xpath=//footer//button[contains(@class, 'oe_link')]

Look for partners with invalid email
    MainMenu    Verkauf
    SubMenu    Rahmenverträge
    Sleep    3
    TreeViewSelectRecord    lr.contract    partner_id    Deutsche Bahn
    Sleep    3
    TopAction    Mehr    Bereinigung starten
    Select-Option  cleanup.data    cleanup_rule    Kontakte mit ungültigen E-Mail Adressen
    Button    cleanup.data    find_data
    Sleep    3
    Page Should Contain Element    xpath=//span[contains(text(), 'Keine Einträge gefunden.')]
    Click Button    xpath=//footer//button[contains(@class, 'oe_link')]

Look for address without private address
    MainMenu    Verkauf
    Sleep    3
    SubMenu    Bereinigung starten
    Select-Option  cleanup.data    cleanup_rule    Kontakte ohne private Adresse
    Button    cleanup.data    find_data
    Sleep    3
    TreeViewShouldContain    res.partner    display_name    001 Testkunde AG, Beate Business

Look for address without business address
    MainMenu    Verkauf
    Sleep    3
    SubMenu    Bereinigung starten
    Select-Option  cleanup.data    cleanup_rule    Kontakte ohne geschäftliche Adresse
    Button    cleanup.data    find_data
    Sleep    3
    TreeViewShouldContain    res.partner    display_name    001 Testkunde AG, Dagobert Duck

Close Browser
    Close Browser
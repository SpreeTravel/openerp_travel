=====================
Robot Framework Suite
=====================

------------
Installation
------------

For the installation of the the Robot Framework you should follow the following steps:

1. Install python modules:

.. code-block:: bash

    pip install robotframework
    pip install robotframework-selenium2library

2. Install the module web_selenium, which should be already added inside addons_extern. Otherwise it can be downloaded
from https://github.com/brain-tec/web_selenium. Our version has some fixes over the original version from Github.

-----
Usage
-----

The tests can be executed using the pybot command with the configuration from file.
Inside ${LROERP_PROJECT}/robot you can run a test as shown below.

.. code-block:: bash

    pybot -v CONFIG:config_local.py tests/1_new_contract.robot

To run tests in headless mode there is also a configuration file:

.. code-block:: bash

    pybot -v CONFIG:config_local_headless.py tests/1_new_contract.robot

To run All tests you use the preferred configuration file and run the main tests folder, this will run all test scenarios:

.. code-block:: bash

    pybot -v CONFIG:config_local_headless.py tests

To see the results of the tests in HTML, the Robot Framework generates a file log.html.
In this page the tests can be checked in details step by step.

.. image:: img/robot_log.png

-----
Tests
-----

Robot Framework test data is defined in tabular format. The plain texts formats is very easy to edit using any text editor
and they also work very well in version control.

Test data is structured in four types. These test data types are identified by names with asterisks. Recognized type
names are *Settings*, *Variables*, *Test Cases*, and *Keywords*.

.. code-block:: robotframework

    *** Settings ***
    Library     OperatingSystem

    *** Variables ***
    ${MESSAGE}      Hello, world!

    *** Test Cases ***
    Test One
        [Documentation]     Test One
        Log         ${MESSAGE}
        MyKeyword       /tmp

    Test Two
        Should Be Equal     ${MESSAGE}      Hello, world!

    *** Keywords ***
    MyKeyword       [Arguments]     ${path}
        Directory Should Exist      ${path}

Test cases are constructed from the available keywords. First it needed the test case name and later one row per action.
Each row should have a keyword name or a variable and after that all possible arguments for the specified keyword.

.. code-block:: robotframework

    *** Test Cases ***
    Valid Login
        Open Login Page
        Input Username      admin
        Input Password      admin
        Submit Credentials
        Welcome Page Should be Open

    Setting Variables
        ${value}=       Get Some Value
        Should Be Equal     ${value}    expected value

More information about how to write test can be found in http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html

In the folder ${LROERP_PROJECT}/robot/tests there are some tests, that also can be check as samples.

--------
Keywords
--------

The project Odoo-Robot-Framework (https://github.com/brain-tec/odoo-robot-framework) has created some keywords to use
in the backend of Odoo. Here there is a list of them and also other keywords we added creating test for LeaseRad project.

+---------------------------+---------------------------------------------------------------------------------------------------------------------+
| Keyword                   |  Arguments                                                                                                          |
+===========================+=====================================================================================================================+
| Login                     | ${url}=${ODOO_URL}    ${user}=${ODOO_USER}    ${password}=${ODOO_PASSWORD}    ${db}=${ODOO_DB}   ${bamboo}=${BAMBOO}|
+---------------------------+---------------------------------------------------------------------------------------------------------------------+
| LoginNoNewBrowser         | ${url}=${ODOO_URL}    ${user}=${ODOO_USER}    ${password}=${ODOO_PASSWORD}    ${db}=${ODOO_DB}   ${bamboo}=${BAMBOO}|
+---------------------------+---------------------------------------------------------------------------------------------------------------------+
| MainMenu                  | ${menu}                                                                                                             |
+---------------------------+---------------------------------------------------------------------------------------------------------------------+
| SubMenu                   | ${menu}                                                                                                             |
+---------------------------+---------------------------------------------------------------------------------------------------------------------+
| ChangeView                | ${view}                                                                                                             |
+---------------------------+---------------------------------------------------------------------------------------------------------------------+
| ElementPreCheck           | ${element}                                                                                                          |
+---------------------------+---------------------------------------------------------------------------------------------------------------------+
| ElementPostCheck          |                                                                                                                     |
+---------------------------+---------------------------------------------------------------------------------------------------------------------+
| WriteInField              | ${model}    ${fieldname}    ${value}                                                                                |
+---------------------------+---------------------------------------------------------------------------------------------------------------------+
| Button                    | ${model}    ${button_name}                                                                                          |
+---------------------------+---------------------------------------------------------------------------------------------------------------------+
| Many2OneSelect            | ${model}    ${field}    ${value}                                                                                    |
+---------------------------+---------------------------------------------------------------------------------------------------------------------+
| Date                      | ${model}    ${field}    ${value}                                                                                    |
+---------------------------+---------------------------------------------------------------------------------------------------------------------+
| Char                      | ${model}    ${field}    ${value}                                                                                    |
+---------------------------+---------------------------------------------------------------------------------------------------------------------+
| Float                     | ${model}    ${field}    ${value}                                                                                    |
+---------------------------+---------------------------------------------------------------------------------------------------------------------+
| Text                      | ${model}    ${field}    ${value}                                                                                    |
+---------------------------+---------------------------------------------------------------------------------------------------------------------+
| Select-Option             | ${model}    ${field}    ${value}                                                                                    |
+---------------------------+---------------------------------------------------------------------------------------------------------------------+
| Checkbox                  | ${model}    ${field}                                                                                                |
+---------------------------+---------------------------------------------------------------------------------------------------------------------+
| NotebookPage              | ${value}                                                                                                            |
+---------------------------+---------------------------------------------------------------------------------------------------------------------+
| NewOne2Many               | ${model}    ${field}                                                                                                |
+---------------------------+---------------------------------------------------------------------------------------------------------------------+
| One2ManySelectRecord      | ${model}    ${field}    ${submodel}    @{fields}                                                                    |
+---------------------------+---------------------------------------------------------------------------------------------------------------------+
| SelectListView            | ${model}    ${field}                                                                                                |
+---------------------------+---------------------------------------------------------------------------------------------------------------------+
| SidebarAction             | ${type}    ${id}                                                                                                    |
+---------------------------+---------------------------------------------------------------------------------------------------------------------+
| MainWindowButton          | ${model}    ${button_text}                                                                                          |
+---------------------------+---------------------------------------------------------------------------------------------------------------------+
| MainWindowNormalField     | ${field}    ${value}                                                                                                |
+---------------------------+---------------------------------------------------------------------------------------------------------------------+
| MainWindowSearchTextField | ${model}    ${field}                                                                                                |
+---------------------------+---------------------------------------------------------------------------------------------------------------------+
| MainWindowMany2One        | ${model}    ${field}                                                                                                |
+---------------------------+---------------------------------------------------------------------------------------------------------------------+
| SubMenuGroup              | ${menu}                                                                                                             |
+---------------------------+---------------------------------------------------------------------------------------------------------------------+
| KanbanButton              | ${model}    ${button_name}                                                                                          |
+---------------------------+---------------------------------------------------------------------------------------------------------------------+
| Many2ManySelect           | ${model}    ${model}    ${field}    ${value}                                                                        |
+---------------------------+---------------------------------------------------------------------------------------------------------------------+
| ModalButton               | ${model}    ${button_name}                                                                                         |
+---------------------------+---------------------------------------------------------------------------------------------------------------------+
| TreeViewSelectRecord      | ${model}    ${field}    ${value}                                                                                    |
+---------------------------+---------------------------------------------------------------------------------------------------------------------+
| ListViewButton            | ${model}    ${action}                                                                                               |
+---------------------------+---------------------------------------------------------------------------------------------------------------------+
| Editable-Select-Option    | ${model}    ${field}    ${value}                                                                                    |
+---------------------------+---------------------------------------------------------------------------------------------------------------------+
| Editable-Char             | ${model}    ${field}    ${value}                                                                                    |
+---------------------------+---------------------------------------------------------------------------------------------------------------------+
| TopAction                 | ${action}    ${text}                                                                                                |
+---------------------------+---------------------------------------------------------------------------------------------------------------------+
| Logout                    |                                                                                                                     |
+---------------------------+---------------------------------------------------------------------------------------------------------------------+
| ClearFilter               |                                                                                                                     |
+---------------------------+---------------------------------------------------------------------------------------------------------------------+
| WebsitePortalPage         | ${path}                                                                                                             |
+---------------------------+---------------------------------------------------------------------------------------------------------------------+
| WebsiteModalButton        | ${button_name}                                                                                                        |
+---------------------------+---------------------------------------------------------------------------------------------------------------------+

More information about the implemented keywords in Robot-Framework can be found in http://robotframework.org/Selenium2Library/doc/Selenium2Library.html

---------------
LeaseRad Sample
---------------

Below is shown a test created for LeaseRad project:

.. code-block:: robotframework

    *** Test Cases ***
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
        Select-Option    lr.contract    insurance    AN trägt Versicherungsrate
        Select-Option    lr.contract    grant_type    Kein Zuschuss
        Many2ManySelect    lr.contract    allowed_categories    Alle Produkte / JobRad / Fahrrad
        Button    lr.contract    oe_form_button_save

----------------
LeaseRad Modules
----------------

The new tests to cover the features of the project should be created in a folder robot inside each module.
Currently exists a robot folder in the root of the project with the configuration files and some main tests
to cover general features.

Module structure
----------------

.. code-block:: python

    |_ lr_contract
        |_ data
        |_ i18n
        |_ models
        |_ security
        |_ static
        |_ tests
        |_ robot
            |_ 1_new_contract.robot
            |_ 2_edit_contract.robot
        |_ views
        |_ __init__.py
        |_ __openerp__.py


Robot file configuration
------------------------

.. code-block:: robotframework

    *** Settings ***
    Documentation       Create Contract
    Resource        ../../../robot/keywords_8_0.robot

    *** Test Cases ***
    ...
import pyautogui
import time
import aclib

def get_navigator_item_guids_from_tree(current_branch, navigator_item_guids, navigator_item_type):
    for navigator_item in current_branch:
        navigator_item = navigator_item['navigatorItem']
        if navigator_item['type'] == navigator_item_type:
            navigator_item_guids.append(navigator_item['navigatorItemId'])
        children = navigator_item.get('children')
        if children:
            get_navigator_item_guids_from_tree(children, navigator_item_guids, navigator_item_type)

def get_root_subsets(navigator_tree):
    return navigator_tree['navigatorTree']['rootItem']['children'][0]['navigatorItem'].get('children')

def get_layout(subsets,suffix = '-dwg'):
    layout_guids = []
    for navigator_item in subsets:
        if navigator_item['navigatorItem']['type']=='SubsetItem' and suffix in navigator_item['navigatorItem']['name']:
            get_navigator_item_guids_from_tree([navigator_item],layout_guids, navigator_item_type='LayoutItem')
    return [{'navigatorItemId': guid} for guid in layout_guids]

def explode_selected():
    active_window = pyautogui.getActiveWindow()
    if active_window:
        active_window.activate()
        time.sleep(1)
        pyautogui.hotkey('ctrl', '=')
        time.sleep(1)
        pyautogui.hotkey('enter')
        print(f"Сочетание отправлено в окно: {active_window.title}")
    else:
        print("Активное окно не найдено")

def explode_drawingsonlayout(databaseId):
    windows = aclib.RunTapirCommand(command='ChangeWindow',
                                    parameters={'windowType': 'Layout',
                                                'databaseId': databaseId})['success']
    time.sleep(1)
    if windows:
        drawings = aclib.RunTapirCommand(command='GetElementsByType',
                                        parameters={'elementType': 'Drawing',
                                                    'databases': databaseId} )['elements']
        for drawing in drawings:
            select = aclib.RunTapirCommand ('ChangeSelectionOfElements', {'addElementsToSelection': [drawing]})['executionResultsOfAddToSelection'][0]['success']
            if select:
                explode_selected()
            aclib.RunTapirCommand ('ChangeSelectionOfElements', {'addElementsToSelection': []})


navigator_tree_id = {'navigatorTreeId': {'type': 'LayoutBook'}}
navigator_tree = aclib.RunCommand(command='API.GetNavigatorItemTree',
                                  parameters=navigator_tree_id)
subsets = get_root_subsets(navigator_tree)
layout_elements = get_layout(subsets, '-dwg')
databases = aclib.RunTapirCommand(command='GetDatabaseIdFromNavigatorItemId',
                                  parameters={'navigatorItemIds': layout_elements}, debug=True)

for db in databases['databases']:
    explode_drawingsonlayout(db['databaseId'])









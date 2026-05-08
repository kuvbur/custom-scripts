import pyautogui
import time
import aclib


def activate_window_by_title(title):
    windows = pyautogui.getWindowsWithTitle(title)
    if not windows:
        return False
    for win in windows:
        try:
            win.activate()
            return True
        except PyGetWindowException as e:
            if "Error code from Windows: 0" in str(e):
                return True
            else:
                continue
    return False

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
    activate_window_by_title("archicad")
    active_window = pyautogui.getActiveWindow()
    if active_window:
        pyautogui.hotkey('ctrl', '=')
        time.sleep(2)
        pyautogui.hotkey('enter')
        time.sleep(3)
        pyautogui.hotkey('esc')
        time.sleep(1)
    else:
        print("Активное окно не найдено")

def explode_drawingsonlayout(databaseId):
    windows = aclib.RunTapirCommand(command='ChangeWindow',
                                    parameters={'windowType': 'Layout',
                                                'databaseId': databaseId})
    time.sleep(1)
    if windows['success']:
        drawings = aclib.RunTapirCommand(command='GetElementsByType',
                                        parameters={'elementType': 'Drawing',
                                                    'databases': databaseId} )['elements']
        for drawing in drawings:
            select = aclib.RunTapirCommand ('ChangeSelectionOfElements', {'addElementsToSelection': [drawing]})['executionResultsOfAddToSelection'][0]['success']
            if select:
                explode_selected()
                time.sleep(5)

navigator_tree_id = {'navigatorTreeId': {'type': 'LayoutBook'}}
navigator_tree = aclib.RunCommand(command='API.GetNavigatorItemTree',
                                  parameters=navigator_tree_id)
subsets = get_root_subsets(navigator_tree)
layout_elements = get_layout(subsets, '-dwg')
databases = aclib.RunTapirCommand(command='GetDatabaseIdFromNavigatorItemId',
                                  parameters={'navigatorItemIds': layout_elements}, debug=True)


for db in databases['databases']:
    explode_drawingsonlayout(db['databaseId'])









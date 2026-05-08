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


navigator_tree_id = {'navigatorTreeId': {'type': 'LayoutBook'}}

navigator_tree = aclib.RunCommand(command='API.GetNavigatorItemTree',
                                  parameters=navigator_tree_id)

layout_guids = []
subsets = navigator_tree['navigatorTree']['rootItem']['children'][0]['navigatorItem'].get('children')

for navigator_item in subsets:
    if navigator_item['navigatorItem']['type']=='SubsetItem' and '-dwg' in navigator_item['navigatorItem']['name']:
        get_navigator_item_guids_from_tree([navigator_item],layout_guids, navigator_item_type='LayoutItem')

layout_elements = [{'navigatorItemId': guid} for guid in layout_guids]
databases = aclib.RunTapirCommand(command='GetDatabaseIdFromNavigatorItemId',
                                  parameters={'navigatorItemIds': layout_elements}, debug=True)

for db in databases['databases']:
    databaseId = db['databaseId']
    windows = aclib.RunTapirCommand(command='ChangeWindow',
                                    parameters={'windowType': 'Layout',
                                                'databaseId': databaseId})['success']
    sleep(1)
    if windows:
        active_window = pyautogui.getActiveWindow()
        if active_window:
            # Активируем окно (если нужно)
            active_window.activate()

            drawings = aclib.RunTapirCommand(command='GetElementsByType',
                                            parameters={'elementType': 'Drawing',
                                                        'databases': databaseId} )['elements']

            select = aclib.RunTapirCommand ('ChangeSelectionOfElements', {'addElementsToSelection': drawings})['success']
            if select:
                time.sleep(2)
                pyautogui.hotkey('ctrl', '=')
            
                print(f"Сочетание отправлено в окно: {active_window.title}")
        else:
            print("Активное окно не найдено")








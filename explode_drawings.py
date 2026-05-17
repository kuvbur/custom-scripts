
import time
import aclib
import tkinter as tk
from tkinter import ttk
import pyautogui
from pygetwindow import PyGetWindowException

flags = [
    'IsEditable',
    'IsVisibleByLayer',
    'InMyWorkspace',
    'HasAccessRight'
]

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
    subsets = []
    for navigator_item in navigator_tree['navigatorTree']['rootItem']['children'][0]['navigatorItem'].get('children'):
        if navigator_item['navigatorItem']['type']=='SubsetItem':
            subsets.append(navigator_item)
    return subsets

def get_layout(subsets):
    layout_guids = []
    for navigator_item in subsets:
        if navigator_item['navigatorItem']['type']=='SubsetItem':
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
                                        parameters={'elementType': 'Drawing','filters': flags,
                                                    'databases': databaseId} )['elements']
        for drawing in drawings:
            select = aclib.RunTapirCommand ('ChangeSelectionOfElements', {'addElementsToSelection': [drawing]})['executionResultsOfAddToSelection'][0]['success']
            if select:
                explode_selected()
                time.sleep(5)


def update_scrollregion(event):
    canvas.configure(scrollregion=canvas.bbox("all"))
    
def on_mousewheel(event):
    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


navigator_tree_id = {'navigatorTreeId': {'type': 'LayoutBook'}}
navigator_tree = aclib.RunCommand(command='API.GetNavigatorItemTree',
                                  parameters=navigator_tree_id)
subsets = get_root_subsets(navigator_tree)
selected_subsets = []
def on_submit():
    global selected_subsets
    selected_subsets = [subsets[i] for i, var in enumerate(check_vars) if var.get()]
    try:
        root.quit()
    except tk.TclError:
        pass

def on_cancel():
    global selected_subsets
    selected_subsets = []
    try:
        root.quit()
    except tk.TclError:
        pass

ITEM_HEIGHT = 25
MIN_HEIGHT = 250
MAX_HEIGHT = 600
num_items = len(subsets)
height = min(MAX_HEIGHT, num_items * ITEM_HEIGHT + 150)
width = 450

root = tk.Tk()
root.title("Выберите поднаборы для декомпозиции")
root.geometry(f"{width}x{height}")
root.minsize(350, MIN_HEIGHT)
root.protocol("WM_DELETE_WINDOW", on_cancel)
main_container = ttk.Frame(root)
main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
canvas = tk.Canvas(main_container)
scrollbar = ttk.Scrollbar(main_container, orient=tk.VERTICAL, command=canvas.yview)
scrollable_frame = ttk.Frame(canvas)
canvas.configure(yscrollcommand=scrollbar.set)
canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
scrollable_frame.bind('<Configure>', update_scrollregion)
check_vars = []
for name in subsets:
    var = tk.BooleanVar()
    check_vars.append(var)
    cb = ttk.Checkbutton(scrollable_frame, text=name['navigatorItem']['name'], variable=var)
    cb.pack(anchor=tk.W, pady=3, padx=5)
button_frame = ttk.Frame(root)
button_frame.pack(fill=tk.X, padx=10, pady=5)
ttk.Button(button_frame, text="OK", command=on_submit).pack(side=tk.LEFT, padx=(0,5))
ttk.Button(button_frame, text="Отмена", command=on_cancel).pack(side=tk.LEFT)
result_label = ttk.Label(button_frame, text="")
result_label.pack(side=tk.RIGHT)
canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
root.bind_all("<MouseWheel>", on_mousewheel)
try:
    root.mainloop()
except tk.TclError:
    pass

layout_elements = get_layout(selected_subsets)

databases = aclib.RunTapirCommand(command='GetDatabaseIdFromNavigatorItemId',
                                  parameters={'navigatorItemIds': layout_elements}, debug=True)


for db in databases['databases']:
    explode_drawingsonlayout(db['databaseId'])









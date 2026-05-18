import sys
import time
import aclib
import tkinter as tk
from tkinter import messagebox, ttk
import pyautogui
from pygetwindow import PyGetWindowException

FLAGS = [
    'IsEditable',
    'InMyWorkspace',
    'HasAccessRight'
]


class NavigatorHelper:
    @staticmethod
    def get_navigator_item_guids_from_tree(current_branch, navigator_item_guids, navigator_item_type):
        for navigator_item in current_branch:
            navigator_item = navigator_item['navigatorItem']
            if navigator_item['type'] == navigator_item_type:
                navigator_item_guids.append(navigator_item['navigatorItemId'])
            children = navigator_item.get('children')
            if children:
                NavigatorHelper.get_navigator_item_guids_from_tree(children,
                                                                  navigator_item_guids,
                                                                  navigator_item_type)

    @staticmethod
    def get_root_subsets(navigator_tree):
        subsets = []
        root_children = navigator_tree['navigatorTree']['rootItem']['children'][0]['navigatorItem'].get('children', [])
        for navigator_item in root_children:
            if navigator_item['navigatorItem']['type'] == 'SubsetItem':
                subsets.append(navigator_item)
        return subsets

    @staticmethod
    def get_layout(subsets):
        layout_guids = []
        for navigator_item in subsets:
            if navigator_item['navigatorItem']['type'] == 'SubsetItem':
                NavigatorHelper.get_navigator_item_guids_from_tree([navigator_item],
                                                                  layout_guids,
                                                                  navigator_item_type='LayoutItem')
        return [{'navigatorItemId': guid} for guid in layout_guids]


class ArchicadController:
    @staticmethod
    def activate_window_by_title(title):
        windows = pyautogui.getWindowsWithTitle(title)
        if not windows:
            return False
        for win in windows:
            try:
                win.activate()
                return True
            except PyGetWindowException as e:
                if 'Error code from Windows: 0' in str(e):
                    return True
                continue
        return False

    @staticmethod
    def wait_for_window(title, timeout=10, interval=0.25):
        deadline = time.time() + timeout
        while time.time() < deadline:
            windows = pyautogui.getWindowsWithTitle(title)
            if windows:
                return windows[0]
            time.sleep(interval)
        return None

    @staticmethod
    def wait_for_window_close(title, timeout=10, interval=0.25):
        deadline = time.time() + timeout
        while time.time() < deadline:
            if not pyautogui.getWindowsWithTitle(title):
                return True
            time.sleep(interval)
        return False

    @staticmethod
    def show_error(message):
        try:
            messagebox.showerror('Ошибка', message)
        except tk.TclError:
            print(message)

    @staticmethod
    def explode_selected():
        if not ArchicadController.activate_window_by_title('archicad'):
            ArchicadController.show_error('Активное окно Архикад не найдено.')
            return False

        time.sleep(1)
        pyautogui.hotkey('ctrl', '=')
        time.sleep(1)

        dialog_window = ArchicadController.wait_for_window('Декомпозиция', timeout=12)
        if not dialog_window:
            ArchicadController.show_error('Диалог "Декомпозиция" не появился.')
            return False

        try:
            dialog_window.activate()
        except PyGetWindowException:
            pass

        time.sleep(1)
        pyautogui.press('enter')
        time.sleep(1)

        ArchicadController.wait_for_window_close('Декомпозиция', timeout=12)
        time.sleep(1)

        ArchicadController.activate_window_by_title('archicad')
        time.sleep(1)
        pyautogui.press('esc')
        time.sleep(1)
        return True


    @staticmethod
    def change_window_to_layout(database_id):
        return aclib.RunTapirCommand(command='ChangeWindow',
                                     parameters={'windowType': 'Layout',
                                                 'databaseId': database_id})

    @staticmethod
    def get_drawings_for_database(database_id):
        response = aclib.RunTapirCommand(command='GetElementsByType',
                                         parameters={'elementType': 'Drawing',
                                                     'filters': FLAGS,
                                                     'databases': database_id})
        return response.get('elements', [])

    @staticmethod
    def get_database_ids(layout_elements):
        return aclib.RunTapirCommand(command='GetDatabaseIdFromNavigatorItemId',
                                    parameters={'navigatorItemIds': layout_elements},
                                    debug=False)

    @staticmethod
    def select_drawing(drawing):
        result = aclib.RunTapirCommand('ChangeSelectionOfElements',
                                       {'addElementsToSelection': [drawing]})
        execution = result.get('executionResultsOfAddToSelection', [])
        return bool(execution and execution[0].get('success'))

    def explode_drawings_on_layout(self, database_id, drawings):
        response = self.change_window_to_layout(database_id)
        time.sleep(1)
        if not response.get('success'):
            return

        for drawing in drawings:
            if self.select_drawing(drawing):
                self.explode_selected()
                time.sleep(5)


class SelectionDialog:
    def __init__(self, subsets):
        self.subsets = subsets
        self.selected_subsets = []
        self.root = None
        self.check_vars = []
        self.canvas = None
        self.window_id = None

    def show(self):
        self._build_ui()
        try:
            self.root.mainloop()
        except tk.TclError:
            pass
        try:
            self.root.destroy()
        except tk.TclError:
            pass
        return self.selected_subsets

    def _build_ui(self):
        item_height = 25
        min_height = 250
        max_height = 600
        height = min(max_height, len(self.subsets) * item_height + 150)
        width = 450

        self.root = tk.Tk()
        self.root.title('Выберите поднаборы для декомпозиции')
        self.root.geometry(f'{width}x{height}')
        self.root.minsize(350, min_height)
        self.root.protocol('WM_DELETE_WINDOW', self._on_cancel)

        root_frame = ttk.Frame(self.root)
        root_frame.pack(fill=tk.BOTH, expand=True)

        button_frame = ttk.Frame(root_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(button_frame, text='OK', command=self._on_submit).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text='Отмена', command=self._on_cancel).pack(side=tk.LEFT)

        list_frame = ttk.Frame(root_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(list_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollable_frame = ttk.Frame(self.canvas)
        self.window_id = self.canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')

        scrollable_frame.bind('<Configure>', self._on_frame_configure)
        self.canvas.bind('<Configure>', self._on_canvas_configure)

        for item in self.subsets:
            var = tk.BooleanVar()
            self.check_vars.append(var)
            cb = ttk.Checkbutton(scrollable_frame, text=item['navigatorItem']['name'], variable=var)
            cb.pack(anchor=tk.W, pady=3, padx=5)

        self.root.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))
        self.root.bind_all('<MouseWheel>', self._on_mousewheel)

    def _on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.window_id, width=event.width)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')

    def _on_submit(self):
        self.selected_subsets = [self.subsets[i] for i, var in enumerate(self.check_vars) if var.get()]
        try:
            self.root.quit()
        except tk.TclError:
            pass

    def _on_cancel(self):
        self.selected_subsets = []
        try:
            self.root.quit()
        except tk.TclError:
            pass


def main():
    navigator_tree_id = {'navigatorTreeId': {'type': 'LayoutBook'}}
    navigator_tree = aclib.RunCommand(command='API.GetNavigatorItemTree',
                                      parameters=navigator_tree_id)

    subsets = NavigatorHelper.get_root_subsets(navigator_tree)
    selected_subsets = SelectionDialog(subsets).show()
    if not selected_subsets:
        return

    layout_elements = NavigatorHelper.get_layout(selected_subsets)
    databases = ArchicadController.get_database_ids(layout_elements)

    plan = []
    total_drawings = 0
    for db in databases.get('databases', []):
        drawings = ArchicadController.get_drawings_for_database(db['databaseId'])
        if drawings:
            plan.append({'databaseId': db['databaseId'], 'drawings': drawings})
            total_drawings += len(drawings)

    if total_drawings == 0:
        ArchicadController.show_error('Нет чертежей для обработки.')
        return

    controller = ArchicadController()
    for item in plan:
        controller.explode_drawings_on_layout(item['databaseId'], item['drawings'])


if __name__ == '__main__':
    main()









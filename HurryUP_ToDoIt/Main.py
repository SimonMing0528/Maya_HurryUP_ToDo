# =========================================================
# HurryUP_ToDo-It
# =========================================================
#
# Maya Artist Task Workspace Tool
#
# Version:
#     v1.0.0
#
# Author:
#     Simon Lee
#
# Created:
#     2026.05.08
#
# Description:
#     A lightweight task management tool for Maya artists,
#     designed for production workflow usage.
#
# Core Features:
#     - WIP / TODO task management
#     - Drag & Drop task workflow
#     - Task detail editor
#     - Focus task system (⭐ Priority)
#     - Workspace-based JSON save system
#     - Multi-department task list support
#     - Scene folder sidecar JSON storage
#     - Auto workspace discovery
#     - Workspace identifier display
#
# Workspace Example:
#     shot010_MOD.todo.json
#     shot010_LGT.todo.json
#     shot010_FX.todo.json
#
# Notes:
#     Please save Maya scene before creating
#     or loading workspace files.
#
# Future Plans:
#     - Deadline reminder
#     - Auto backup system
#     - Publish note integration
#     - Pipeline hook support
#
# =====================================================================================

import maya.cmds as cmds
import os
import json

from PySide2 import QtWidgets
from PySide2 import QtCore
from PySide2 import QtGui
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

# =========================
# Detail Edit Dialog
# =========================
class DetailEditDialog(QtWidgets.QDialog):

    def __init__(
        self,
        title,
        detail,
        parent=None
    ):

        super(
            DetailEditDialog,
            self
        ).__init__(parent)

        self.setWindowTitle(
            "Edit Task Detail"
        )

        self.setMinimumWidth(400)

        layout = QtWidgets.QVBoxLayout(
            self
        )

        layout.addWidget(
            QtWidgets.QLabel(
                "Task Name:"
            )
        )

        self.title_edit = QtWidgets.QLineEdit(
            title
        )

        layout.addWidget(
            self.title_edit
        )

        layout.addWidget(
            QtWidgets.QLabel(
                "Detail:"
            )
        )

        self.detail_edit = QtWidgets.QTextEdit(
            detail
        )

        layout.addWidget(
            self.detail_edit
        )

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok |
            QtWidgets.QDialogButtonBox.Cancel
        )

        buttons.accepted.connect(
            self.accept
        )

        buttons.rejected.connect(
            self.reject
        )

        layout.addWidget(
            buttons
        )

    def get_data(self):

        return (
            self.title_edit.text(),
            self.detail_edit.toPlainText()
        )


# =========================
# Custom List Widget
# =========================
class ToDoListWidget(QtWidgets.QListWidget):

    def __init__(
        self,
        name,
        parent_ui
    ):

        super(
            ToDoListWidget,
            self
        ).__init__()

        self.parent_ui = parent_ui

        self.setObjectName(name)

        self.setDragEnabled(True)

        self.setAcceptDrops(True)

        self.setDropIndicatorShown(True)

        self.setDragDropMode(
            QtWidgets.QAbstractItemView.DragDrop
        )

        self.setDefaultDropAction(
            QtCore.Qt.MoveAction
        )

        self.itemChanged.connect(
            self.on_item_changed
        )

        self.setContextMenuPolicy(
            QtCore.Qt.CustomContextMenu
        )

        self.customContextMenuRequested.connect(
            self.show_context_menu
        )

    # =========================
    # Item Changed
    # =========================
    def on_item_changed(self, item):

        if not self.parent_ui._block_save:

            self.parent_ui.update_item_look(
                item
            )

            self.parent_ui.save_data()

    # =========================
    # Drop Event
    # =========================
    def dropEvent(self, event):

        super(
            ToDoListWidget,
            self
        ).dropEvent(event)

        self.parent_ui.refresh_all_styles()

        self.parent_ui.save_data()

    # =========================
    # Double Click
    # =========================
    def mouseDoubleClickEvent(self, event):

        item = self.itemAt(
            event.pos()
        )

        if item:

            self.parent_ui.edit_item_detail(
                item
            )

        super(
            ToDoListWidget,
            self
        ).mouseDoubleClickEvent(event)

    # =========================
    # Context Menu
    # =========================
    def show_context_menu(self, pos):

        item = self.itemAt(pos)

        if not item:
            return

        menu = QtWidgets.QMenu(self)

        act_duplicate = menu.addAction(
            "Duplicate"
        )

        act_delete = menu.addAction(
            "Delete"
        )

        menu.addSeparator()

        if self.objectName() == "TODO":

            act_move = menu.addAction(
                "Move To WIP"
            )

        else:

            act_move = menu.addAction(
                "Move To TODO"
            )

            menu.addSeparator()

            act_focus = menu.addAction(
                "⭐ Set Focus"
            )

        action = menu.exec_(
            self.mapToGlobal(pos)
        )

        if action == act_duplicate:

            self.parent_ui.duplicate_item(
                item
            )

        elif action == act_delete:

            self.parent_ui.delete_item(
                item
            )

        elif action == act_move:

            self.parent_ui.move_item_between_lists(
                item
            )

        elif (
            self.objectName() == "WIP" and
            action == act_focus
        ):

            self.parent_ui.set_focus_item(
                item
            )


# =========================
# Main Window
# =========================
class ToDoItWindow(
    MayaQWidgetDockableMixin,
    QtWidgets.QWidget
):

    STORAGE_KEY = "ToDoIt_V4"

    CURRENT_WORKSPACE = None

    FOCUS_ROLE = QtCore.Qt.UserRole + 1

    TEXT_ROLE = QtCore.Qt.UserRole + 2

    # =========================
    # Init
    # =========================
    def __init__(self, parent=None):

        super(
            ToDoItWindow,
            self
        ).__init__(parent=parent)

        self.setWindowTitle(
            "HurryUP_ToDo-It"
        )

        self.setObjectName(
            "HurryUP_ToDoItWindow"
        )

        self._block_save = False

        self.btn_refresh = None
        self.btn_open_folder = None

        self.init_style()

        self.init_ui()

        self.load_data()

    # =========================
    # Style
    # =========================
    def init_style(self):

        self.setStyleSheet("""

            QToolTip {
                background-color: #ffffcc;
                color: #333;
                border: 1px solid #d4d4aa;
                padding: 5px;
            }
            
            QPushButton:hover {
                background-color: #5a5a5a;
            }
            
            QLabel#WorkspaceLabel {
                color: #FFD700;
                font-weight: bold;
                font-size: 14px;
                padding: 6px;
            }

            QLabel#WIPHeader {
                font-weight: bold;
                color: #00FFFF;
                background-color: transparent;
                padding: 6px;
                border-radius: 3px;
            }

            QLabel#TODOHeader {
                font-weight: bold;
                color: #FFD700;
                background-color: transparent;
                padding: 6px;
                border-radius: 3px;
            }

            QListWidget#WIP {
                border: 1px solid #222;
                background-color: #2D353F;
                outline: none;
                font-size: 13px;
            }

            QListWidget#TODO {
                border: 1px solid #222;
                background-color: #2B2B2B;
                outline: none;
                font-size: 13px;
            }

            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #333;
            }

            QListWidget#WIP::item:selected {
                background-color: #4C7A7A;
                color: white;
            }

            QListWidget#TODO::item:selected {
                background-color: #505050;
                color: white;
            }

            QListWidget::item:hover {
                background-color: #404850;
            }

            QPushButton {
                padding: 4px;
            }

            QPushButton:hover {
                background-color: #5a5a5a;
            }

        """)

    # =========================
    # UI
    # =========================
    def init_ui(self):

        main_layout = QtWidgets.QVBoxLayout(self)

        main_layout.setContentsMargins(
            4,
            4,
            4,
            4
        )


        # Top Toolbar
        toolbar_layout = QtWidgets.QHBoxLayout()
        toolbar_layout.setAlignment(QtCore.Qt.AlignRight)
        toolbar_layout.setSpacing(4)

        self.btn_refresh = QtWidgets.QPushButton("R")
        self.btn_refresh.setFixedSize(24, 24)
        self.btn_refresh.setToolTip("Refresh")
        self.btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #3a3a3a;
                color: #ccc;
                border: 1px solid #555;
                border-radius: 3px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #505050;
                color: #fff;
                border: 1px solid #777;
            }
            QPushButton:pressed {
                background-color: #2a2a2a;
            }
        """)
        toolbar_layout.addWidget(self.btn_refresh)

        main_layout.addLayout(toolbar_layout)

        # =========================
        # Current Workspace Label
        # =========================
        self.workspace_label = QtWidgets.QLabel(
            "【 No Workspace Loaded 】"
        )

        self.workspace_label.setAlignment(
            QtCore.Qt.AlignCenter
        )

        self.workspace_label.setObjectName(
            "WorkspaceLabel"
        )

        main_layout.addWidget(
            self.workspace_label
        )

        self.btn_open_folder = QtWidgets.QPushButton("F")
        self.btn_open_folder.setFixedSize(24, 24)
        self.btn_open_folder.setToolTip("Open Folder")
        self.btn_open_folder.setStyleSheet("""
            QPushButton {
                background-color: #3a3a3a;
                color: #ccc;
                border: 1px solid #555;
                border-radius: 3px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #505050;
                color: #fff;
                border: 1px solid #777;
            }
            QPushButton:pressed {
                background-color: #2a2a2a;
            }
        """)
        toolbar_layout.addWidget(self.btn_open_folder)

        # =========================
        # Button Function Bind
        # =========================
        self.btn_refresh.setText("R")
        self.btn_refresh.clicked.connect(
            self.refresh_workspace
        )

        self.btn_open_folder.setText("N")
        self.btn_open_folder.setToolTip(
            "New Workspace"
        )
        self.btn_open_folder.clicked.connect(
            self.create_new_workspace
        )

        main_layout.addLayout(toolbar_layout)


        # WIP
        main_layout.addWidget(
            QtWidgets.QLabel(
                "🚧 WIP ",
                objectName="WIPHeader"
            )
        )

        self.wip_list = ToDoListWidget(
            "WIP",
            self
        )

        main_layout.addWidget(
            self.wip_list
        )

        # TODO
        main_layout.addWidget(
            QtWidgets.QLabel(
                "📋 TODO ",
                objectName="TODOHeader"
            )
        )

        self.todo_list = ToDoListWidget(
            "TODO",
            self
        )

        main_layout.addWidget(
            self.todo_list
        )

        # Input
        input_layout = QtWidgets.QHBoxLayout()

        self.line_edit = QtWidgets.QLineEdit()

        self.line_edit.setPlaceholderText(
            "Add New Task..."
        )

        self.line_edit.returnPressed.connect(
            self.add_new_task
        )

        btn_add = QtWidgets.QPushButton("+")
        btn_add.setFixedWidth(40)

        btn_add.clicked.connect(
            self.add_new_task
        )

        input_layout.addWidget(
            self.line_edit
        )

        input_layout.addWidget(
            btn_add
        )

        main_layout.addLayout(
            input_layout
        )

        # Clear Button
        btn_clear = QtWidgets.QPushButton(
            "Clear Completed WIP"
        )

        btn_clear.clicked.connect(
            self.clear_completed
        )

        main_layout.addWidget(
            btn_clear
        )

    # =========================
    # Add Task
    # =========================
    def add_new_task(self):

        scene_path = cmds.file(
            q=True,
            sn=True
        )

        if not scene_path:
            QtWidgets.QMessageBox.warning(
                self,
                "Save Required",
                "Please save Maya scene first before adding tasks."
            )

            return

        text = self.line_edit.text().strip()

        if not text:
            return

        self._block_save = True

        self.create_item(
            self.todo_list,
            text
        )

        self.line_edit.clear()

        self._block_save = False

        self.btn_refresh = None
        self.btn_open_folder = None

        self.save_data()

    # =========================
    # Create Item
    # =========================
    def create_item(
        self,
        target_list,
        text,
        checked=False,
        detail=""
    ):

        item = QtWidgets.QListWidgetItem(text)

        item.setData(
            QtCore.Qt.UserRole,
            detail
        )

        item.setData(
            self.FOCUS_ROLE,
            False
        )

        item.setData(
            self.TEXT_ROLE,
            text
        )

        target_list.addItem(item)

        self.setup_item_by_list(item)

        if checked:

            item.setCheckState(
                QtCore.Qt.Checked
            )

        else:

            item.setCheckState(
                QtCore.Qt.Unchecked
            )

        self.refresh_item_display_text(
            item
        )

        self.update_item_look(
            item
        )

        self.refresh_tooltip(
            item
        )

        return item

    # =========================
    # Setup Item
    # =========================
    def setup_item_by_list(self, item):

        parent_list = item.listWidget()

        flags = (
            QtCore.Qt.ItemIsSelectable |
            QtCore.Qt.ItemIsEnabled |
            QtCore.Qt.ItemIsDragEnabled
        )

        if parent_list.objectName() == "WIP":

            item.setFlags(
                flags |
                QtCore.Qt.ItemIsUserCheckable
            )

        else:

            item.setFlags(flags)

    # =========================
    # Update Item Look
    # =========================
    def update_item_look(self, item):

        if not item:
            return

        font = item.font()

        is_checked = (
            item.checkState() ==
            QtCore.Qt.Checked
        )

        font.setStrikeOut(is_checked)

        item.setFont(font)

        is_focus = item.data(
            self.FOCUS_ROLE
        )

        if is_checked:

            color = QtGui.QColor(
                120,
                120,
                120
            )

        elif is_focus:

            color = QtGui.QColor(
                255,
                220,
                120
            )

        else:

            color = QtGui.QColor(
                220,
                220,
                220
            )

        item.setForeground(color)

    # =========================
    # Refresh Text
    # =========================
    def refresh_item_display_text(self, item):

        original_text = item.data(
            self.TEXT_ROLE
        )

        if not original_text:
            original_text = item.text()

        is_focus = item.data(
            self.FOCUS_ROLE
        )

        if is_focus:

            item.setText(
                original_text + "  ⭐"
            )

        else:

            item.setText(
                original_text
            )

    # =========================
    # Refresh Tooltip
    # =========================
    def refresh_tooltip(self, item):

        detail = item.data(
            QtCore.Qt.UserRole
        )

        if detail:

            item.setToolTip(
                "<b>Detail:</b><br>" +
                detail.replace(
                    "\n",
                    "<br>"
                )
            )

        else:

            item.setToolTip(
                "No Detail"
            )

    # =========================
    # Refresh Styles
    # =========================
    def refresh_all_styles(self):

        self._block_save = True

        for lst in [
            self.wip_list,
            self.todo_list
        ]:

            for i in range(lst.count()):

                item = lst.item(i)

                self.update_item_look(
                    item
                )

        self._block_save = False

        self.btn_refresh = None
        self.btn_open_folder = None

    # =========================
    # Edit Detail
    # =========================
    def edit_item_detail(self, item):

        dialog = DetailEditDialog(
            item.data(self.TEXT_ROLE),
            item.data(QtCore.Qt.UserRole),
            self
        )

        if dialog.exec_():

            title, detail = dialog.get_data()

            item.setData(
                self.TEXT_ROLE,
                title
            )

            item.setData(
                QtCore.Qt.UserRole,
                detail
            )

            self.refresh_item_display_text(
                item
            )

            self.refresh_tooltip(
                item
            )

            self.save_data()

    # =========================
    # Duplicate Item
    # =========================
    def duplicate_item(self, item):

        parent_list = item.listWidget()

        self.create_item(
            parent_list,
            item.data(self.TEXT_ROLE),
            item.checkState() ==
            QtCore.Qt.Checked,
            item.data(QtCore.Qt.UserRole)
        )

        self.save_data()

    # =========================
    # Delete Item
    # =========================
    def delete_item(self, item):

        parent_list = item.listWidget()

        row = parent_list.row(item)

        parent_list.takeItem(row)

        self.save_data()

    # =========================
    # Move Item
    # =========================
    def move_item_between_lists(self, item):

        source_list = item.listWidget()

        text = item.data(
            self.TEXT_ROLE
        )

        checked = (
            item.checkState() ==
            QtCore.Qt.Checked
        )

        detail = item.data(
            QtCore.Qt.UserRole
        )

        focus = item.data(
            self.FOCUS_ROLE
        )

        row = source_list.row(item)

        source_list.takeItem(row)

        if source_list == self.todo_list:

            new_item = self.create_item(
                self.wip_list,
                text,
                checked,
                detail
            )

        else:

            new_item = self.create_item(
                self.todo_list,
                text,
                False,
                detail
            )

        new_item.setData(
            self.FOCUS_ROLE,
            focus
        )

        self.refresh_item_display_text(
            new_item
        )

        self.update_item_look(
            new_item
        )

        self.save_data()

    # =========================
    # Focus Functions
    # =========================
    def clear_all_focus(self):

        for i in range(
            self.wip_list.count()
        ):

            item = self.wip_list.item(i)

            item.setData(
                self.FOCUS_ROLE,
                False
            )

            self.refresh_item_display_text(
                item
            )

            self.update_item_look(
                item
            )

    def set_focus_item(self, item):

        self.clear_all_focus()

        item.setData(
            self.FOCUS_ROLE,
            True
        )

        self.refresh_item_display_text(
            item
        )

        self.update_item_look(
            item
        )

        self.save_data()

    # =========================
    # Clear Completed
    # =========================
    def clear_completed(self):

        self._block_save = True

        for i in reversed(
            range(
                self.wip_list.count()
            )
        ):

            item = self.wip_list.item(i)

            if (
                item.checkState() ==
                QtCore.Qt.Checked
            ):

                self.wip_list.takeItem(i)

        self._block_save = False

        self.btn_refresh = None
        self.btn_open_folder = None

        self.save_data()

    # =========================
    # Save Data
    # =========================
    def save_data(self, *args):

        if self._block_save:
            return

        if not self.CURRENT_WORKSPACE:
            return

        all_data = {
            "WIP": self.get_list_data(self.wip_list),
            "TODO": self.get_list_data(self.todo_list)
        }

        try:
            with open(self.CURRENT_WORKSPACE, "w") as f:
                json.dump(
                    all_data,
                    f,
                    indent=4
                )

        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self,
                "Save Failed",
                str(e)
            )

    # =========================
    # Get List Data
    # =========================
    def get_list_data(self, widget):

        items = []

        for i in range(widget.count()):

            item = widget.item(i)

            items.append({

                "text":
                    item.data(
                        self.TEXT_ROLE
                    ),

                "status":
                    item.checkState() ==
                    QtCore.Qt.Checked,

                "detail":
                    item.data(
                        QtCore.Qt.UserRole
                    ),

                "focus":
                    item.data(
                        self.FOCUS_ROLE
                    )
            })

        return items

    # =========================
    # Load Data
    # =========================
    def load_data(self):

        self._block_save = True

        raw = cmds.fileInfo(
            self.STORAGE_KEY,
            q=True
        )

        if raw:

            try:

                data_str = ""

                for i in range(
                    0,
                    len(raw),
                    2
                ):

                    if raw[i] == self.STORAGE_KEY:

                        data_str = raw[i + 1]

                        break

                if data_str:

                    full_data = json.loads(
                        data_str
                    )

                    # WIP
                    for task in full_data.get(
                        "WIP",
                        []
                    ):

                        new_item = self.create_item(
                            self.wip_list,
                            task.get("text", ""),
                            task.get("status", False),
                            task.get("detail", "")
                        )

                        new_item.setData(
                            self.FOCUS_ROLE,
                            task.get("focus", False)
                        )

                        self.refresh_item_display_text(
                            new_item
                        )

                        self.update_item_look(
                            new_item
                        )

                    # TODO
                    for task in full_data.get(
                        "TODO",
                        []
                    ):

                        new_item = self.create_item(
                            self.todo_list,
                            task.get("text", ""),
                            False,
                            task.get("detail", "")
                        )

                        new_item.setData(
                            self.FOCUS_ROLE,
                            False
                        )

                        self.refresh_item_display_text(
                            new_item
                        )

                        self.update_item_look(
                            new_item
                        )

            except:
                pass

        self._block_save = False

        self.btn_refresh = None
        self.btn_open_folder = None

        self.refresh_all_styles()

    # =========================
    # NEW: Get Scene Directory
    # =========================
    def get_scene_directory(self):

        # =========================
        # Update Workspace Label
        # =========================
        scene_path = cmds.file(q=True, sn=True)

        if not scene_path:
            QtWidgets.QMessageBox.warning(
                self,
                "Warning",
                "Please save Maya scene first."
            )
            return None

        return os.path.dirname(scene_path)


    # =========================
    # Update Workspace Label
    # =========================
    def update_workspace_label(self, identifier=None):

        if not identifier:
            self.workspace_label.setText(
                "【 No Workspace Loaded 】"
            )
            return

        self.workspace_label.setText(
            "【 {} Workspace 】".format(
                identifier.upper()
            )
        )

    # =========================
    # NEW: Get Scene Base Name
    # =========================
    def get_scene_basename(self):

        scene_path = cmds.file(q=True, sn=True)

        if not scene_path:
            return None

        file_name = os.path.basename(scene_path)
        base_name = os.path.splitext(file_name)[0]

        return base_name

    # =========================
    # NEW: Find Workspace JSON Files
    # =========================
    def find_workspace_files(self):

        scene_dir = self.get_scene_directory()

        if not scene_dir:
            return []

        scene_base = self.get_scene_basename()

        if not scene_base:
            return []

        result = []

        for file_name in os.listdir(scene_dir):

            if (
                    file_name.startswith(scene_base + "_") and
                    file_name.endswith(".todo.json")
            ):
                result.append(
                    os.path.join(scene_dir, file_name)
                )

        return result

        # =========================
        scene_dir = self.get_scene_directory()

        if not scene_dir:
            return

        scene_base = self.get_scene_basename()

        if not scene_base:
            return

        text, ok = QtWidgets.QInputDialog.getText(
            self,
            "Create New Workspace",
            "Input Identifier (Example: MOD / LGT / FX):"
        )

        if not ok:
            return

        identifier = text.strip()

        if not identifier:
            return

        file_name = "{}_{}.todo.json".format(
            scene_base,
            identifier
        )

        json_path = os.path.join(
            scene_dir,
            file_name
        )

        if os.path.exists(json_path):
            QtWidgets.QMessageBox.warning(
                self,
                "Warning",
                "Workspace already exists."
            )
            return

        empty_data = {
            "WIP": [],
            "TODO": []
        }

        with open(json_path, "w") as f:
            json.dump(
                empty_data,
                f,
                indent=4
            )

        self.CURRENT_WORKSPACE = json_path

        QtWidgets.QMessageBox.information(
            self,
            "Success",
            "Workspace created:\n{}".format(file_name)
        )

    # =========================
    # NEW: Refresh Workspace
    # =========================
    def refresh_workspace(self):

        files = self.find_workspace_files()

        if not files:
            QtWidgets.QMessageBox.information(
                self,
                "No Workspace",
                "No 'ToDoList' found in scene folder."
            )
            return

        selected_file = None

        if len(files) == 1:
            selected_file = files[0]

        else:
            display_map = {}

            for f in files:
                file_name = os.path.basename(f)

                identifier = (
                    file_name
                    .replace(self.get_scene_basename() + "_", "")
                    .replace(".todo.json", "")
                )

                display_map[identifier] = f

            identifiers = sorted(display_map.keys())

            selected_name, ok = QtWidgets.QInputDialog.getItem(
                self,
                "Select Workspace",
                "Choose TODO Workspace:",
                identifiers,
                0,
                False
            )

            if not ok:
                return

            selected_file = display_map.get(
                selected_name
            )

        if not selected_file:
            return

        self.CURRENT_WORKSPACE = selected_file

        self.update_workspace_label(
            selected_name
        )

        self.load_workspace_json(
            selected_file
        )


    # =========================
    # NEW: Create New Workspace
    # =========================
    def create_new_workspace(self):

        scene_dir = self.get_scene_directory()

        if not scene_dir:
            return

        scene_base = self.get_scene_basename()

        if not scene_base:
            return

        text, ok = QtWidgets.QInputDialog.getText(
            self,
            "Create New Workspace",
            "Input Identifier (Example: MOD / LGT / FX):"
        )

        if not ok:
            return

        identifier = text.strip()

        if not identifier:
            return

        file_name = "{}_{}.todo.json".format(
            scene_base,
            identifier
        )

        json_path = os.path.join(
            scene_dir,
            file_name
        )

        if os.path.exists(json_path):
            QtWidgets.QMessageBox.warning(
                self,
                "Warning",
                "Workspace already exists."
            )
            return

        empty_data = {
            "WIP": [],
            "TODO": []
        }

        with open(json_path, "w") as f:
            json.dump(
                empty_data,
                f,
                indent=4
            )

        self.CURRENT_WORKSPACE = json_path

        self.update_workspace_label(
            identifier
        )

        QtWidgets.QMessageBox.information(
            self,
            "Success",
            "Workspace created:\n{}".format(file_name)
        )


    # =========================
    # NEW: Load Workspace JSON
    # =========================
    def load_workspace_json(self, json_path):

        self._block_save = True

        self.wip_list.clear()
        self.todo_list.clear()

        try:
            with open(json_path, "r") as f:
                full_data = json.load(f)

            for task in full_data.get("WIP", []):
                item = self.create_item(
                    self.wip_list,
                    task.get("text", ""),
                    task.get("status", False),
                    task.get("detail", "")
                )

                item.setData(
                    self.FOCUS_ROLE,
                    task.get("focus", False)
                )

                self.refresh_item_display_text(item)
                self.update_item_look(item)

            for task in full_data.get("TODO", []):
                item = self.create_item(
                    self.todo_list,
                    task.get("text", ""),
                    False,
                    task.get("detail", "")
                )

                self.refresh_item_display_text(item)
                self.update_item_look(item)

        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self,
                "Load Failed",
                str(e)
            )

        self._block_save = False




# =========================
# Show UI
# =========================
def show_todo_it():

    control_name = (
        "HurryUP_ToDoItWindowWorkspaceControl"
    )

    if cmds.workspaceControl(
        control_name,
        exists=True
    ):

        cmds.deleteUI(control_name)

    ui = ToDoItWindow()

    ui.show(
        dockable=True,
        area='right',
        floating=False
    )
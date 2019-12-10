from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import matplotlib.colors as pltc
import config


# noinspection PyArgumentList
class SettingsWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.tabs = QTabWidget()
        self.general = GeneralTab()
        self.labels = LabelsTab()
        self.button_panel = QWidget()

        self.setWindowTitle("Settings")
        self.setWindowModality(Qt.ApplicationModal)
        self.setFixedSize(640, 480)

        self.init()
        self.show()

    def init(self):
        self.init_buttons()

        layout = QVBoxLayout()
        self.tabs.addTab(self.general, "General")
        self.tabs.addTab(self.labels, "Labels")
        layout.addWidget(self.tabs)
        layout.addWidget(self.button_panel)
        self.setLayout(layout)

    def init_buttons(self):
        button_layout = QHBoxLayout()
        ok_button = QPushButton("Ok")
        apply_button = QPushButton("Apply")
        cancel_button = QPushButton("Cancel")
        ok_button.clicked.connect(self.ok)
        apply_button.clicked.connect(self.apply)
        cancel_button.clicked.connect(self.cancel)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        button_layout.addWidget(spacer)
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(apply_button)
        button_layout.addWidget(ok_button)
        self.button_panel.setLayout(button_layout)

    def ok(self):
        self.apply()
        self.close()

    def apply(self):
        self.general.apply()
        self.labels.apply()
        config.tsl_config.save()

    def cancel(self):
        self.close()


# noinspection PyArgumentList
class GeneralTab(QWidget):
    def __init__(self):
        super().__init__()
        self.autosave = QCheckBox("Autosave", self)
        self.autosave.setChecked(config.tsl_config.config["autosave"])
        self.autosave.move(40, 40)

        title = QLabel("TSL (Time Series Labeler)", self)
        title.setFont(QFont("Times", 10, QFont.Bold))
        credit = QLabel("Developed by zorzr\nLicensed under GPL v3.0", self)
        title.move(390, 320)
        credit.move(390, 338)

    def apply(self):
        conf = config.tsl_config.config
        conf["autosave"] = self.autosave.isChecked()


# noinspection PyArgumentList
class LabelsTab(QWidget):
    def __init__(self):
        super().__init__()
        labels, colors = config.data_config.get_labels_info()
        labels_list = [(labels[i], colors[i]) for i in range(len(labels))]

        self.table = LabelTable(labels_list)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        panel_layout = QHBoxLayout()
        panel = QWidget()
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        add_button = QPushButton("Add")
        edit_button = QPushButton("Edit")
        remove_button = QPushButton("Remove")
        add_button.clicked.connect(self.add)
        edit_button.clicked.connect(self.edit)
        remove_button.clicked.connect(self.remove)

        panel.setLayout(panel_layout)
        panel_layout.addWidget(add_button)
        panel_layout.addWidget(edit_button)
        panel_layout.addWidget(remove_button)
        panel_layout.addWidget(spacer)

        tab_layout = QVBoxLayout()
        tab_layout.addWidget(self.table)
        tab_layout.addWidget(panel)
        self.setLayout(tab_layout)

    # Labels buttons
    def add(self):
        dialog = LabelDialog()
        ret = dialog.exec_()
        if ret == 0:
            return

        name = dialog.name.text()
        color = dialog.color.text()

        if pltc.is_color_like(color):
            self.table.insert_row(name, pltc.to_hex(color))

    def edit(self):
        if self.table.rowCount() == 0:
            return

        row = self.table.currentRow()
        row_name = self.table.item(row, 0).text()
        row_color = self.table.item(row, 1).text()

        dialog = LabelDialog(row_name, row_color)
        ret = dialog.exec_()
        if ret == 0:
            return

        name = dialog.name.text()
        color = dialog.color.text()

        if pltc.is_color_like(color):
            self.table.item(row, 0).setText(name)
            self.table.item(row, 1).setText(pltc.to_hex(color))

    def remove(self):
        if self.table.rowCount() == 1:
            return

        self.table.removeRow(self.table.currentRow())

    def mousePressEvent(self, event):
        self.clear_selected()

    def clear_selected(self):
        self.table.clearSelection()
        self.table.setCurrentCell(-1, -1)

    def apply(self):
        names, colors = self.table.generate_labels_list()
        config.data_config.set_labels_info(names, colors)


class LabelTable(QTableWidget):
    def __init__(self, labels_list):
        super().__init__()
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["Label name", "Color"])

        for label in labels_list:
            self.insert_row(label[0], label[1])

        self.verticalHeader().hide()
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection | QAbstractItemView.NoSelection)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

    def insert_row(self, label, color):
        row = self.rowCount()
        self.insertRow(row)
        self.setItem(row, 0, QTableWidgetItem(label))
        self.setItem(row, 1, QTableWidgetItem(color))
        self.item(row, 0).setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self.item(row, 1).setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

    def generate_labels_list(self):
        names_list = []
        colors_list = []
        for i in range(self.rowCount()):
            name = self.item(i, 0).text()
            color = self.item(i, 1).text()
            names_list.append(name)
            colors_list.append(color)
        return names_list, colors_list


# noinspection PyArgumentList
class LabelDialog(QDialog):
    def __init__(self, label="", color=""):
        super().__init__()
        self.setWindowTitle("Customization")
        self.resize(250, 130)

        self.group_box = QGroupBox("Label details")
        layout = QFormLayout()

        self.name = QLineEdit()
        self.color = QLineEdit()
        self.pick = QPushButton("Pick")

        self.name.setText(label)
        self.color.setText(color)
        self.name.setMaxLength(20)

        self.pick.clicked.connect(self.pick_color)
        self.name.textChanged.connect(self.validate_form)
        self.color.textChanged.connect(self.validate_form)

        color_input = QWidget()
        color_layout = QHBoxLayout()
        color_layout.addWidget(self.color)
        color_layout.addWidget(self.pick)
        color_input.setLayout(color_layout)
        color_layout.setContentsMargins(0, 0, 0, 0)

        layout.addRow(QLabel("Name:"), self.name)
        layout.addRow(QLabel("Color:"), color_input)
        self.group_box.setLayout(layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.group_box)
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)

        self.bad_names = []
        self.set_bad_names()

    def pick_color(self):
        dialog = QColorDialog()

        # Default matplotlib colors are proposed as custom colors
        for i, col in enumerate(['C' + str(j) for j in range(10)]):  # TODO: find a better way to enumerate
            dialog.setCustomColor(i, QColor(pltc.to_hex(col)))

        color = dialog.getColor()
        if color.isValid():
            self.color.setText(color.name())

    def validate_form(self):
        name = self.name.text()
        color = self.color.text()

        if name not in self.bad_names and not name.isspace() \
                and pltc.is_color_like(color) and pltc.is_color_like(pltc.to_hex(color)):
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)
        else:
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)

    def set_bad_names(self):
        conf = config.data_config
        data_col = conf.datafile.get_data_header()
        labels, _ = conf.get_labels_info()
        functions = conf.get_functions()
        self.bad_names = [""] + data_col + labels + functions
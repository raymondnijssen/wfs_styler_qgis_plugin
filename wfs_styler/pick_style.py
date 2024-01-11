import os

from qgis.PyQt import uic
from PyQt5.QtWidgets import QDialog, QDialogButtonBox

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'pick_style.ui'))


class PickStyleDialog(QDialog, FORM_CLASS):
    def __init__(self, plugin, parent=None):
        """Constructor."""
        super(PickStyleDialog, self).__init__(parent)

        self.setupUi(self)
        self.plugin = plugin

        self.list_styles.itemSelectionChanged.connect(self.update_widgets)

        self.update_widgets()
    
    def set_styles(self, styles):
        self.list_styles.clear()
        for name, value in styles.items():
            self.list_styles.addItem(name)
        
        if self.list_styles.count() == 1:
            self.list_styles.setCurrentRow(0)

        self.update_widgets()
    
    def update_widgets(self):
         enable_ok_button = self.list_styles.currentItem() is not None
         self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(enable_ok_button)

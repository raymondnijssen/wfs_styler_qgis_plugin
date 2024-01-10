import os

from qgis.PyQt import uic
from PyQt5.QtWidgets import QDialog

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'pick_style.ui'))


class PickStyleDialog(QDialog, FORM_CLASS):
    def __init__(self, plugin, parent=None):
        """Constructor."""
        super(PickStyleDialog, self).__init__(parent)

        self.setupUi(self)
        #self.iface = iface
        self.plugin = plugin
    
    def set_styles(self, styles):
        self.list_styles.clear()
        for name, value in styles.items():
            self.list_styles.addItem(name)
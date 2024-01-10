import os

from PyQt5.QtCore import QStandardPaths
from PyQt5.QtWidgets import QAction
from PyQt5.QtGui import QIcon

from .wfs_probe import WfsStyleProbe

class WfsStylerPlugin:

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)

    def initGui(self):
        icon = QIcon(os.path.join(self.plugin_dir, 'icon.svg'))
        self.action = QAction(icon, 'Try to set SLD to current layer', self.iface.mainWindow())
        self.action.triggered.connect(self.probe_active_layer)
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        self.iface.removeToolBarIcon(self.action)
        del self.action


    def is_wfs_layer(self, layer):
        return layer.storageType() == 'OGC WFS (Web Feature Service)'

    def probe_active_layer(self):
        layer = self.iface.activeLayer()
        if not self.is_wfs_layer(layer):
            print('Not a WFS layer')
            return

        probe = WfsStyleProbe(layer)

        style_name = next(iter(probe.styles)) # Pick first
        #print(style_name)

        tmp_dir = QStandardPaths.writableLocation(QStandardPaths.TempLocation)
        sld_fn = os.path.join(tmp_dir, 'qgis_wfs_styler_plugin_style.sld')
        #print(sld_fn)

        if probe.get_sld(style_name, sld_fn):
            layer.loadSldStyle(sld_fn)
        else:
            print('No SLD file created')

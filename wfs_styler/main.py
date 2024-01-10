import os

from PyQt5.QtCore import QStandardPaths
from PyQt5.QtWidgets import QAction, QDialog
from PyQt5.QtGui import QIcon

from .pick_style import PickStyleDialog
from .wfs_probe import WfsStyleProbe


class WfsStylerPlugin():

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.pick_style_dlg = PickStyleDialog(self)

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
        print(probe.styles)

        print('Found styles: {}'.format(len(probe.styles)))

        if len(probe.styles) == 0:
            print('No styles found')
            return

        self.pick_style_dlg.set_styles(probe.styles)

        #self.pick_style_dlg.show()
        #self.generate_calc_input_dlg.show()
        result = self.pick_style_dlg.exec_()
        if result:
            style_name = self.pick_style_dlg.list_styles.currentItem().text()
            print(f'Picked style: {style_name}')
        else:
            print('Canceled')
            return
        #style_name = next(iter(probe.styles)) # Pick first
        #print(style_name)

        tmp_dir = QStandardPaths.writableLocation(QStandardPaths.TempLocation)
        sld_fn = os.path.join(tmp_dir, 'qgis_wfs_styler_plugin_style.sld')
        #print(sld_fn)

        if probe.get_sld(style_name, sld_fn):
            layer.loadSldStyle(sld_fn)
        else:
            print('No SLD file created')

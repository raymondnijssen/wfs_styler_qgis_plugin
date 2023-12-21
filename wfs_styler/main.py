import os
from urllib.parse import urlparse

from PyQt5.QtWidgets import QAction
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QIcon
from PyQt5.QtNetwork import QNetworkRequest

from qgis.core import QgsBlockingNetworkRequest


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

    def _dict_from_source(self, src):
        result = {}
        kv_parts = src.split()
        for kv_part in kv_parts:
            if '=' in kv_part:
                k = kv_part.split('=')[0]
                v = kv_part.split('=')[1].replace("'", "")
                result[k] = v
        return result

    def probe_active_layer(self):
        layer = self.iface.activeLayer()
        self.probe_layer(layer)

    def probe_layer(self, layer):
        print('============== probe_layer():', layer, layer.name())

        sld_urls = self.guess_sld_urls(layer)

        sld_url = sld_urls[0]

        content = self.run_request(sld_url)

        sld_fn = os.path.join(self.plugin_dir, 'temp.sld')
        print(sld_fn)
        # sld_fn = '/home/raymond/terglobo/projecten/ogg/zeeland/support/20220201_wfs_sld/wtlbscmnmwalvlk.sld'

        # manager = QgsNetworkAccessManager.instance()
        # print(content)

        with open(sld_fn, 'wb') as sld_file:
            sld_file.write(bytes(content))

        layer.loadSldStyle(sld_fn)

    def run_request(self, sld_url):
        url = QUrl(sld_url)
        # print(url)
        request = QNetworkRequest(url)
        request.setRawHeader(b'Content-Type', b'application/xml')
        qgis_request = QgsBlockingNetworkRequest()
        err = qgis_request.get(request, True)
        if err > 0:
            # TODO: return error code or None or something...
            pass
            # print(error)

        reply = qgis_request.reply()
        # print(reply)
        content = reply.content()
        return content

    def guess_sld_urls(self, layer):
        result = []
        result += self.guess_geoserver_sld_urls(layer)
        return result

    def guess_geoserver_sld_urls(self, layer):
        source = self._dict_from_source(layer.source())
        print(source)

        wfs_url = source['url']
        print(wfs_url)

        wfs_layer = source['typename']
        print(wfs_layer)

        wms_url = wfs_url.replace('/wfs', '/wms')
        print(wms_url)

        # https://opengeodata.zeeland.nl/geoserver/Archeologie/wms?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetStyles&layers=geocmd_wtlbscmnmwalvlk
        sld_url = f'{wms_url}?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetStyles&layers={wfs_layer}'
        print(sld_url)

        return [sld_url]

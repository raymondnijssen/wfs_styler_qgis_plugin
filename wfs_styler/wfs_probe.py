# ---------------------------------------------------------------------
# Copyright (C) 2022 Raymond Nijssen
# ---------------------------------------------------------------------
# Licensed under the terms of GNU GPL 2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# ---------------------------------------------------------------------

import os
import xml.etree.ElementTree as ET
import io

from PyQt5.QtCore import QUrl
from PyQt5.QtNetwork import QNetworkRequest

from qgis.core import QgsBlockingNetworkRequest
from urllib.parse import urlparse

from owslib.wms import WebMapService

class WfsStyleProbe(object):

    def __init__(self, layer):
        self.layer = layer
        self.source_dict = self.get_source_dict(self.layer)
        self.wfs_url = QUrl(self.source_dict.get('url', None))
        self.layer_name = self.source_dict.get('typename', None)
        #self.capabilities_tree = self.get_capabilities()
        self.styles = self.get_styles_owslib()

    def __str__(self):
        result = ('WfsStyleProbe[]')
        return result

    def get_source_dict(self, layer):
        """Creates a dictionary from a QgsVectorLayer source string (bit hacky...)"""
        s = self.layer.source()
        return self._get_dict_from_string(s, kv_sep='=')
    
    def _get_dict_from_string(self, s, item_sep=' ', kv_sep=':'):
        result = {}
        kv_parts = s.split(item_sep)
        for kv_part in kv_parts:
            if kv_sep in kv_part:
                k = kv_part.split(kv_sep)[0]
                v = kv_part.split(kv_sep)[1].strip("'")
                result[k] = v
        return result

    def run_request(self, url):
        url = QUrl(url)
        # print(url)
        request = QNetworkRequest(url)
        request.setRawHeader(b'Content-Type', b'application/xml')
        qgis_request = QgsBlockingNetworkRequest()
        err = qgis_request.get(request, True)
        if err > 0:
            # TODO: return error code or None or something...
            print(err)
            return

        reply = qgis_request.reply()
        # print(reply)
        return reply

    def get_styles_owslib(self):
        self.wms_url = self.guess_wms_url()
        if self.wms_url is None:
            return {}
        
        wms = WebMapService(self.wms_url.toString())

        layer_names = [self.layer_name]
        layer_names.append(self.layer_name.split(':')[-1]) # Without the name space and ":"

        result = {}
        for layer_name in layer_names:
            pass
            try:
                styles = wms.contents[layer_name].styles
                result.update(styles)
            except(KeyError):
                print(f'  passing {layer_name}')
                pass
        
        return result

    def get_sld(self, style_name, sld_fn):
        style = self.styles.get(style_name, None)

        if style is None:
            print(f'style {style_name} not found')
            return False

        # print(style['title'])

        style_url = QUrl(self.wms_url)
        style_url.setQuery(f'SERVICE=WMS&VERSION=1.1.1&REQUEST=GetStyles&layers={self.layer_name}&STYLE={style_name}')
        print(style_url.toEncoded())

        reply = self.run_request(style_url)
        # print(reply)
        content = reply.content()

        with open(sld_fn, 'w') as sld_file:
            sld_file.write(content.data().decode('utf8'))
            return True

    def get_capabilities(self):
        '''Depricated'''
        wms_url = self.guess_wms_url()

        if wms_url is None:
            return
        
        capabilities_url = QUrl(wms_url)
        capabilities_url.setQuery('SERVICE=WMS&REQUEST=GetCapabilities&ACCEPTVERSIONS=2.0.0,1.1.0,1.0.0')

        reply = self.run_request(capabilities_url)
        content = reply.content()
        result = ET.fromstring(content)
        return result

    def guess_wms_url(self):
        if self.wfs_url is None or self.wfs_url.isEmpty():
            return
        
        wms_path_elements = []
        for wfs_path_elem in self.wfs_url.path().split('/'):
            if wfs_path_elem.lower() == 'wfs':
                wms_path_elements.append('wms')
            else:
                wms_path_elements.append(wfs_path_elem)
        wms_path = '/'.join(wms_path_elements)

        wms_url = QUrl(self.wfs_url)
        wms_url.setPath(wms_path)

        return wms_url



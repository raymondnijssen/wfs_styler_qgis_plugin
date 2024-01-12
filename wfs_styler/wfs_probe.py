# ---------------------------------------------------------------------
# Copyright (C) 2023 Raymond Nijssen
# ---------------------------------------------------------------------
# Licensed under the EUPL
# ---------------------------------------------------------------------

from PyQt5.QtCore import QUrl
from PyQt5.QtNetwork import QNetworkRequest
from PyQt5.QtXml import QDomDocument

from qgis.core import QgsBlockingNetworkRequest
from urllib.parse import urlparse


class WfsStyleProbe(object):

    def __init__(self, layer):
        self.layer = layer
        self.source_dict = self.get_source_dict(self.layer)
        self.wfs_url = QUrl(self.source_dict.get('url', None))
        self.layer_name = self.source_dict.get('typename', None)
        self.styles = self.get_styles()

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
            # print('error', err)
            return

        reply = qgis_request.reply()
        # print(reply)
        return reply

    def get_styles(self):
        wms_urls = self.guess_wms_urls()
        # print(wms_urls)

        if len(wms_urls) == 0:
            return {}

        style_dict = {}

        layer_names = [self.layer_name]
        if ':' in self.layer_name:
            layer_names.append(self.layer_name.split(':')[-1])
        # print(layer_names)

        for layer_name in layer_names:
            for wms_url in wms_urls:
                styles_url = QUrl(wms_url)
                styles_url.setQuery(f'SERVICE=WMS&VERSION=1.1.1&REQUEST=GetStyles&LAYERS={layer_name}')

                reply = self.run_request(styles_url)

                if reply is None:
                    continue

                # print(reply.content())
                content = reply.content()

                doc = QDomDocument()
                doc.setContent(content, True)

                named_layer = doc.firstChildElement('Namedlayer')
                if named_layer is None:
                    break

                user_styles = doc.elementsByTagName('UserStyle')
                # print(user_styles, len(user_styles))

                for i in range(len(user_styles)):
                    user_style = user_styles.item(i)
                    node = user_style.firstChildElement('Name')
                    name = node.toElement().text()
                    if name == '':
                        name = f'Style {i + 1}' # Should always have name.
                    node = user_style.firstChildElement('Title')
                    title = node.toElement().text()
                    node = user_style.firstChildElement('FeatureTypeStyle')
                    
                    style_dict[name] = {
                        'name': name,
                        'title': title,
                        'sld_node': node
                    }
                
                # print(style_dict)
                if len(style_dict) > 0:
                    self.wms_url = wms_url
                    return style_dict
            
        return style_dict

    def create_sld_file(self, style_name, sld_fn):
        style = self.styles.get(style_name, None)
        # print(style)

        if style is None:
            print(f'style {style_name} not found')
            return False

        doc = QDomDocument()

        inst = doc.createProcessingInstruction('xml', 'version="1.0" encoding="UTF-8"')
        doc.appendChild(inst)

        sld_elem = doc.createElement('sld:StyledLayerDescriptor')
        sld_elem.setAttribute('xmlns', 'http://www.opengis.net/sld')
        sld_elem.setAttribute('version', '1.1.0')
        sld_elem.setAttribute('xsi:schemaLocation', 'http://www.opengis.net/sld http://schemas.opengis.net/sld/1.1.0/StyledLayerDescriptor.xsd')
        sld_elem.setAttribute('xmlns:se', 'http://www.opengis.net/se')
        sld_elem.setAttribute('xmlns:ogc', 'http://www.opengis.net/ogc')
        sld_elem.setAttribute('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        sld_elem.setAttribute('xmlns:xlink', 'http://www.w3.org/1999/xlink')

        named_layer_elem = doc.createElement('sld:NamedLayer')

        layer_name_elem = doc.createElement('sld:Name')
        layer_name_elem.appendChild(doc.createTextNode(self.layer_name))
        named_layer_elem.appendChild(layer_name_elem)

        user_style_elem = doc.createElement('sld:UserStyle')

        style_name_elem = doc.createElement('sld:Name')
        style_name_elem.appendChild(doc.createTextNode(style_name))
        user_style_elem.appendChild(style_name_elem)

        sld_node = style['sld_node']
        user_style_elem.appendChild(sld_node)

        named_layer_elem.appendChild(user_style_elem)

        sld_elem.appendChild(named_layer_elem)
        doc.appendChild(sld_elem)

        with open(sld_fn, 'w') as sld_file:
            sld_file.write(doc.toString())
        return True

    def guess_wms_urls(self):
        if self.wfs_url is None or self.wfs_url.isEmpty():
            return []
        
        result = []

        wms_path_elements = []
        for wfs_path_elem in self.wfs_url.path().split('/'):
            if wfs_path_elem.lower() == 'wfs':
                wms_path_elements.append('wms')
            else:
                wms_path_elements.append(wfs_path_elem)
        wms_path = '/'.join(wms_path_elements)

        wms_url = QUrl(self.wfs_url)
        wms_url.setPath(wms_path)

        result.append(wms_url)

        wms_url = QUrl(self.wfs_url)
        wms_url.setPath('een/andere/wms')
        result.append(wms_url)


        return result



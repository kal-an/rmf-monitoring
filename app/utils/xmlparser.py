from xml.etree import ElementTree as ET


class XMLParser:

    def __init__(self, xml_string):
        self.root = ET.fromstring(xml_string)
        self.serialized_xml = {}

    def get_serialized_xml(self):
        resource_list = self.get_tag_resource(self.root)
        metric_list = self.get_tag_metric_list(self.root)
        report = self.get_tag_report(self.root)
        message = self.get_tag_message(self.root)
        time_data = self.get_tag_time_data(self.root)

        self.update_serialized_xml(message, resource_list, metric_list, report, time_data)
        return self.serialized_xml

    def update_serialized_xml(self, *tags):
        for tag in tags:
            # if len(list(tag.values()).pop()) != 0:  # не обновлять словарь если он пустой
            if len(tag) != 0:
                self.serialized_xml.update(tag)

    def get_tag_resource(self, root):
        resources_list = []
        for resource in root.iter('resource'):
            d = {}
            if resource.find('reslabelurl') is not None:
                for el in resource:
                    if el.tag == 'reslabel':
                        el.text = el.text.lstrip(',')
                    if el.tag not in ['icon', 'attributes']:
                        d[el.tag] = el.text
                resources_list.append(d)
        return {'resources': resources_list}

    def get_tag_metric_list(self, root):
        metric_list = []
        for metric in root.iter('metric'):
            d = {}
            if metric.find('description') is not None:
                d['id'] = metric.attrib['id']
                for el in metric:
                    if el.text is None:
                        el.text = ''
                    el.text = el.text.strip()
                    d[el.tag] = el.text
                metric_list.append(d)
        metric_list = sorted(metric_list, key=lambda i: i['description'])
        return {'listmetrics': metric_list}

    def get_tag_report(self, root):
        row_list = []
        # row_list = [ {'refno': id, 'col_list': [{'col': text}, {'col': text}....]}, {  ...  } ]
        for row in root.iter('row'):
            d = {}
            col_list = []
            d['refno'] = row.attrib['refno']
            for el in row:
                if el.text is None:
                    el.text = '-'
                col_list.append({el.tag: el.text})
            d['columns'] = col_list
            row_list.append(d)
        return {'perform': row_list}

    def get_tag_time_data(self, root):
        time_data = {}
        for elements in root.iter('time-data'):
            for element in elements:
                time_data[element.tag] = element.text
        return {'time-data': time_data}

    def get_tag_message(self, root):
        message = {}
        for elements in root.iter('message'):
            message['id'] = elements.attrib['id']
            for el in elements:
                message[el.tag] = el.text
        return {'message': message}

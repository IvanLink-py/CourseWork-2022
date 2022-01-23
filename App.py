import configparser

from VideoSetter import VideoSetter

class App:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read("config.ini")
        self._video = VideoSetter(self.config)
        self.data = {}

    def run(self):
        self._video.set()
        self.data = self._video.scan()
        self.export()

    def export(self):
        exportFormat = self.config['Export']['exportFormat']

        if exportFormat == 'RawTXT':
            self.ExportAsRawTXT()
        elif exportFormat == 'PythonList':
            self.ExportAsPythonList()
        elif exportFormat == 'PythonDict':
            self.ExportAsPythonDict()
        elif exportFormat == 'JSON':
            self.ExportAsJSON()
        elif exportFormat == 'NumpyArray':
            self.ExportAsNumpyArray()
        elif exportFormat == 'Excel':
            self.ExportAsExcel()
        elif exportFormat == 'Graph':
            self.ExportAsGraph()

    def ExportAsRawTXT(self):
        with open(self.config['Export']['exportFileName']+'.txt', 'w', encoding='utf-8') as file:
            file.write('\n'.join(map(str, self.data.values())))

    def ExportAsPythonList(self):
        with open(self.config['Export']['exportFileName']+'.txt', 'w', encoding='utf-8') as file:
            file.write(str(list(self.data.values())))

    def ExportAsPythonDict(self):
        with open(self.config['Export']['exportFileName']+'.txt', 'w', encoding='utf-8') as file:
            file.write(str(self.data))

    def ExportAsJSON(self):
        import json
        with open(self.config['Export']['exportFileName']+'.json', 'w', encoding='utf-8') as file:
            file.write(json.dumps(self.data))

    def ExportAsNumpyArray(self):
        import numpy as np
        np.save(self.config['Export']['exportFileName'], np.array(list(self.data.values())))

    def ExportAsExcel(self):
        import xlsxwriter

        workbook = xlsxwriter.Workbook(self.config['Export']['exportFileName']+'.xlsx')
        worksheet = workbook.add_worksheet()

        worksheet.write(0, 1, 'Секунда')
        worksheet.write(0, 2, 'Значение')

        for i, sec in enumerate(self.data):
            worksheet.write(i+1, 1, sec)
            worksheet.write(i+1, 2, self.data[sec])

        workbook.close()

    def ExportAsGraph(self):
        import matplotlib.pyplot as plt
        names = list(self.data.keys())
        values = list(self.data.values())

        fig, ax = plt.subplots()
        ax.plot(names, values)
        plt.show()

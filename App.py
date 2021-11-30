from VideoSetter import VideoSetter, Scanner

class App:
    def __init__(self):
        self._video = VideoSetter('Experiments/E-1/video.mp4')

    def run(self):
        self._video.set()
        data = self._video.export()
        self.scaner = Scanner(data)
        self.scaner.scan()

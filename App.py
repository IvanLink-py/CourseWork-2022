from VideoSetter import VideoSetter

class App:
    def __init__(self):
        self._video = VideoSetter('Experiments/E-Test/video.mp4')

    def run(self):
        self._video.set()
        self._video.scan()

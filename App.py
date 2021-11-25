from Video import Video

class App:
    def __init__(self):
        self._video = Video('Experiments/E-1/video.mp4')

    def run(self):
        self._video.crop()
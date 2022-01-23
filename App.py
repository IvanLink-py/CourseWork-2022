from VideoSetter import VideoSetter
import configparser

class App:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read("config.ini")
        self._video = VideoSetter(self.config)

    def run(self):
        self._video.set()
        self._video.scan()

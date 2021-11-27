import cv2
import numpy as np


class VideoSetter:

    def __init__(self, path):
        self.path = path
        self._capture = cv2.VideoCapture(path)
        self.fps = self._capture.get(5)
        self.cropping = []
        self.croppingArea = [(), ()]

        self.isCropping = False
        self.isRotating = False
        self.isPlacement = False

        self.scaleF = 1
        self.rotate = 0
        self.d1 = Digit(self)

        _, self.source_img = self._capture.read()
        self.frame = self.source_img.copy()
        self.ratio = self.frame.shape[0] / self.frame.shape[1]

    def set(self):
        cv2.setMouseCallback('Frame', self.onClick)
        self.crop()
        self.rotating()
        self.placement()

    def _scale(self):
        sizeY, sizeX, _ = self.frame.shape
        if sizeX > 900 or sizeY > 900:
            self.frame = cv2.resize(self.frame, (round(900 / self.ratio), 900))
            self.scaleF = 900 / sizeY

        else:
            self.scaleF = 1

    def _rotate(self):
        if 1 <= self.rotate <= 3:
            self.frame = np.rot90(self.frame, self.rotate)

    def _drawSegments(self):
        self.d1.draw()

    def crop(self):
        self.isCropping = True
        while True:
            self.showFrame()
            cv2.setWindowTitle('Frame', 'Cropping')
            key = cv2.waitKey()
            if key == 13:
                break
            elif key == -1:
                quit()

        self.isCropping = False

    def rotating(self):
        self.isRotating = True
        while True:
            self.showFrame()
            cv2.setWindowTitle('Frame', 'Rotating')
            key = cv2.waitKey()
            if key == 13:
                break
            elif ord('r') == key:
                self.rotate = (self.rotate + 1) % 4
            elif key == -1:
                quit()

        self.isRotating = False

    def placement(self):
        self.isPlacement = True

        while True:
            self.showFrame()
            cv2.setWindowTitle('Frame', 'Placement')
            key = cv2.waitKey()
            if key == -1:
                quit()

        self.isPlacement = False

    def showFrame(self):
        self.frame = self.source_img.copy()
        for crop in self.cropping:
            self.frame = self.frame[crop[0][1]:crop[1][1], crop[0][0]:crop[1][0]]

        self._scale()
        self._rotate()
        self._drawSegments()
        cv2.imshow('Frame', self.frame)

    def onClick(self, event, posX, posY, flags, param):
        pos = (round(posX / self.scaleF), round(posY / self.scaleF))
        if self.isCropping:
            if event == 1:
                self.croppingArea[0] = pos
            elif event == 4:
                self.croppingArea[1] = pos
                self.cropping.append(tuple(self.croppingArea))
                self.croppingArea = [(), ()]
                self.showFrame()
        elif self.isPlacement:
            if event == 1:
                self.d1.place(pos)
                self.showFrame()


class Segment:
    size = 7

    def __init__(self, digit, position):
        self.digit = digit
        self.pos = position

    def scan(self, frame):
        return False

    def getColor(self, frame):
        print(frame[self.pos[1], self.pos[0]])
        return frame[self.pos[1], self.pos[0]].tolist()

    def draw(self, frame):
        cv2.rectangle(frame,
                      (self.pos[0] - self.size, self.pos[1] - self.size),
                      (self.pos[0] + self.size, self.pos[1] + self.size),
                      self.getColor(frame),
                      -1)
        cv2.rectangle(frame,
                      (self.pos[0] - self.size, self.pos[1] - self.size),
                      (self.pos[0] + self.size, self.pos[1] + self.size),
                      (0,0,0),
                      1)


class Digit:
    def __init__(self, video):
        self.segments = []
        self.video = video

    def place(self, position):
        new_seg = Segment(self, position)
        self.segments.append(new_seg)

    def scan(self, frame):
        data = [seg.scan(frame) for seg in self.segments]

    def draw(self):
        [seg.draw(self.video.frame) for seg in self.segments]

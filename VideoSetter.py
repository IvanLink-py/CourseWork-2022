from dataclasses import dataclass
from enum import Enum, auto

import cv2
import numpy as np


class VideoSetter:
    def __init__(self, path):
        self.path = path
        self._capture = cv2.VideoCapture(path)
        # self._capture.set(1, 500)
        self.fps = self._capture.get(5)
        self.cropping = []
        self.croppingArea = [(), ()]

        self.isCropping = False
        self.isRotating = False
        self.isPlacement = False
        self.isNaming = False

        self.scaleF = 1
        self.rotate = 0
        self.digits = []
        self.segmentsHistory = []
        self.nameHistory = []

        _, self.source_img = self._capture.read()
        self.frame = self.source_img.copy()

        self.sizeY, self.sizeX, _ = self.frame.shape
        self.originalSize = (self.sizeX, self.sizeY)

        self.ratio = self.sizeY / self.sizeX

    def set(self):
        self.showFrame()
        cv2.setMouseCallback('Frame', self.onClick)

        self.transform()
        self.placement()
        self.naming()

        cv2.destroyWindow('Frame')

    def _scale(self, frame):
        self.sizeY, self.sizeX, _ = frame.shape
        self.ratio = self.sizeY / self.sizeX
        if self.sizeX > 900 or self.sizeY > 900:
            frame = cv2.resize(frame, (round(900 / self.ratio), 900))
            self.scaleF = 900 / self.sizeY
        else:
            self.scaleF = 1
        return frame

    def _rotate(self, frame):
        return np.ascontiguousarray(np.rot90(frame, self.rotate), dtype=np.uint8)

    def _drawSegments(self, frame):
        [d.draw(frame) for d in self.digits]

    def transform(self):
        self.isCropping = True
        while True:
            self.showFrame()
            cv2.setWindowTitle('Frame', 'Transform')
            key = cv2.waitKey()
            if key == 13:
                break
            elif key == 8:
                self.cropping.pop(-1)
                self.showFrame()

            elif ord('r') == key:
                self.rotate = (self.rotate + 1) % 4

            elif key == -1:
                quit()
            else:
                print(key)

        self.isCropping = False

    def placement(self):
        self.isPlacement = True

        while True:
            self.showFrame()
            cv2.setWindowTitle('Frame', 'Placement')
            key = cv2.waitKey()
            if key == 13:
                break
            elif key == -1:
                quit()
            elif key == 8:
                self.removeLast()
            else:
                print(key)

        self.isPlacement = False

    def naming(self):
        self.isNaming = True
        self.namer = SegmentName.getName()
        self.noNamedDigits = self.digits.copy()

        self.showFrame()
        cv2.setWindowTitle('Frame', 'Naming')
        while True:
            key = cv2.waitKey()
            if key == 8:
                self.nameHistory[-1].name = None
                self.nameHistory.pop(-1)
                self.showFrame()
            elif key == 13 and self.allNamed():
                break

        self.isNaming = False

    @staticmethod
    def correctRect(pos1, pos2):
        _pos1 = (pos1[0] if pos1[0] < pos2[0] else pos2[0]), (pos1[1] if pos1[1] < pos2[1] else pos2[1])
        _pos2 = (pos1[0] if pos1[0] > pos2[0] else pos2[0]), (pos1[1] if pos1[1] > pos2[1] else pos2[1])
        return _pos1, _pos2

    def showFrame(self):
        self.frame = self.source_img.copy()
        for crop in self.cropping:
            self.frame = self.frame[crop[0][1]:crop[1][1], crop[0][0]:crop[1][0]]

        self.frame = self._scale(self.frame)
        self.frame = self._rotate(self.frame)
        self._drawSegments(self.frame)

        cv2.imshow('Frame', self.frame)

    def convertCords(self, pos):

        # Координаты с экрана → Кординаты исходного кадра

        for crop in self.cropping:
            pos = (pos[0] + crop[0][0], pos[1] + crop[0][1])

        pos = (round(pos[0] / self.scaleF), round(pos[1] / self.scaleF))

        if self.rotate == 0:
            pos = (pos[0], pos[1])
        elif self.rotate == 1:
            pos = (self.originalSize[0] - pos[1], pos[0])
        elif self.rotate == 2:
            pos = (self.originalSize[0] - pos[0], self.originalSize[1] - pos[1])
        elif self.rotate == 3:
            pos = (pos[1], self.originalSize[1] - pos[0])
        else:
            raise IndexError

        return pos

    def showedCords(self, pos):

        # Кординаты исходного кадра → Координаты на экране

        if self.rotate == 0:
            pos = (pos[0], pos[1])
        elif self.rotate == 1:
            pos = (pos[1], self.originalSize[0] - pos[0])
        elif self.rotate == 2:
            pos = (self.originalSize[0] - pos[0], self.originalSize[1] - pos[1])
        elif self.rotate == 3:
            pos = (self.originalSize[1] - pos[1], pos[0])

        else:
            raise IndexError

        pos = (round(pos[0] * self.scaleF), round(pos[1] * self.scaleF))

        for crop in self.cropping:
            pos = (pos[0] - crop[0][0], pos[1] - crop[0][1])

        return pos

    def onClick(self, event, posX, posY, flags, param):
        pos = self.convertCords((posX, posY))
        if self.isCropping:
            if event == 1:
                self.croppingArea[0] = pos
            elif event == 4:
                self.croppingArea[1] = pos
                self.cropping.append(self.correctRect(*self.croppingArea))
                self.croppingArea = [(), ()]
                self.showFrame()
        elif self.isPlacement:
            if event == 1:
                self.setSegment(pos)
                self.showFrame()

        elif self.isNaming:
            if event == 1:

                noNames = []

                for d in self.noNamedDigits:
                    if d.isNamed():
                        d.isNaming = False
                        continue
                    noNames = [s for s in d.segments if s.name is None]
                    d.isNaming = True
                    break

                if noNames:
                    seg = min(noNames, key=lambda p: (p.pos[0] - pos[0]) ** 2 + (p.pos[1] - pos[1]) ** 2)
                    seg.name = self.namer.__next__()
                    self.nameHistory.append(seg)

                self.showFrame()

    def setSegment(self, pos):
        for seg in self.segmentsHistory:
            if seg.getDistance(pos) < 100:
                print('Пошёл нах*й')
                break
        else:
            if not self.digits:
                self.digits.append(Digit(self))
            for d in self.digits:
                if d.isFull():
                    continue
                d.place(pos)
                break
            else:
                self.digits.append(Digit(self))
                self.digits[-1].place(pos)

    def removeLast(self):
        if self.segmentsHistory:
            seg = self.segmentsHistory[-1]
            digit = seg.digit
            digit.segments.remove(seg)
            self.segmentsHistory.remove(seg)
            if digit.isEmpty():
                self.digits.remove(digit)
        self.showFrame()

    def allNamed(self):
        return all([d.isNamed() for d in self.digits])

    def export(self):
        return VideoData(0, int(self.fps), self.digits, self._capture, self)


class Scanner:
    def __init__(self, videoData):
        self.startFrame = videoData.startFrame
        self.step = videoData.step
        self.digits = videoData.digits
        self.capture = videoData.capture
        self.setter = videoData.setter

        self.capture.set(1, self.startFrame)

        _, self.currentFrame = self.capture.read()
        self.FrameN = self.startFrame

        [dig.sort() for dig in self.digits]

    def nextFrame(self):
        self.capture.set(1, round(self.step * self.FrameN + self.startFrame))
        self.FrameN += 1
        ret, frame = self.capture.read()
        if ret:
            self.currentFrame = frame.copy()
            frame = self.setter._scale(frame)
            self.setter._drawSegments(frame)
            cv2.imshow('debug', frame)

            cv2.waitKey(1)
            return False
        else:
            return True

    def scan(self):
        data = {}
        while True:
            curr = ''.join(map(str, [d.scan(self.currentFrame) for d in self.digits]))
            data[self.FrameN] = curr
            q = self.nextFrame()
            if q:
                from pprint import pprint
                pprint(data)
                with open('data.txt', 'w', encoding='utf-8') as file:
                    file.write(str(data))
                quit()


class Segment:
    size = 7

    onColor = np.array([194, 209, 191])
    offColor = np.array([65, 56, 40])

    def __init__(self, digit, position, setter):
        self.digit = digit
        self.pos = position
        self.videoSetter = setter
        self.name = None

    def scan(self, frame):
        color = self.getColor(frame, toList=False)

        offDif = np.sum(np.abs(self.offColor - color))
        onDif = np.sum(np.abs(self.onColor - color))

        return onDif < offDif

    def getColor(self, frame, pos=None, toList=True):
        if pos is None:
            pos = self.pos
        return frame[pos[1], pos[0]].tolist() if toList else frame[pos[1], pos[0]]

    def draw(self, frame):
        pos = self.videoSetter.showedCords(self.pos)
        cv2.rectangle(frame,
                      (pos[0] - self.size, pos[1] - self.size),
                      (pos[0] + self.size, pos[1] + self.size),
                      self.getColor(frame, pos),
                      -1)

        color = 0, 0, 0
        if self.name is not None:
            color = 0, 255, 0
        elif self.digit.isNaming:
            color = 255, 0, 0

        cv2.rectangle(frame,
                      (pos[0] - self.size, pos[1] - self.size),
                      (pos[0] + self.size, pos[1] + self.size),
                      color,
                      1)

        cv2.rectangle(frame,
                      (pos[0] - self.size -1, pos[1] - self.size-1),
                      (pos[0] + self.size+1, pos[1] + self.size+1),
                      (255,255,255),
                      1)

        # print(self.getColor(frame, pos))

    def getDistance(self, pos):
        return (pos[0] - self.pos[0])**2 + (pos[1] - self.pos[1])**2


class Digit:
    def __init__(self, video):
        self.segments = []
        self.video = video
        self.isNaming = False
        self.sorted = {}
        self._isSorted = False

    def sort(self):
        for segment in self.segments:
            self.sorted[segment.name] = segment
            if segment.name is None:
                raise KeyError()
        if len(self.sorted) != 7:
            raise KeyError(len(self.sorted))
        self._isSorted = True

    def place(self, position):
        new_seg = Segment(self, position, self.video)
        self.segments.append(new_seg)
        self.video.segmentsHistory.append(new_seg)

    def scan(self, frame):
        data = {}
        for seg in self.segments:
            data[seg.name] = seg.scan(frame)

        return self.interpret(data)

    @staticmethod
    def interpret(data):
        return Interrupt.find(tuple(data.values()))

    def draw(self, frame):
        [seg.draw(frame) for seg in self.segments]

    def removeLast(self):
        self.segments.pop(-1)

    def isFull(self):
        return len(self.segments) >= 7

    def isNamed(self):
        return all([s.name is not None for s in self.segments])

    def isEmpty(self):
        return not self.segments


@dataclass
class VideoData:
    startFrame: int
    step: int
    digits: list
    capture: cv2.VideoCapture

    setter: VideoSetter


class SegmentName(Enum):
    U = auto()
    UL = auto()
    UR = auto()
    M = auto()
    BL = auto()
    BR = auto()
    B = auto()

    @staticmethod
    def getName():
        while True:
            for name in SegmentName:
                yield name


class Interrupt:
    _0 = True, True, True, False, True, True, True
    _1 = False, False, True, False, False, True, False
    _2 = True, False, True, True, True, False, True
    _3 = True, False, True, True, False, True, True
    _4 = False, True, True, True, False, True, False
    _5 = True, True, False, True, False, True, True
    _6 = True, True, False, True, True, True, True
    _7 = True, False, True, False, False, True, False
    _8 = True, True, True, True, True, True, True
    _9 = True, True, True, True, False, True, True

    digits = [_0, _1, _2, _3, _4, _5, _6, _7, _8, _9, ]
    dataToN = {_0: 0, _1: 1, _2: 2, _3: 3, _4: 4, _5: 5, _6: 6, _7: 7, _8: 8, _9: 9}

    @staticmethod
    def find(data):
        for d in Interrupt.digits:
            if d == data:
                print('!'*20)
                return Interrupt.dataToN[d]
        else:
            print(data)
            return 0

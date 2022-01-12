from enum import Enum, auto

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
        self.isNaming = False

        self.scaleF = 1
        self.rotate = 0
        self.digits = []
        self.segmentsHistory = []
        self.nameHistory = []

        self.currentFrameScan = 5
        self.ScanFrame = self.fps

        _, self.source_img = self._capture.read()
        self.frame = self.source_img.copy()

        self.sizeY, self.sizeX, _ = self.frame.shape
        self.originalSize = (self.sizeX, self.sizeY)

        self.ratio = self.sizeY / self.sizeX

    def set(self):
        self.showFrame()
        cv2.setMouseCallback('Frame', self.onClick)

        self.crop()
        self.rotating()
        self.placement()
        self.naming()

        cv2.destroyWindow('Frame')

    def scan(self):

        [dig.sort() for dig in self.digits]

        while True:
            self._capture.set(1, round(self.ScanFrame * self.currentFrameScan, 1))
            ret, self.source_img = self._capture.read()
            if ret:
                self.currentFrameScan += 1

                scan_data = [d.scan(self.source_img) for d in self.digits]

                for i, res in enumerate(scan_data):
                    if not res[0]:
                        self.digits[i].is_broken = True

                print(f'{self.ScanFrame * self.currentFrameScan} - ' + ''.join([str(i[1]) for i in scan_data]))

                self.showFrame()

                if round(self.ScanFrame * (self.currentFrameScan + 1), 1) > self._capture.get(cv2.CAP_PROP_FRAME_COUNT):
                    print('Done')
                    break

            else:
                raise cv2.error

    def _scale(self):
        self.sizeY, self.sizeX, _ = self.frame.shape
        self.ratio = self.sizeY / self.sizeX
        if self.sizeX > 900 or self.sizeY > 900:
            self.frame = cv2.resize(self.frame, (round(900 / self.ratio), 900))
            self.scaleF = 900 / self.sizeY

        else:
            self.scaleF = 1

    def _rotate(self):
        self.frame = np.ascontiguousarray(np.rot90(self.frame, self.rotate), dtype=np.uint8)

    def _drawSegments(self):
        [d.draw() for d in self.digits]

    def crop(self):
        self.isCropping = True
        while True:
            self.showFrame()
            cv2.setWindowTitle('Frame', 'Cropping')
            key = cv2.waitKey()
            if key == 13:
                break
            elif key == 8:
                self.cropping.pop(-1)
                self.showFrame()
            elif key == -1:
                quit()
            else:
                print(key)

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
            else:
                print(key)

        self.isRotating = False

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

    def showFrame(self):
        self.frame = self.source_img.copy()
        for crop in self.cropping:
            self.frame = self.frame[crop[0][1]:crop[1][1], crop[0][0]:crop[1][0]]

        self._scale()
        self._rotate()
        self._drawSegments()

        cv2.imshow('Frame', self.frame)

    def convertCords(self, pos):

        # Координаты с экрана → Кординаты исходного кадра
        pos = (round(pos[0] / self.scaleF), round(pos[1] / self.scaleF))

        for crop in self.cropping:
            pos = (pos[0] + crop[0][0], pos[1] + crop[0][1])

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

        for crop in self.cropping:
            pos = (pos[0] - crop[0][0], pos[1] - crop[0][1])

        pos = (round(pos[0] * self.scaleF), round(pos[1] * self.scaleF))

        return pos

    def onClick(self, event, posX, posY, flags, param):
        pos = self.convertCords((posX, posY))
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


class Scanner:
    def __init__(self, videoData):
        self.startFrame = videoData.startFrame
        self.step = videoData.step
        self.digits = videoData.digits
        self.capture = videoData.capture

        _, self.currentFrame = self.capture.read()
        self.FrameN = self.startFrame

    def nextFrame(self):
        self.capture.set(1, round(self.step * self.FrameN, 1))
        self.FrameN += 1

    def scan(self):
        while True:

            self.nextFrame()
            if self.FrameN > 100:
                print('end')
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
        if self.digit.is_broken:
            color = 0, 255, 255
        elif self.name is not None:
            color = 0, 255, 0
        elif self.digit.isNaming:
            color = 255, 0, 0

        cv2.rectangle(frame,
                      (pos[0] - self.size, pos[1] - self.size),
                      (pos[0] + self.size, pos[1] + self.size),
                      color,
                      1)

        # print(self.getColor(frame, pos))


class Digit:
    is_broken = False

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
            raise KeyError
        self._isSorted = True

    def place(self, position):
        new_seg = Segment(self, position, self.video)
        self.segments.append(new_seg)
        self.video.segmentsHistory.append(new_seg)

    def scan(self, frame):
        data = {}
        for seg in self.segments:
            data[seg.name] = seg.scan(frame)

        self.is_broken = False

        return self.interpret(data)

    @staticmethod
    def interpret(data):
        return Interrupt.find(tuple(data.keys()))

    def draw(self):
        [seg.draw(self.video.frame) for seg in self.segments]

    def removeLast(self):
        self.segments.pop(-1)

    def isFull(self):
        return len(self.segments) >= 7

    def isNamed(self):
        return all([s.name is not None for s in self.segments])

    def isEmpty(self):
        return not self.segments


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
    dataSet = {0: (True, True, True, False, True, True, True),
               1: (False, False, True, False, False, True, False),
               2: (True, False, True, True, True, False, True),
               3: (True, False, True, True, False, True, True),
               4: (False, True, True, True, False, True, False),
               5: (True, True, False, True, False, True, True),
               6: (True, True, False, True, True, True, True),
               7: (True, False, True, False, False, True, False),
               8: (True, True, True, True, True, True, True),
               9: (True, True, True, True, False, True, True)}

    @staticmethod
    def find(data):
        if data in list(Interrupt.dataSet.values()):
            return True, Interrupt.dataSet[data]
        else:
            print('Жопа')
            return False, 0

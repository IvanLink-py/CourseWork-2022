import cv2

class Video:
    def __init__(self, path):
        self.path = path
        self._capture = cv2.VideoCapture(path)
        self.fps = self._capture.get(5)
        self.cropping = []
        self.croppingArea = [(), ()]
        self.isCropping = False
        
        self.scaleF = 1
        
        _, self.source_img = self._capture.read()
        self.frame = self.source_img.copy()
        self.ratio = self.frame.shape[0] / self.frame.shape[1]

    def _scale(self):
        sizeY, sizeX, _ = self.frame.shape
        if sizeX > 900 or sizeY > 900:
            self.frame = cv2.resize(self.frame, (round(900/self.ratio), 900))
            self.scaleF = 900 / sizeY

        else:
            self.scaleF = 1

    def crop(self):
        self.isCropping = True

        self.showFrame()
        cv2.setMouseCallback('Frame', self.onClick)
        cv2.setWindowTitle('Frame', 'Cropping')
        cv2.waitKey()

        self.isCropping = False

    def showFrame(self):
        self.frame = self.source_img.copy()
        for crop in self.cropping:
            self.frame = self.frame[crop[0][1]:crop[1][1], crop[0][0]:crop[1][0]]

        self._scale()
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
        
import cv2

video = cv2.VideoCapture('Experiments/E-1/video.mp4')

fps = video.get(5)
print("Frame Rate :",fps)

print("Frame count : ", video.get(7))

selection = [(), ()]
scaleF = 1

def onClick(event, posX, posY, flags, param):
	global selection, frame

	pos = (round(posX*scaleF), round(posY*scaleF))
	if event == 1:
		selection[0] = pos
	elif event == 4:
		selection[1] = pos
		print(selection)
		if scaleF != 1:
			frame = frame[selection[0][1]:selection[1][1], selection[0][0]:selection[1][0]]
		try:
			cv2.imshow('Frame', frame)
		except:
			frame = source_img
			cv2.imshow('Frame', frame)



def cropping():
	ret, frame = video.read()
	source_img = frame.copy()
	while True:
		cv2.imshow('Frame', frame)
		cv2.setMouseCallback('Frame', onClick)
		cv2.setWindowTitle('Frame', 'Cropping')
		key = cv2.waitKey()
		if ord('r') == key:
			frame = source_img.copy()
		elif key == 13:
			break
		elif key == -1:
			quit()


# i = 0
# while video.isOpened():
#
# 	video.set(1, round(fps*i, 1))
# 	ret, frame = video.read()
# 	i += 1
# 	if ret:
# 		cv2.imshow('Frame',frame)
# 		k = cv2.waitKey(20)
# 		if k == 113:
# 			break
# 	else:
# 		break


# video.release()
# cv2.destroyAllWindows()
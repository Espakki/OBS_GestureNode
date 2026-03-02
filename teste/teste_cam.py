import cv2
import time

inicio = time.time()

print("Abrindo câmera...")
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

print("Tempo para abrir:", time.time() - inicio)

ret, frame = cap.read()
print("Tempo total:", time.time() - inicio)

cap.release()
import cv2
import pyvirtualcam


class CameraManager:
	def __init__(
		self,
		camera_index=0,
		width=1280,
		height=720,
		fps=60,
		enable_virtual_camera=True,
		virtual_camera_device=None,
	):
		self.camera_index = camera_index
		self.width = width
		self.height = height
		self.fps = fps
		self.enable_virtual_camera = enable_virtual_camera
		self.virtual_camera_device = virtual_camera_device

		self.capture = None
		self.virtual_camera = None

	def iniciar(self):
		self.capture = cv2.VideoCapture(self.camera_index)

		self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
		self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
		self.capture.set(cv2.CAP_PROP_FPS, self.fps)

		if self.enable_virtual_camera:
			self.virtual_camera = pyvirtualcam.Camera(
				width=self.width,
				height=self.height,
				fps=self.fps,
				device=self.virtual_camera_device,
			)
			print(f"Câmera virtual ativa: {self.virtual_camera.device}")

	def ler_frame(self):
		if not self.capture:
			return False, None

		ok, frame = self.capture.read()
		if not ok:
			return False, None

		frame = cv2.flip(frame, 1)
		return True, frame

	def enviar_para_virtual(self, frame_bgr):
		if not self.virtual_camera:
			return

		frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
		self.virtual_camera.send(frame_rgb)
		self.virtual_camera.sleep_until_next_frame()

	def encerrar(self):
		if self.capture:
			self.capture.release()

		if self.virtual_camera:
			self.virtual_camera.close()

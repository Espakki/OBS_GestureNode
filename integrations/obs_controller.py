import obsws_python as obs
import time

class OBSController:
    def __init__(self, host="localhost", port=4455, password="R6n3NNtb2NbyTFjH"):
        print("Iniciando conexão OBS...")
        inicio = time.time()

        self.cliente = obs.ReqClient(
            host=host,
            port=port,
            password=password,
            timeout=5  # 👈 MUITO IMPORTANTE
        )

        print("Conectado ao OBS!")
        print("Tempo OBS:", time.time() - inicio)

    def listar_cenas(self):
        cenas = self.cliente.get_scene_list()
        return [scene["sceneName"] for scene in cenas.scenes]

    def trocar_cena(self, nome_cena):
        self.cliente.set_current_program_scene(nome_cena)
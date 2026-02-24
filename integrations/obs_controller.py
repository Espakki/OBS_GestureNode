import obsws_python as obs

class OBSController:
    def __init__(self, host="localhost", port=4455, password="R6n3NNtb2NbyTFjH"):
        self.cliente = obs.ReqClient(host=host, port=port, password=password)

    def listar_cenas(self):
        cenas = self.cliente.get_scene_list()
        return [scene["sceneName"] for scene in cenas.scenes]

    def trocar_cena(self, nome_cena):
        self.cliente.set_current_program_scene(nome_cena)
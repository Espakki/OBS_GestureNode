class ActionManager:
    def __init__(self, obs_controller):
        self.obs = obs_controller

    def executar(self, tipo, valor=None):
        if tipo == "trocar_cena":
            self.obs.trocar_cena(valor)

        elif tipo == "iniciar_live":
            self.obs.cliente.start_stream()

        elif tipo == "parar_live":
            self.obs.cliente.stop_stream()

        else:
            print("Ação desconhecida:", tipo)
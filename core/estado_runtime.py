"""O que está acontecendo agora — como estado tipado, não como frase. Ver D-48.

Antes disto, a UI descobria o estado do sistema **lendo texto em português**:

    if "falha ao iniciar câmera" in texto.lower():
    obs_status_text = self.obs_status_label.text().lower()

O segundo é o pior: o painel de saúde lia o estado de dentro do texto de um label, ou
seja, o widget era a fonte da verdade. Renomear uma mensagem quebrava o painel em
silêncio, e nenhum teste pegaria porque a mensagem "continua certa" — só que ninguém mais
a reconhece.

Aqui o estado é um enum. A mensagem legível continua existindo e continua indo para o log,
mas ela passa a ser **consequência** do estado, não o meio de transporte dele.
"""

from dataclasses import dataclass, replace
from enum import Enum


class EstadoCamera(Enum):
    PARADA = "parada"
    RODANDO = "rodando"
    LIMITADA = "limitada"  # abriu, mas não no modo pedido — ver D-32
    FALHOU = "falhou"


class EstadoOBS(Enum):
    DESATIVADO = "desativado"  # modo teste não usa OBS (D-16)
    NAO_TESTADO = "nao_testado"
    CONECTANDO = "conectando"
    CONECTADO = "conectado"
    FALHOU = "falhou"


class EstadoEngine(Enum):
    PARADA = "parada"
    RODANDO = "rodando"
    PARANDO = "parando"


@dataclass(frozen=True)
class Saude:
    """Retrato do runtime num instante.

    Imutável de propósito: quem recebe não consegue alterar o estado de quem enviou. Para
    derivar um novo, use `com()`.
    """

    engine: EstadoEngine = EstadoEngine.PARADA
    camera: EstadoCamera = EstadoCamera.PARADA
    obs: EstadoOBS = EstadoOBS.NAO_TESTADO
    detalhe_camera: str = ""
    detalhe_obs: str = ""

    def com(self, **campos):
        return replace(self, **campos)


# Cada evento traz o estado que ele implica. A engine emite o evento; quem escuta decide
# o que fazer — o painel pinta, o log escreve, e nenhum dos dois interpreta string.
class Evento(Enum):
    ENGINE_INICIADA = "engine_iniciada"
    ENGINE_PARADA = "engine_parada"
    CAMERA_INICIADA = "camera_iniciada"
    CAMERA_LIMITADA = "camera_limitada"
    CAMERA_FALHOU = "camera_falhou"
    OBS_CONECTADO = "obs_conectado"
    OBS_FALHOU = "obs_falhou"
    MODO_TESTE = "modo_teste"


def aplicar(saude, evento, detalhe=""):
    """Transição pura: `(saúde, evento) → nova saúde`.

    Função e não método porque é a regra do sistema, não do dado — e assim ela é testável
    sem construir nada.
    """
    if evento is Evento.ENGINE_INICIADA:
        return saude.com(engine=EstadoEngine.RODANDO)

    if evento is Evento.ENGINE_PARADA:
        # A câmera cai junto com a engine: ela não sobrevive à parada, e deixar o painel
        # dizendo "rodando" depois do stop era exatamente o tipo de mentira que o parsing
        # de string produzia.
        return saude.com(
            engine=EstadoEngine.PARADA,
            camera=EstadoCamera.PARADA,
            detalhe_camera="",
        )

    if evento is Evento.CAMERA_INICIADA:
        return saude.com(camera=EstadoCamera.RODANDO, detalhe_camera=detalhe)

    if evento is Evento.CAMERA_LIMITADA:
        return saude.com(camera=EstadoCamera.LIMITADA, detalhe_camera=detalhe)

    if evento is Evento.CAMERA_FALHOU:
        return saude.com(camera=EstadoCamera.FALHOU, detalhe_camera=detalhe)

    if evento is Evento.OBS_CONECTADO:
        return saude.com(obs=EstadoOBS.CONECTADO, detalhe_obs=detalhe)

    if evento is Evento.OBS_FALHOU:
        return saude.com(obs=EstadoOBS.FALHOU, detalhe_obs=detalhe)

    if evento is Evento.MODO_TESTE:
        return saude.com(obs=EstadoOBS.DESATIVADO, detalhe_obs="")

    return saude

"""Recolhe os textos de licença das dependências para dentro do pacote. Ver D-51.

    .venv\\Scripts\\python.exe ferramentas\\coletar_licencas.py

**Por que coletar e não escrever à mão.** O texto de uma licença tem de ir *verbatim*, e uma
cópia transcrita envelhece: sobe a versão de um pacote, muda a licença, e o arquivo continua
afirmando a antiga. Todo pacote instalado já traz o próprio texto no `dist-info` — a fonte
correta é essa, e ela se atualiza junto com o `pip install`.

**Por que isso precisa existir.** O app é GPL-3.0, e a GPL exige que uma cópia da licença
acompanhe o binário. O PySide6/Qt é LGPL-3.0, que exige aviso de uso e o texto junto. "Está
no GitHub" não cumpre: quem baixou o `.exe` pode nunca ter visto o repositório.

O que **não** entra: README, CHANGELOG, `.planning/`. Isso é contexto, e o lugar dele é o
repositório — não a máquina de quem só quer usar o programa.
"""

import importlib.metadata as metadata
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "licencas"

# As dependências declaradas, mais as transitivas que de fato são distribuídas no bundle.
# Lista explícita e não "tudo que está no venv": o venv tem ferramenta de desenvolvimento
# (pytest e companhia) que não é distribuída, e declarar licença de quem não vai junto é
# ruído que dá a impressão errada do que o pacote contém.
PACOTES = (
    "PySide6",
    "shiboken6",
    "mediapipe",
    "opencv-python",
    "opencv-contrib-python",
    "numpy",
    "av",
    "obsws-python",
    "websocket-client",
    "keyboard",
    "pygrabber",
    "comtypes",
    "protobuf",
    "attrs",
    "pyvirtualcam",
)

CABECALHO = """# Licenças de terceiros

O OBS GestureNode é distribuído sob a **GPL-3.0** (veja `LICENSE` na raiz).

Este pacote embute as bibliotecas abaixo. Os textos completos estão nesta mesma pasta, um
arquivo por biblioteca, copiados sem alteração do pacote instalado.

**Sobre o Qt / PySide6 (LGPL-3.0):** ele é usado como biblioteca dinâmica e não foi
modificado. Você tem o direito de substituí-lo por outra versão compatível — para isso,
recompile a partir do código-fonte disponível no repositório do projeto, seguindo as
instruções do README.

| Biblioteca | Versão | Licença |
|---|---|---|
"""


def _texto_da_licenca(dist):
    """O primeiro arquivo de licença que o pacote trouxer, ou `None`."""
    for arquivo in dist.files or []:
        nome = arquivo.name.upper()
        if nome.startswith(("LICENSE", "COPYING", "LICENCE")):
            try:
                caminho = Path(dist.locate_file(arquivo))
                if caminho.is_file() and caminho.stat().st_size > 0:
                    return caminho
            except OSError:
                continue
    return None


def _rotulo(dist):
    bruto = (
        dist.metadata.get("License-Expression")
        or dist.metadata.get("License")
        or ""
    ).strip()
    # Alguns pacotes põem a licença inteira no campo `License`. Só a primeira linha serve
    # como rótulo; o texto completo vai no arquivo ao lado.
    primeira = bruto.splitlines()[0].strip() if bruto else ""

    # O campo `License` é texto livre, e alguns pacotes despejam ali a licença inteira ou o
    # aviso de copyright — o numpy declara "Copyright (c) 2005-2024, NumPy Developers.".
    # Quando não parece um identificador, o classificador é a fonte confiável.
    parece_identificador = (
        primeira
        and len(primeira) <= 60
        and "copyright" not in primeira.lower()
    )
    if parece_identificador:
        return primeira

    for classificador in dist.metadata.get_all("Classifier") or []:
        if classificador.startswith("License ::"):
            return classificador.rsplit("::", 1)[-1].strip()

    return "ver arquivo ao lado"


def coletar():
    DESTINO.mkdir(exist_ok=True)
    linhas = []
    faltando = []

    for nome in PACOTES:
        try:
            dist = metadata.distribution(nome)
        except metadata.PackageNotFoundError:
            faltando.append(f"{nome}: não instalado")
            continue

        origem = _texto_da_licenca(dist)
        if origem is None:
            faltando.append(f"{nome}: sem arquivo de licença no dist-info")
            arquivo = "—"
        else:
            arquivo = f"{nome}-LICENSE.txt"
            shutil.copyfile(origem, DESTINO / arquivo)

        linhas.append(f"| {nome} | {dist.version} | {_rotulo(dist)} |")

    (DESTINO / "LEIA-ME.md").write_text(
        CABECALHO + "\n".join(linhas) + "\n", encoding="utf-8"
    )

    print(f"{len(linhas)} pacotes catalogados em {DESTINO}")
    for problema in faltando:
        print(f"  ATENÇÃO: {problema}")

    # Faltar texto de licença não é detalhe: é obrigação de distribuição não cumprida.
    return 1 if faltando else 0


if __name__ == "__main__":
    sys.exit(coletar())

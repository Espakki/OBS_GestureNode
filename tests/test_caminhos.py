"""Onde o config.json mora em cada forma de rodar o app. Ver D-29 e B-08."""

import sys
from pathlib import Path

import pytest

from util import caminhos


@pytest.fixture
def congelado(monkeypatch):
    """Finge um bundle do PyInstaller."""

    def _ativar(meipass=None):
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        if meipass is not None:
            monkeypatch.setattr(sys, "_MEIPASS", str(meipass), raising=False)

    return _ativar


class TestRodandoDoCodigoFonte:
    def test_fica_ao_lado_do_projeto(self):
        """Em desenvolvimento o config continua na raiz — comportamento histórico."""
        destino = caminhos.caminho_do_config()
        assert destino.name == "config.json"
        assert destino.parent == Path(caminhos.__file__).resolve().parent.parent

    def test_nao_esta_congelado(self):
        assert caminhos.esta_congelado() is False

    def test_nao_tenta_migrar(self, tmp_path):
        """Migração é exclusiva do bundle; do fonte não há de onde migrar."""
        assert caminhos.migrar_config_legado(tmp_path / "config.json") is False


class TestEmpacotado:
    def test_vai_para_appdata(self, congelado, monkeypatch, tmp_path):
        congelado()
        monkeypatch.setenv("APPDATA", str(tmp_path))

        destino = caminhos.caminho_do_config()

        assert destino == tmp_path / caminhos.NOME_DO_APP / "config.json"
        assert destino.parent.is_dir(), "o diretório precisa ser criado"

    def test_nao_fica_dentro_do_bundle(self, congelado, monkeypatch, tmp_path):
        """A regressão que motivou o B-08.

        Antes, `Path(__file__).parent` congelado resolvia para o `_MEIPASS`, então o
        config ia para `dist\\main\\_internal\\`. Instalado em Program Files, o save
        falhava — e falhava em silêncio.
        """
        meipass = tmp_path / "bundle" / "_internal"
        meipass.mkdir(parents=True)
        congelado(meipass=meipass)
        monkeypatch.setenv("APPDATA", str(tmp_path / "roaming"))

        destino = caminhos.caminho_do_config()

        assert meipass not in destino.parents
        assert "_internal" not in str(destino)

    def test_cai_para_a_home_sem_appdata(self, congelado, monkeypatch):
        """Ambiente sem APPDATA não pode derrubar o app."""
        congelado()
        monkeypatch.delenv("APPDATA", raising=False)

        destino = caminhos.caminho_do_config(criar_diretorio=False)

        assert destino.name == "config.json"
        assert Path.home() in destino.parents


class TestMigracaoDoLocalAntigo:
    def test_traz_config_que_estava_no_bundle(self, congelado, tmp_path):
        meipass = tmp_path / "_internal"
        meipass.mkdir()
        (meipass / "config.json").write_text('{"modo": "manual"}', encoding="utf-8")
        congelado(meipass=meipass)

        destino = tmp_path / "roaming" / "config.json"
        destino.parent.mkdir()

        assert caminhos.migrar_config_legado(destino) is True
        assert destino.read_text(encoding="utf-8") == '{"modo": "manual"}'

    def test_nunca_sobrescreve_config_existente(self, congelado, tmp_path):
        """Config atual do usuário vence sempre — migrar não pode destruir dado."""
        meipass = tmp_path / "_internal"
        meipass.mkdir()
        (meipass / "config.json").write_text('{"modo": "antigo"}', encoding="utf-8")
        congelado(meipass=meipass)

        destino = tmp_path / "config.json"
        destino.write_text('{"modo": "atual"}', encoding="utf-8")

        assert caminhos.migrar_config_legado(destino) is False
        assert destino.read_text(encoding="utf-8") == '{"modo": "atual"}'

    def test_sem_legado_nao_faz_nada(self, congelado, tmp_path):
        meipass = tmp_path / "_internal"
        meipass.mkdir()
        congelado(meipass=meipass)

        assert caminhos.migrar_config_legado(tmp_path / "config.json") is False

"""A versão do aplicativo, num lugar só. Ver D-51.

Até aqui a versão existia apenas como tag do git, e o app não sabia a própria. Isso
bloqueava duas coisas ao mesmo tempo: mostrar a versão ao usuário (que é o primeiro dado
que qualquer suporte pede) e comparar com o último release do GitHub para avisar de
atualização.

**Bumpar é manual e deliberado.** Não é derivado do git: o `.exe` empacotado não carrega o
repositório junto, e um número que só existe quando há `.git` por perto seria uma versão que
falha exatamente onde ela mais importa.

Ao lançar: suba o número aqui, feche a seção no `CHANGELOG.md` e crie a tag `v<versão>`
apontando para esse commit. As três coisas precisam concordar.
"""

__version__ = "1.0.0"

NOME_DO_APP = "OBS GestureNode"

# Onde o app procura por versões novas. Ver B-27.
REPOSITORIO = "Espakki/OBS_GestureNode"
URL_DE_RELEASES = f"https://github.com/{REPOSITORIO}/releases"

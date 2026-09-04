# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).
Versionamento [semântico](https://semver.org/lang/pt-BR/).

## [Não lançado]

Primeira versão pública em preparação. Tudo abaixo entrou depois do MVP interno.

### Adicionado

- **Aviso de limitação da câmera na tela.** Modos que a webcam não oferece ficam
  desabilitados, e uma faixa na aba Geral diz qual é o limite dela — em vez de o app
  falhar quando você tentasse usar.
- **Configuração recomendada.** Um botão escolhe a melhor resolução e FPS para o modo em
  uso: em Teste e Manual mira 720p, porque acima disso não melhora a detecção; em
  Automático usa a maior resolução, porque é o que o público vê no OBS.
- **Ajuste automático de FPS.** Se a câmera não aceita o valor pedido, o app abre no que
  ela suporta e avisa, em vez de recusar a iniciar.
- **Esqueleto na saída do OBS** como opção separada da do preview: dá para calibrar vendo
  as linhas sem que o público as veja.
- **Confirmação antes de reiniciar** ao trocar entre 1 e 2 mãos.
- Licença MIT, README para usuário e desenvolvedor, e este changelog.

### Corrigido

- **A imagem enviada ao OBS estava em qualidade reduzida.** A câmera virtual recebia o
  quadro reduzido usado na detecção, reampliado — agora recebe a captura em resolução
  nativa.
- **Joinha inclinado virava deslike.** Acima de ~70° de inclinação o gesto era reconhecido
  como o oposto, o que trocava para a cena errada. Agora existe uma faixa larga em que
  nenhum dos dois dispara, e inverter passou a ser impossível sem atravessá-la.
- **Joinha de lado era aceito.** Com o polegar apontando para trás ou muito na diagonal, o
  gesto disparava sem que você tivesse feito um joinha.
- **Parar e iniciar de novo falhava** com erro de câmera ocupada, muitas vezes exigindo
  fechar o app.
- **"Câmera ocupada" quando o problema era outro.** O sistema usa o mesmo erro para
  dispositivo em uso e para modo não suportado, então o app mandava procurar um programa
  que não existia.
- **Configurações se perdiam sem aviso** no app instalado: eram gravadas dentro da pasta do
  programa, e em local protegido a gravação falhava em silêncio. Agora vão para a pasta do
  usuário, e uma falha de gravação avisa na tela.
- **Trocar o nome da cena de um gesto parecia não salvar.** Um nome que o OBS não tinha
  derrubava a conexão inteira, e nada voltava a funcionar até reiniciar.
- **A janela travava e piscava ao parar** a captura.
- **A interface podia ficar travada** com os botões desabilitados quando a captura falhava
  ao iniciar.
- **Duas mãos em quadro disparavam duas ações.** Agora vale a primeira mão a completar o
  gesto.
- **Esqueleto quase invisível em 1080p**: a espessura do traço não acompanhava a resolução.
- Instalação limpa não subia por dependências não declaradas.

### Alterado

- **Executável 38% menor**: de 774 MB para 480 MB, removendo bibliotecas que vinham de
  carona e o app não usa.
- **Interface da aba Geral enxugada**: 71% menos texto nos trechos revisados, com as opções
  de esqueleto virando botões no mesmo padrão visual do resto.
- **Detecção de duas mãos** deixou de ser sobre gestos combinados e passou a ser
  tolerância: ter as duas mãos em quadro não atrapalha mais, e a ação continua sendo de uma
  mão só.
- Gestos combinados foram **removidos** — exigiam soltar controle, teclado e mouse, o que
  contraria o motivo do app existir.

### Interno

- Camada de plataforma isolada em `plataforma/`, primeiro passo para o suporte a Linux.
- 203 testes automatizados, de zero. Rodam em ~2s, sem webcam e sem OBS.
- Decisões de projeto registradas em `.planning/DECISIONS.md`.

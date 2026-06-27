# AGENTS.md - Protótipo: MyQTT Performance HUD

## 1. Objetivo Geral do Projeto

Desenvolver um protótipo funcional de um overlay gráfico para exibir métricas de recursos da máquina (CPU, RAM) sobre jogos em execução em tela cheia no ambiente Wayland (CachyOS). O sistema utilizará o protocolo MQTT para comunicação entre o coletor de dados e a interface de exibição, e o framework Qt6 (PySide6) para a construção da janela transparente e sobreposta.

## 2. Arquitetura de Alto Nível

O sistema será composto por **dois processos independentes e leves**, comunicando-se exclusivamente via um broker MQTT local (ou externo). Isso garante desacoplamento e segue o padrão didático do MQTT.

- **Processo A (Coletor/Publicador)**: Script em Python executado em segundo plano. Responsável por interrogar o sistema operacional em intervalos regulares e publicar os dados em tópicos MQTT.
- **Processo B (Assinante/Overlay)**: Aplicação gráfica Qt6 em Python que se inscreve nos tópicos MQTT e renderiza as informações em uma janela overlay configurada para o Wayland.

## 3. Estrutura de Módulos e Responsabilidades

### 3.1. Módulo de Coleta de Dados (Processo A)

- **Tecnologia**: Python 3 + `psutil`.
- **Funcionalidade**: Coletar percentuais de uso da CPU (geral) e da memória RAM (percentual de uso).
- **Frequência**: Publicar os dados a cada 2 segundos no broker MQTT.
- **Tópicos definidos**:
  - `sistema/pc/cpu`
  - `sistema/pc/ram`

### 3.2. Módulo de Cliente MQTT (Compartilhado)

- **Tecnologia**: Biblioteca `paho-mqtt`.
- **Configuração**: Conectar-se a um broker público/local (ex: `broker.emqx.io` ou `localhost`). Utilizar QoS 1 para garantir a entrega das mensagens.
- **Comportamento no Processo B**: Implementar um loop de escuta assíncrona (`loop_start()`) para não bloquear a interface gráfica.

### 3.3. Módulo do Overlay Gráfico (Processo B - Qt6)

- **Tecnologia**: PySide6 (Python bindings para Qt6).
- **Janela Principal (QMainWindow/QWidget)**:
  - **Sem Bordas**: `setWindowFlags(Qt.FramelessWindowHint)`.
  - **Sempre no Topo**: `setWindowFlags(Qt.WindowStaysOnTopHint)`.
  - **Transparência**: Habilitar `setAttribute(Qt.WA_TranslucentBackground)`.
  - **Foco e Clique**: A janela não deve roubar o foco do teclado nem bloquear cliques do mouse para o jogo. Configurar `setAttribute(Qt.WA_TransparentForMouseEvents)` (ou equivalente no Qt6 para permitir que eventos de clique atravessem a janela).
- **Renderização**: Utilizar QWidgets simples (QLabel) ou QML para exibir os valores de forma legível (fonte branca/verde com sombra para contraste).

### 3.4. Integração entre MQTT e UI

- **Threading**: O cliente MQTT deve rodar em uma thread separada ou via `QTimer` para consultar as mensagens recebidas, evitando travar o loop de eventos principal do Qt.
- **Atualização**: Quando uma nova mensagem chegar no tópico de CPU ou RAM, o callback deve atualizar o texto do respectivo QLabel utilizando o mecanismo de sinais/slots para garantir a segurança entre threads (emitir um sinal que é conectado a um slot que atualiza a UI).

## 4. Estratégia Crítica para o Wayland

A compatibilidade com Wayland exige atenção especial:

- **Forçar o Backend**: O Qt6 pode tentar usar XWayland. Para garantir o uso nativo do Wayland, a aplicação deve ser iniciada com a variável de ambiente `QT_QPA_PLATFORM=wayland`.
- **Protocolo Layer-Shell (Opcional Avançado)**: Para garantir que o overlay fique *acima* de janelas em tela cheia que usam o protocolo exclusivo do Wayland, pode ser necessário utilizar a extensão `qt-wayland-compositor` ou integrar a biblioteca `layer-shell-qt`. Para o protótipo inicial, a flag `WindowStaysOnTopHint` somada ao `FramelessWindowHint` já deve ser suficiente para a maioria dos jogos rodando via XWayland ou nativos, desde que o gerenciador de janelas (KWin/Sway) permita sobreposição.
- **Posicionamento**: Definir a geometria da janela no canto superior esquerdo ou inferior direito, com tamanho fixo (ex: 200x100 pixels) para não atrapalhar a visão do jogo.

## 5. Fluxo de Comunicação e Dados

1. **Inicialização**:
   - Processo B (Overlay) inicia, conecta-se ao broker e se inscreve em `sistema/pc/#`.
   - Processo A (Coletor) inicia, conecta-se ao broker e começa a publicar.
2. **Execução Contínua**:
   - Coletor -> Publica CPU/RAM -> Broker.
   - Broker -> Encaminha para Overlay.
   - Overlay -> Atualiza a interface em tempo real.
3. **Encerramento**: Ambos os processos devem incluir um `try/except` para capturar `KeyboardInterrupt` e desconectar gracefulmente do broker.

## 6. Setup do Ambiente de Desenvolvimento (Obrigações Técnicas)

O ambiente de desenvolvimento é estritamente definido para garantir a reprodutibilidade e a integração nativa com o sistema CachyOS (base Arch Linux).

### 6.1. Gerenciamento de Pacotes do Sistema

- **Ferramenta obrigatória**: `pacman`.
- Todas as dependências de nível de sistema **devem** ser instaladas exclusivamente através do `pacman`. Isso inclui, mas não se limita a: interpretador Python, bibliotecas de desenvolvimento Qt6, suporte a Wayland, e o broker MQTT (ex: `mosquitto`).

### 6.2. Gerenciamento do Ambiente Python e Dependências

- **Ferramenta obrigatória**: `uv` (astral-sh/uv).
- O gerenciamento do ambiente virtual, a instalação das bibliotecas Python específicas do projeto e o controle de versões **devem** ser realizados exclusivamente com o `uv`.
- As dependências Python obrigatórias do projeto são: `pyside6`, `paho-mqtt` e `psutil`.
- A estrutura do repositório **deve** conter os arquivos de manifesto gerenciados pelo `uv` (como `pyproject.toml` e `uv.lock`) para assegurar que todos os desenvolvedores (ou agentes de código) reproduzam o mesmo ambiente.

### 6.3. Observação sobre a Proibição de Descrição de Comandos

Este documento não descreve os comandos específicos para instalação ou configuração. A implementação prática deve ser realizada pelo agente de código seguindo a documentação oficial das ferramentas `pacman` e `uv`, respeitando as obrigações estabelecidas acima.

## 7. Critérios de Aceitação para o Protótipo Mínimo Viável (MVP)

- O script do Coletor deve rodar sem erros e publicar números inteiros (strings) nos tópicos.
- O script do Overlay deve abrir uma janela preta (transparente) com textos estáticos "CPU: 0%" e "RAM: 0%".
- Ao rodar ambos os scripts simultaneamente, os números na janela do overlay devem se atualizar a cada 2 segundos com os valores reais do sistema.
- A janela do overlay deve permanecer visível sobre qualquer janela aberta (incluindo navegadores e jogos em modo janela/tela cheia).
- O clique do mouse e o foco do teclado devem funcionar perfeitamente no aplicativo que está sob o overlay (a janela não pode interceptar interações).

## 8. Não-Escopo do Protótipo (Para este estágio)

- Monitoramento de GPU, temperatura ou rede.
- Suporte a múltiplos monitores com posicionamento dinâmico.
- Sistema de configuração/arquivo `.conf` para personalização de cores ou posição.
- Suporte a protocolo Layer-Shell (será considerado apenas se o `WindowStaysOnTopHint` falhar nos testes iniciais).

# AGENTS.md - Protótipo: MyQTT Performance HUD

## 1. Arquitetura de Alto Nível

O sistema será composto por **dois processos independentes e leves**, comunicando-se exclusivamente via um broker MQTT local (ou externo). Isso garante desacoplamento e segue o padrão didático do MQTT.

- **Processo A (Coletor/Publicador)**: Script em Python executado em segundo plano. Responsável por interrogar o sistema operacional em intervalos regulares e publicar os dados em tópicos MQTT.
- **Processo B (Assinante/Overlay)**: Aplicação gráfica Qt6 em Python que se inscreve nos tópicos MQTT e renderiza as informações em uma janela overlay configurada para o Wayland.

## 2. Estrutura de Módulos e Responsabilidades

### 2.1. Módulo de Coleta de Dados (Processo A)

- **Tecnologia**: Python 3 + `psutil`.
- **Funcionalidade**: Coletar percentuais de uso da CPU (geral) e da memória RAM (percentual de uso).
- **Frequência**: Publicar os dados a cada 2 segundos no broker MQTT.
- **Tópicos definidos**:
  - `sistema/pc/cpu`
  - `sistema/pc/ram`

### 2.2. Módulo de Cliente MQTT (Compartilhado)

- **Tecnologia**: Biblioteca `paho-mqtt`.
- **Configuração**: Conectar-se a um broker público/local (ex: `broker.emqx.io` ou `localhost`). Utilizar QoS 1 para garantir a entrega das mensagens.
- **Comportamento no Processo B**: Implementar um loop de escuta assíncrona (`loop_start()`) para não bloquear a interface gráfica.

### 2.3. Módulo do Overlay Gráfico (Processo B - Qt6)

- **Tecnologia**: PySide6 (Python bindings para Qt6).
- **Janela Principal (QMainWindow/QWidget)**:
  - **Sem Bordas**: `setWindowFlags(Qt.FramelessWindowHint)`.
  - **Sempre no Topo**: `setWindowFlags(Qt.WindowStaysOnTopHint)`.
  - **Transparência**: Habilitar `setAttribute(Qt.WA_TranslucentBackground)`.
  - **Foco e Clique**: A janela não deve roubar o foco do teclado nem bloquear cliques do mouse para o jogo. Configurar `setAttribute(Qt.WA_TransparentForMouseEvents)` (ou equivalente no Qt6 para permitir que eventos de clique atravessem a janela).
- **Renderização**: Utilizar QWidgets simples (QLabel) ou QML para exibir os valores de forma legível (fonte branca/verde com sombra para contraste).

### 2.4. Integração entre MQTT e UI

- **Threading**: O cliente MQTT deve rodar em uma thread separada ou via `QTimer` para consultar as mensagens recebidas, evitando travar o loop de eventos principal do Qt.
- **Atualização**: Quando uma nova mensagem chegar no tópico de CPU ou RAM, o callback deve atualizar o texto do respectivo QLabel utilizando o mecanismo de sinais/slots para garantir a segurança entre threads (emitir um sinal que é conectado a um slot que atualiza a UI).

## 3. Estratégia Crítica para o Wayland

A compatibilidade com Wayland exige atenção especial:

- **Forçar o Backend**: O Qt6 pode tentar usar XWayland. Para garantir o uso nativo do Wayland, a aplicação deve ser iniciada com a variável de ambiente `QT_QPA_PLATFORM=wayland`.
- **Posicionamento**: Definir a geometria da janela no canto superior esquerdo ou inferior direito, com tamanho fixo (ex: 200x100 pixels) para não atrapalhar a visão do jogo.

## 4. Fluxo de Comunicação e Dados

Overlay conecta-se ao broker (`sistema/pc/#`) → Coletor publica CPU/RAM a cada 2s → Broker encaminha → Overlay atualiza UI via signal/slot.
Ambos os processos capturam `KeyboardInterrupt` e desconectam gracefulmente.

## 5. Setup do Ambiente de Desenvolvimento (Obrigações Técnicas)

O ambiente de desenvolvimento é estritamente definido para garantir a reprodutibilidade e a integração nativa com o sistema CachyOS (base Arch Linux).

### 5.1. Gerenciamento de Pacotes do Sistema

- **Ferramenta obrigatória**: `pacman`.
- Todas as dependências de nível de sistema **devem** ser instaladas exclusivamente através do `pacman`. Isso inclui, mas não se limita a: interpretador Python, bibliotecas de desenvolvimento Qt6, suporte a Wayland, e o broker MQTT (ex: `mosquitto`).

### 5.2. Gerenciamento do Ambiente Python e Dependências

- **Ferramenta obrigatória**: `uv` (astral-sh/uv).
- O gerenciamento do ambiente virtual, a instalação das bibliotecas Python específicas do projeto e o controle de versões **devem** ser realizados exclusivamente com o `uv`.
- As dependências Python obrigatórias do projeto são: `pyside6`, `paho-mqtt` e `psutil`.
- A estrutura do repositório **deve** conter os arquivos de manifesto gerenciados pelo `uv` (como `pyproject.toml` e `uv.lock`) para assegurar que todos os desenvolvedores (ou agentes de código) reproduzam o mesmo ambiente.

## 6. Critérios de Aceitação (MVP)

- Coletor publica dados sem erros nos tópicos.
- Overlay abre janela transparente com "CPU: 0%" e "RAM: 0%".
- Valores atualizam a cada 2s com dados reais do sistema.
- Overlay visível sobre qualquer janela (tela cheia inclusa).
- Clique/foco não bloqueados pelo overlay.

## 7. Não-Escopo (Para este estágio)

- GPU, temperatura ou rede.
- Múltiplos monitores ou posicionamento dinâmico.
- Arquivo de configuração (`.conf`).
- Protocolo Layer-Shell (apenas se `WindowStaysOnTopHint` falhar).

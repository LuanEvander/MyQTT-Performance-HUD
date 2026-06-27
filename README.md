# MyQTT Performance HUD (Monitor de Recursos com Overlay Customizado)

## 1. Visão Geral do Projeto

Este projeto consiste no desenvolvimento de um protótipo funcional para monitoramento de recursos de uma máquina pessoal (CPU e RAM) durante a execução de jogos em tela cheia. A solução é composta por dois processos independentes que se comunicam via protocolo MQTT: um coletor de dados e um overlay gráfico customizado desenvolvido com Qt6, otimizado para o ambiente Wayland no sistema operacional CachyOS.

---

## 2. Escopo do Projeto (Scope)

### 2.1. Funcionalidades Incluídas

- **Coleta de Dados**: Extração dos percentuais de uso da CPU (geral) e da memória RAM do sistema em intervalos regulares de 2 segundos.
- **Publicação MQTT**: Envio dos dados para um broker MQTT (local ou público) nos tópicos `sistema/pc/cpu` e `sistema/pc/ram`.
- **Overlay Gráfico**: Janela transparente e sempre visível (sobreposta) que exibe os dados recebidos via MQTT em tempo real, sem bordas ou elementos de interface que interrompam a experiência do jogo.
- **Compatibilidade Wayland**: Configuração específica da janela Qt6 para garantir a renderização correta sobre aplicações em tela cheia no protocolo Wayland, utilizando os flags `FramelessWindowHint`, `WindowStaysOnTopHint` e `WA_TranslucentBackground`.

### 2.2. Fora do Escopo (Limitações do Protótipo)

- Monitoramento de GPU, temperatura, uso de disco ou tráfego de rede.
- Suporte a múltiplos monitores ou posicionamento dinâmico da janela.
- Sistema de persistência de configurações (arquivos `.conf`).
- Implementação avançada do protocolo `layer-shell` do Wayland (será avaliado apenas em caso de falha na sobreposição básica).

---

## 3. Justificativa Técnica e Didática (Justification)

### 3.1. Contexto Acadêmico

Este projeto atende aos requisitos da atividade prática da disciplina de Redes de Computadores, que exige a implementação prática de um dos protocolos elencados (MQTT, HTTP, CoAP ou MCP). A escolha do MQTT é estratégica, pois permite demonstrar de forma clara e tangível os conceitos fundamentais de comunicação em redes: **broker**, **tópicos (pub/sub)** e **desacoplamento de serviços**.

### 3.2. Por que MQTT em vez de IPC nativo?

Embora soluções nativas de comunicação entre processos (IPC) no Linux, como *Unix Domain Sockets* ou *Memória Compartilhada*, sejam tecnicamente mais leves e apresentem menor latência para uma aplicação local, a adoção do MQTT neste projeto vai além da eficiência pura:

1. **Desacoplamento Arquitetural**: A separação entre o coletor (publicador) e o overlay (assinante) permite que cada componente evolua de forma independente. Futuramente, o mesmo coletor pode alimentar múltiplos overlays, dashboards web ou notificações em dispositivos móveis sem necessidade de refatoração.
2. **Adesão ao Padrão de Mercado**: O MQTT é amplamente utilizado em sistemas de telemetria e IoT, sendo a base para ferramentas de monitoramento industrial e automação residencial (ex: Home Assistant). Aprender seu fluxo de requisições e Qualidade de Serviço (QoS) agrega valor profissional ao aluno.
3. **Demonstração Didática do Protocolo**: O projeto evidencia na prática o papel do *Broker* como intermediário central, a hierarquia de tópicos e a comunicação assíncrona, conceitos que seriam obscurecidos caso utilizássemos comunicação direta entre processos.

> **Nota**: A sobrecarga adicional do TCP/IP e do broker é mitigada pelo uso da interface de loopback (`127.0.0.1`) e pela baixa taxa de atualização (2 segundos), tornando o impacto no desempenho do jogo imperceptível.

---

## 4. Arquitetura Proposta

| Componente | Tecnologia | Responsabilidade |
| :--- | :--- | :--- |
| **Coletor de Dados** | Python 3 + `psutil` | Ler recursos do sistema e publicar no Broker. |
| **Cliente MQTT** | `paho-mqtt` | Gerenciar a conexão e a troca de mensagens. |
| **Broker** | `Mosquitto` (local) ou Broker público | Roteamento das mensagens entre publicador e assinante. |
| **Overlay Gráfico** | PySide6 (Qt6) | Renderizar a janela transparente e atualizar os textos com os dados recebidos. |
| **Ambiente Gráfico** | Wayland + KWin/Sway (CachyOS) | Gerenciar a sobreposição de janelas. |

### Fluxo de Dados

1. `Coletor` → (CPU/RAM) → `Broker MQTT`
2. `Broker` → (Encaminha mensagem) → `Overlay Qt6`
3. `Overlay` → (Atualiza UI via Sinais/Slots) → `Usuário visualiza dados sobre o jogo`

---

## 5. Resultados Esperados (Expected Results)

Ao final do desenvolvimento e execução do protótipo, espera-se alcançar os seguintes resultados funcionais e qualitativos:

### 5.1. Resultados Funcionais

1. **Coleta e Publicação**: O script coletor deve executar sem erros, publicando números inteiros (strings) nos tópicos MQTT a cada 2 segundos de forma estável.
2. **Renderização do Overlay**: A janela Qt6 deve ser aberta com fundo completamente transparente, exibindo os rótulos "CPU: X%" e "RAM: Y%" em uma posição fixa da tela (ex: canto superior esquerdo).
3. **Atualização em Tempo Real**: Ao rodar ambos os scripts simultaneamente, os valores exibidos no overlay devem refletir com precisão (tolerância de até 1 segundo) os dados coletados do sistema operacional.
4. **Interação não-bloqueante**: A janela do overlay **não deve** roubar o foco do teclado nem capturar eventos de clique do mouse, permitindo que o jogador interaja normalmente com o jogo subjacente.
5. **Compatibilidade com Jogos**: O overlay deve permanecer visível sobre jogos em modo *tela cheia* (nativos ou via XWayland/Proton) no ambiente Wayland.

### 5.2. Resultados Didáticos (Para o Aluno/Equipe)

- Compreensão prática do ciclo de vida de uma mensagem MQTT (conexão, publicação, assinatura e entrega).
- Capacidade de configurar e depurar uma comunicação cliente-servidor utilizando portas TCP e compreensão dos flags de QoS (Quality of Service).
- Experiência em desenvolver interfaces gráficas com transparência e manipulação de flags de janela em sistemas Linux modernos (Wayland).
- Habilidade em estruturar um projeto de software desacoplado, separando claramente a camada de coleta de dados da camada de apresentação.

### 5.3. Critérios de Aceitação para o MVP

- [ ] O Coletor publica dados sem erros no terminal.
- [ ] O Overlay abre uma janela preta/transparente com as labels estáticas.
- [ ] Os números das labels mudam quando o Coletor está rodando.
- [ ] O Overlay fica visível sobre qualquer janela (navegador, editor, jogo em modo janela).
- [ ] O clique do mouse não é bloqueado pela janela do overlay.

---

## 6. Considerações Finais

O projeto proposto equilibra a exigência acadêmica de aplicação de um protocolo de redes com a resolução de um problema real e imediato (monitoramento de desempenho em jogos). A escolha do MQTT, justificada pelo desacoplamento e pela didática, garante que o resultado final seja não apenas um software funcional, mas uma demonstração sólida dos conceitos fundamentais de comunicação em redes de computadores.

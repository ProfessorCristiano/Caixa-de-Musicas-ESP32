# CHANGES.md — Caixa de Música ESP32 (versão Web)

## Resumo

O código original tocava uma lista fixa de ~32 músicas em sequência,
uma atrás da outra, sem nenhuma interação do usuário. Esta versão
transforma o projeto em uma **caixa de música controlada por uma
página web**: o ESP32 cria um servidor HTTP e qualquer pessoa
conectada à mesma rede Wi-Fi pode abrir o IP do ESP32 no navegador,
escolher a música pelo nome e ligar/desligar o modo aleatório.

## Estrutura de arquivos (antes: 1 arquivo → agora: 5 arquivos)

| Arquivo         | Responsabilidade                                                        |
|-----------------|---------------------------------------------------------------------------|
| `songs.py`      | Frequências das notas + todas as melodias/tempos + dicionário `SONGS`   |
| `player.py`     | Motor de reprodução assíncrono (toca notas sem travar o servidor web)   |
| `web_server.py` | Servidor HTTP (rotas da API + página HTML/CSS/JS de controle)           |
| `config.py`     | Configurações editáveis: Wi-Fi, pino do buzzer, porta do servidor       |
| `main.py`       | Ponto de entrada: conecta o Wi-Fi e roda player + servidor em paralelo  |

## Principais mudanças de comportamento

1. **Reprodução sob demanda, não mais sequencial.** As 32 músicas
   continuam todas presentes (nada foi removido), mas agora ficam
   "paradas" esperando o usuário escolher uma pela página web, em vez
   de tocarem automaticamente uma atrás da outra ao ligar o ESP32.

2. **Página web de controle.** Acessando `http://<IP-do-ESP32>/` no
   navegador, o usuário vê um botão para cada música (nome de
   exibição, não a chave técnica) e clica para tocar.

3. **Modo aleatório opcional.** Um checkbox na página liga/desliga o
   "modo aleatório": quando ligado, ao terminar a música atual, se o
   usuário não tiver escolhido outra, uma música aleatória começa a
   tocar sozinha. Quando desligado, o ESP32 fica em silêncio esperando
   uma escolha.

4. **Troca de música em andamento.** Se o usuário escolher uma nova
   música enquanto outra está tocando, a atual é interrompida (na
   próxima nota, não instantaneamente) e a nova começa.

5. **Não bloqueante (assíncrono).** Trocamos todos os
   `time.sleep_ms()` (que travam o processador) por
   `await uasyncio.sleep_ms()`. Isso permite que o servidor web e o
   player "convivam" ao mesmo tempo — o ESP32 responde a requisições
   HTTP mesmo enquanto uma nota está tocando.

## Bug encontrado e corrigido no código original

Em `greensleeves`, duas notas estavam escritas como `D4,04` (com um
zero à esquerda). Isso é um erro de sintaxe em Python 3 e também no
MicroPython atual ("leading zeros in decimal integer literals are not
permitted") — o arquivo original só funcionava porque a versão de
MicroPython usada na época provavelmente era mais tolerante, ou o
trecho nunca foi de fato executado/testado. Corrigido para `D4,4`
(o valor numérico pretendido, sem o zero à esquerda).

## Endpoints do servidor web (API)

| Rota                        | Método | Descrição                                             |
|------------------------------|--------|--------------------------------------------------------|
| `/`                          | GET    | Página HTML de controle (lista de músicas + checkbox)  |
| `/api/songs`                 | GET    | Lista de músicas em JSON `[{key, name}, ...]`           |
| `/api/play?key=<chave>`      | GET    | Pede para tocar a música `<chave>`                      |
| `/api/random?value=1\|0`     | GET    | Liga (`1`) ou desliga (`0`) o modo aleatório            |
| `/api/status`                | GET    | Estado atual: `{playing_key, playing_name, random_mode}`|

A página web consulta `/api/status` a cada 2 segundos para atualizar
o que está tocando na tela (sem precisar recarregar a página).

## Como usar

1. Edite `config.py`:
   - Preencha `WIFI_SSID` e `WIFI_PASSWORD` com os dados da sua rede.
   - Ou defina `USAR_MODO_ACCESS_POINT = True` para o ESP32 criar sua
     própria rede Wi-Fi (útil sem roteador disponível).
   - Confira `PINO_BUZZER` (padrão: GPIO 25, igual ao original).
2. Copie os 5 arquivos (`songs.py`, `player.py`, `web_server.py`,
   `config.py`, `main.py`) para a raiz do sistema de arquivos do ESP32
   (por exemplo, usando `mpremote`, `ampy` ou o Thonny).
3. Ligue o ESP32. Observe no console serial a mensagem com o IP
   (algo como `Conectado! Acesse a caixa de música em: http://192.168.0.42`).
4. Abra esse endereço no navegador de um celular/computador conectado
   à mesma rede.

## Pontos de atenção / limitações conhecidas

- O servidor HTTP é minimalista (feito só com `uasyncio`, sem
  bibliotecas externas como `microdot`), o que é ideal para não gastar
  memória no ESP32, mas não implementa HTTPS, autenticação, nem
  suporte a múltiplos parâmetros complexos na URL — suficiente para
  este projeto, mas vale saber caso queira expandir.
- A API assume `buzzer.duty(...)` no estilo "ESP32 clássico"
  (0–1023), igual ao código original. Se você atualizar para uma
  versão do MicroPython que use `duty_u16()`, será preciso ajustar
  `player.py` (métodos `self.buzzer.duty(...)`) de acordo.
- Testado com mocks em Python 3 puro (simulando `machine`, `network`,
  `uasyncio`, `urandom`, `ujson`) para validar a lógica de rotas HTTP,
  geração de HTML e o motor de reprodução (incluindo troca de música
  em andamento e modo aleatório). Não foi testado em hardware ESP32
  real — recomenda-se testar a conexão Wi-Fi e o som do buzzer
  fisicamente antes de considerar o projeto pronto para uso.

## Atualização — Músicas adicionadas a partir de RTTTL

Foram adicionadas **23 novas músicas** ao catálogo, convertidas do
formato RTTTL (Ring Tone Text Transfer Language — o formato clássico
de toques de celular) para o formato de listas `[NOTA, duração, ...]`
já usado neste projeto. O catálogo passou de 32 para **55 músicas**.

### Regras da conversão

- Duração/oitava ausentes numa nota RTTTL usam os valores padrão do
  cabeçalho (`d=`, `o=`) daquela música.
- Nota pontuada (`.` no RTTTL) virou **duração negativa**, seguindo a
  mesma convenção que o arquivo já usava (ex.: `-4` = seminima pontuada).
- Pausa (`p` no RTTTL) virou `REST`.
- A oitava do RTTTL usa a mesma escala já usada nas constantes deste
  projeto (C4 = dó central), então a conversão de oitava é direta.
- Cada conversão foi feita por um script (não digitada manualmente)
  para evitar erros de transcrição em centenas de notas, e depois
  validada automaticames: sintaxe, pares nota/duração, e uma
  conferência manual de uma música pequena (`smbdeath`) nota a nota
  contra o RTTTL original.

### Músicas adicionadas (chave → nome de exibição)

| Chave | Nome de exibição |
|---|---|
| `thesimpsons` | Os Simpsons - Tema |
| `indiana` | Indiana Jones - Tema |
| `entertainer` | The Entertainer - Scott Joplin |
| `muppets` | Os Muppets - Tema |
| `xfiles` | Arquivo X - Tema |
| `looney` | Looney Tunes - Tema |
| `m20thcenfox` | 20th Century Fox - Fanfarra |
| `bond` | James Bond - Tema 007 |
| `mash` | Tema de MASH |
| `goodbad` | Three Amigos (O Bom, o Mau e o Feio) |
| `topgun` | Top Gun - Tema |
| `ateam` | A-Team (Esquadrão Classe A) |
| `flinstones` | Os Flintstones - Tema |
| `jeopardy` | Jeopardy - Tema de Espera |
| `gadget` | Inspetor Bugiganga - Tema |
| `smurfs` | Os Smurfs - Tema |
| `mahnamahna` | Mahna Mahna (Muppets) |
| `leisuresuit` | Leisure Suit Larry - Tema |
| `missionimp` | Missão Impossível - Tema |
| `smb` | Super Mario Bros (RTTTL) |
| `smbundergr` | Super Mario Bros - Subsolo |
| `smbwater` | Super Mario Bros - Fase Aquática |
| `smbdeath` | Super Mario Bros - Morte do Personagem |

Nenhum arquivo além de `songs.py` precisou mudar: `player.py`,
`web_server.py` e `main.py` já leem o catálogo inteiro a partir de
`songs.SONGS`, então as novas músicas aparecem automaticamente na
página web e no modo aleatório.

## Atualização — Botão Parar, persistência de estado e volume ajustável

Três melhorias pedidas foram implementadas, todas dentro de
`player.py` e `web_server.py` (nenhum outro arquivo precisou mudar).

### 1) Botão "Parar"

- Novo endpoint `GET /api/stop` e método `MusicPlayer.stop()`.
- Silencia o buzzer **imediatamente** (não espera a nota atual
  terminar) e mantém o player ocioso, mesmo que o modo aleatório
  esteja ligado — ele só volta a tocar sozinho se o usuário escolher
  uma música manualmente ou reativar o checkbox de aleatório.
- Novo botão vermelho "Parar" na página web, acima da lista de músicas.
- `/api/status` agora inclui `"stopped": true/false` para a página
  web mostrar "Parado (buzzer em silêncio)" quando aplicável.

### 2) Persistência de estado (sobrevive a reinícios)

- Novo arquivo `estado.json`, salvo na raiz do sistema de arquivos do
  ESP32 (mesmo lugar dos `.py`), guardando: última música tocada,
  modo aleatório (ligado/desligado) e volume.
- Salva automaticamente sempre que: uma música começa a tocar, o
  modo aleatório é ligado/desligado, ou o volume é ajustado — **não**
  a cada nota (isso evitaria desgaste desnecessário da memória flash).
- Ao ligar o ESP32, o estado salvo é lido de volta:
  - Se o modo aleatório **estava ligado**, ele continua ligado e o
    próprio sorteio aleatório assume a reprodução.
  - Se o modo aleatório **estava desligado**, a última música tocada
    é retomada automaticamente.
  - Se o arquivo não existir ainda (primeira vez), usa os padrões
    (aleatório desligado, volume 70%).

### 3) Volume ajustável

- Novo slider (`<input type="range">`) na página web, de 0% a 100%.
- Novo endpoint `GET /api/volume?value=0-100` e método
  `MusicPlayer.set_volume(valor)`. Valores inválidos são ignorados
  (retorna `{"ok": false}`); valores fora da faixa 0-100 são
  "grudados" no limite mais próximo.
- Implementado controlando o **duty cycle** do PWM: volume 100% usa
  duty 512 (50% — o ponto que soa mais "cheio" num buzzer passivo
  tocado com onda quadrada), e volumes menores usam uma fração
  proporcional desse valor.
- A mudança de volume tem efeito **imediato**, mesmo no meio de uma
  música tocando (o volume é lido nota a nota, não fixado no início
  da música).
- **Limitação de hardware, documentada no código:** alguns buzzers
  passivos respondem bem a variações de duty cycle (perceptível como
  volume), mas outros — dependendo do driver/amplificador — só têm,
  na prática, "ligado" e "desligado", quase sem diferença perceptível
  de volume entre 30% e 90%, por exemplo. Teste no seu hardware
  específico; se o efeito for fraco, `DUTY_MAXIMO` em `player.py`
  pode precisar de ajuste, ou o hardware pode simplesmente não
  suportar controle de volume por software.

### Bug encontrado e corrigido durante a implementação

Ao adicionar o botão Parar, um bug foi introduzido e pego pelos
testes automatizados antes de ser entregue: a flag interna
`_skip_requested` (usada para interromper a música atual) só era
zerada quando o usuário escolhia uma música manualmente — não quando
o modo aleatório sorteava a próxima. Resultado: depois de usar
"Parar" e depois religar o modo aleatório, a próxima música sorteada
era interrompida instantaneamente, antes mesmo da primeira nota
tocar (o buzzer ficava mudo mesmo com uma música "selecionada").
Corrigido zerando essa flag logo depois de decidir qual música vai
tocar, não importa se ela veio de um pedido manual ou do sorteio.

### Testes realizados (com mocks de `machine`/`network`/`uasyncio`/`ujson`)

- Volume: duty cycle calculado corretamente para 30%, 42%, e valores
  fora da faixa (999 → limitado a 100); valor inválido (`abc`) é
  rejeitado sem quebrar o servidor.
- Parar: silencia o buzzer na hora; escolher uma música nova depois
  de parar volta a funcionar normalmente.
- Persistência: `estado.json` é criado nas mudanças certas; uma nova
  instância de `MusicPlayer` (simulando reiniciar o ESP32) restaura
  corretamente o volume, o modo aleatório e retoma a última música
  quando o aleatório estava desligado.
- Servidor HTTP: `/api/stop`, `/api/volume` e `/api/status` testados
  via conexão de socket real, e a página HTML confirmada com o botão
  Parar e o slider de volume presentes.

## Próximos passos sugeridos (não implementados)

- Múltiplos usuários controlando ao mesmo tempo podem gerar pequenas
  disputas (ex.: dois cliques quase simultâneos em músicas diferentes)
  — hoje "quem manda por último, vale", sem fila de pedidos.
- Autenticação/senha na página, caso a rede Wi-Fi seja compartilhada
  com pessoas que você não queira que troquem a música.

## Atualização — Rede Wi-Fi própria "JukeBox" (modo Access Point)

Agora o ESP32 já vem configurado, por padrão, para criar sua própria
rede Wi-Fi em vez de depender de um roteador existente — assim, os
celulares se conectam direto nele, em qualquer lugar.

### O que mudou

- `config.py`:
  - `USAR_MODO_ACCESS_POINT = True` (antes era `False` por padrão).
  - `AP_SSID = "JukeBox"` (antes: `"ESP32-CaixaDeMusica"`).
  - `AP_PASSWORD = "S2musica"` (antes: `"musica123"`).
  - A opção de usar uma rede Wi-Fi existente (modo "estação")
    continua disponível — basta voltar `USAR_MODO_ACCESS_POINT` para
    `False` e preencher `WIFI_SSID`/`WIFI_PASSWORD`.
- `main.py`:
  - Validação da senha do Access Point: se `AP_PASSWORD` tiver menos
    de 8 caracteres, o programa para com uma mensagem de erro clara
    em vez de criar uma rede com comportamento inesperado (o WPA2,
    protocolo de segurança usado aqui, exige 8+ caracteres).
  - Mensagem impressa no console serial ficou mais completa ao usar
    o modo Access Point: mostra o nome da rede, a senha e o link
    para abrir no navegador, para facilitar o primeiro uso.

### Como usar

1. Grave os arquivos no ESP32 normalmente (nenhum arquivo novo, só
   `config.py` e `main.py` foram alterados).
2. Ligue o ESP32. Ele vai criar a rede Wi-Fi **"JukeBox"**.
3. No celular, vá em Wi-Fi, conecte-se à rede "JukeBox" com a senha
   **"S2musica"**.
4. Abra o navegador e acesse o endereço mostrado no console serial do
   ESP32 (em modo Access Point, normalmente `http://192.168.4.1`).

### Limitações do modo Access Point (bom saber)

- Enquanto estiver nesse modo, o ESP32 **não tem acesso à internet**
  — ele só cria uma rede local entre ele e os celulares conectados.
  Isso não afeta o funcionamento do projeto (a página e a música
  tocam normalmente), só significa que não dá para, por exemplo,
  abrir outros sites enquanto conectado só a essa rede.
- O alcance do Wi-Fi criado pelo ESP32 costuma ser mais curto que o
  de um roteador doméstico — para uma festa grande ou área externa,
  vale testar a distância com antecedência.
- Por padrão, o ESP32 aceita várias conexões simultâneas nessa rede
  (o hardware costuma suportar ~4 dispositivos conectados ao mesmo
  tempo), então vários celulares podem controlar a caixa de música
  ao mesmo tempo.

### Teste realizado

- Validado (com mocks do módulo `network`) que: o modo Access Point
  usa exatamente `AP_SSID`/`AP_PASSWORD` de `config.py`; uma senha
  menor que 8 caracteres é rejeitada com mensagem clara antes de
  tentar criar a rede; e o modo estação (conectar a um roteador
  existente) continua funcionando normalmente para quem preferir
  usá-lo em vez do Access Point.



# -*- coding: utf-8 -*-
"""
web_server.py
=============
Servidor web bem simples (sem bibliotecas externas) rodando com
uasyncio no ESP32. Ele serve:

  GET /                       -> página HTML com a lista de músicas
  GET /api/songs               -> lista de músicas em JSON
  GET /api/play?key=<chave>    -> pede para tocar a música <chave>
  GET /api/stop                -> silencia o buzzer sem tocar outra música
  GET /api/random?value=1|0    -> liga/desliga o modo aleatório
  GET /api/volume?value=0-100  -> ajusta o volume (duty cycle do PWM)
  GET /api/status              -> estado atual (música, modo aleatório, volume)

A página HTML usa JavaScript simples (fetch) para chamar essas rotas
sem precisar recarregar a página inteira, e consulta /api/status a
cada 2 segundos para atualizar o que está tocando na tela.
"""

import uasyncio as asyncio
import ujson as json

from songs import SONGS


def _parse_query(path):
    """
    Recebe algo como '/api/play?key=asabranca' e devolve
    ('/api/play', {'key': 'asabranca'}).
    Implementação simples: não faz decode de '%XX', pois as chaves
    das músicas só usam letras minúsculas (não precisamos disso aqui).
    """
    if "?" not in path:
        return path, {}
    caminho, query_string = path.split("?", 1)
    params = {}
    for par in query_string.split("&"):
        if "=" in par:
            chave, valor = par.split("=", 1)
            params[chave] = valor
    return caminho, params


def _montar_pagina_html(player):
    """
    Gera a página HTML principal, com um botão para cada música e o
    checkbox de "modo aleatório". A lista de músicas é ordenada pelo
    nome de exibição, para ficar mais fácil de achar no navegador.
    """
    itens_ordenados = sorted(SONGS.items(), key=lambda item: item[1][2])

    botoes_html = ""
    for chave, (_notas, _tempo, nome_exibicao) in itens_ordenados:
        botoes_html += (
            '<button class="song-btn" data-key="{chave}" '
            'onclick="tocarMusica(\'{chave}\')">{nome}</button>\n'
        ).format(chave=chave, nome=nome_exibicao)

    estado_checkbox = "checked" if player.random_mode else ""
    volume_atual = player.volume

    # Observação: o CSS e o JavaScript ficam no mesmo arquivo HTML
    # (sem dependências externas), pois o ESP32 pode não ter acesso
    # à internet para carregar bibliotecas de um CDN.
    return """<!DOCTYPE html>
<html lang="pt-br">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Caixa de Musica ESP32</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      background: #1e1e2f;
      color: #eee;
      margin: 0;
      padding: 20px;
    }}
    h1 {{
      text-align: center;
      color: #ffcc66;
    }}
    #status {{
      text-align: center;
      font-size: 1.2em;
      margin-bottom: 20px;
      padding: 10px;
      background: #2b2b40;
      border-radius: 8px;
    }}
    #random-box {{
      text-align: center;
      margin-bottom: 20px;
      font-size: 1.1em;
    }}
    #volume-box {{
      text-align: center;
      margin-bottom: 20px;
      font-size: 1.1em;
    }}
    #volume-box input[type="range"] {{
      width: 220px;
      vertical-align: middle;
      margin: 0 10px;
    }}
    #stop-box {{
      text-align: center;
      margin-bottom: 20px;
    }}
    #stop-box button {{
      padding: 10px 24px;
      border: none;
      border-radius: 8px;
      background: #b3403a;
      color: #fff;
      cursor: pointer;
      font-size: 1em;
      font-weight: bold;
    }}
    #stop-box button:hover {{
      background: #d1524b;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
      gap: 10px;
      max-width: 900px;
      margin: 0 auto;
    }}
    .song-btn {{
      padding: 12px;
      border: none;
      border-radius: 8px;
      background: #3a3a55;
      color: #fff;
      cursor: pointer;
      font-size: 0.95em;
      transition: background 0.2s;
    }}
    .song-btn:hover {{
      background: #55558a;
    }}
    .song-btn.playing {{
      background: #ffcc66;
      color: #1e1e2f;
      font-weight: bold;
    }}
  </style>
</head>
<body>
  <h1>Caixa de Musica ESP32</h1>

  <div id="status">Carregando estado...</div>

  <div id="stop-box">
    <button onclick="pararMusica()">Parar</button>
  </div>

  <div id="volume-box">
    <label>
      Volume:
      <input type="range" id="volumeSlider" min="0" max="100" value="{volume_atual}"
             oninput="ajustarVolume(this.value)">
      <span id="volumeLabel">{volume_atual}%</span>
    </label>
  </div>

  <div id="random-box">
    <label>
      <input type="checkbox" id="randomCheckbox" {estado_checkbox}
             onchange="alternarAleatorio()">
      Tocar musica aleatoria quando terminar (se nenhuma for escolhida)
    </label>
  </div>

  <div class="grid">
    {botoes}
  </div>

  <script>
    // Envia o pedido para tocar uma musica especifica.
    function tocarMusica(chave) {{
      fetch('/api/play?key=' + chave).then(atualizarStatus);
    }}

    // Silencia o buzzer sem escolher outra musica.
    function pararMusica() {{
      fetch('/api/stop').then(atualizarStatus);
    }}

    // Liga/desliga o modo aleatorio.
    function alternarAleatorio() {{
      var ligado = document.getElementById('randomCheckbox').checked;
      fetch('/api/random?value=' + (ligado ? '1' : '0')).then(atualizarStatus);
    }}

    // Ajusta o volume. Usa um pequeno atraso (debounce) para nao
    // disparar uma requisicao HTTP a cada pixel arrastado no slider,
    // apenas quando o usuario para de mexer por um instante.
    var temporizadorVolume = null;
    function ajustarVolume(valor) {{
      document.getElementById('volumeLabel').textContent = valor + '%';
      clearTimeout(temporizadorVolume);
      temporizadorVolume = setTimeout(function () {{
        fetch('/api/volume?value=' + valor);
      }}, 150);
    }}

    // Consulta o estado atual do ESP32 e atualiza a tela.
    function atualizarStatus() {{
      fetch('/api/status')
        .then(function (resposta) {{ return resposta.json(); }})
        .then(function (dados) {{
          var caixaStatus = document.getElementById('status');
          if (dados.playing_name) {{
            caixaStatus.textContent = 'Tocando agora: ' + dados.playing_name;
          }} else if (dados.stopped) {{
            caixaStatus.textContent = 'Parado (buzzer em silencio)';
          }} else {{
            caixaStatus.textContent = 'Nada tocando no momento';
          }}

          document.getElementById('randomCheckbox').checked = dados.random_mode;

          // So atualiza o slider se o usuario nao estiver mexendo nele
          // agora mesmo, para nao "brigar" com o dedo/mouse da pessoa.
          if (document.activeElement.id !== 'volumeSlider') {{
            document.getElementById('volumeSlider').value = dados.volume;
            document.getElementById('volumeLabel').textContent = dados.volume + '%';
          }}

          // Destaca visualmente o botao da musica que esta tocando.
          var botoes = document.getElementsByClassName('song-btn');
          for (var i = 0; i < botoes.length; i++) {{
            if (botoes[i].getAttribute('data-key') === dados.playing_key) {{
              botoes[i].classList.add('playing');
            }} else {{
              botoes[i].classList.remove('playing');
            }}
          }}
        }})
        .catch(function (erro) {{ console.log('Erro ao buscar status:', erro); }});
    }}

    // Atualiza o status assim que a pagina carrega e depois a cada 2s.
    atualizarStatus();
    setInterval(atualizarStatus, 2000);
  </script>
</body>
</html>
""".format(estado_checkbox=estado_checkbox, botoes=botoes_html, volume_atual=volume_atual)


_MENSAGENS_STATUS = {
    200: "OK",
    404: "Not Found",
    500: "Internal Server Error",
}


async def _enviar_resposta(writer, status_code, content_type, corpo):
    """Monta e envia uma resposta HTTP simples."""
    if isinstance(corpo, str):
        corpo = corpo.encode("utf-8")

    mensagem = _MENSAGENS_STATUS.get(status_code, "OK")
    cabecalho = (
        "HTTP/1.1 {codigo} {mensagem}\r\n"
        "Content-Type: {tipo}\r\n"
        "Content-Length: {tamanho}\r\n"
        "Connection: close\r\n"
        "\r\n"
    ).format(codigo=status_code, mensagem=mensagem, tipo=content_type, tamanho=len(corpo))

    writer.write(cabecalho.encode("utf-8"))
    writer.write(corpo)
    await writer.drain()


async def _handle_client(reader, writer, player):
    """
    Trata uma única conexão HTTP: lê a linha de requisição, descarta
    os cabeçalhos (não precisamos deles aqui) e decide o que
    responder com base no caminho pedido.
    """
    try:
        linha_requisicao = await reader.readline()
        if not linha_requisicao:
            # Conexão vazia/fechada pelo cliente: o bloco "finally" abaixo
            # cuida de fechar o writer corretamente.
            return

        # Exemplo de linha_requisicao: b'GET /api/play?key=tetris HTTP/1.1\r\n'
        partes = linha_requisicao.decode().split(" ")
        if len(partes) < 2:
            return
        caminho_completo = partes[1]

        # Descarta o restante dos cabeçalhos HTTP (não usamos o corpo aqui).
        while True:
            linha = await reader.readline()
            if linha == b"\r\n" or linha == b"":
                break

        caminho, params = _parse_query(caminho_completo)

        if caminho == "/":
            html = _montar_pagina_html(player)
            await _enviar_resposta(writer, 200, "text/html; charset=utf-8", html)

        elif caminho == "/api/songs":
            lista = [
                {"key": chave, "name": nome}
                for chave, (_n, _t, nome) in SONGS.items()
            ]
            await _enviar_resposta(writer, 200, "application/json", json.dumps(lista))

        elif caminho == "/api/play":
            chave_pedida = params.get("key")
            sucesso = player.request_song(chave_pedida) if chave_pedida else False
            resposta = {"ok": sucesso}
            await _enviar_resposta(writer, 200, "application/json", json.dumps(resposta))

        elif caminho == "/api/stop":
            player.stop()
            await _enviar_resposta(writer, 200, "application/json", json.dumps({"ok": True}))

        elif caminho == "/api/random":
            valor = params.get("value", "0")
            player.set_random_mode(valor == "1")
            await _enviar_resposta(writer, 200, "application/json", json.dumps({"ok": True}))

        elif caminho == "/api/volume":
            valor = params.get("value")
            sucesso = player.set_volume(valor) if valor is not None else False
            await _enviar_resposta(writer, 200, "application/json", json.dumps({"ok": sucesso}))

        elif caminho == "/api/status":
            await _enviar_resposta(writer, 200, "application/json", json.dumps(player.status()))

        else:
            await _enviar_resposta(writer, 404, "text/plain", "Nao encontrado")

    except Exception as erro:
        # Em caso de erro inesperado, não deixamos o servidor inteiro cair;
        # apenas fechamos esta conexão e seguimos ouvindo as próximas.
        print("Erro ao atender cliente HTTP:", erro)
    finally:
        # IMPORTANTE: usar close() + wait_closed() (não existe "aclose()"
        # nem no uasyncio do MicroPython nem no asyncio do CPython).
        # Sem isso, a conexão HTTP nunca é encerrada e o navegador do
        # usuário fica esperando a resposta para sempre.
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


async def start_server(player, port=80):
    """
    Inicia o servidor HTTP na porta indicada (80 = padrão HTTP).
    Cada conexão recebida chama _handle_client em uma nova tarefa,
    permitindo várias pessoas conectadas ao mesmo tempo.
    """
    async def _callback(reader, writer):
        await _handle_client(reader, writer, player)

    servidor = await asyncio.start_server(_callback, "0.0.0.0", port)
    print("Servidor web rodando na porta", port)
    return servidor

# -*- coding: utf-8 -*-
"""
main.py
=======
Ponto de entrada do projeto. Este arquivo:
  1) Conecta o ESP32 ao Wi-Fi (ou cria um Access Point próprio);
  2) Cria o "player" (motor de música) e o servidor web;
  3) Roda os dois ao mesmo tempo, para sempre, usando uasyncio.

No ESP32, se este arquivo se chamar "main.py" e estiver na raiz do
sistema de arquivos, ele roda automaticamente ao ligar a placa.
"""

import network
import uasyncio as asyncio

import config
from player import MusicPlayer
from web_server import start_server


def conectar_wifi():
    """
    Conecta o ESP32 a uma rede Wi-Fi existente (modo estação) ou cria
    uma rede própria (modo Access Point), de acordo com config.py.
    Retorna o endereço IP que o usuário deve digitar no navegador.
    """
    if config.USAR_MODO_ACCESS_POINT:
        # Senha curta demais faria o ESP32 recusar o modo WPA2 (authmode=3)
        # silenciosamente ou criar uma rede com comportamento inesperado.
        # Melhor avisar claramente agora do que deixar o usuário
        # descobrir isso tentando conectar o celular sem sucesso.
        if len(config.AP_PASSWORD) < 8:
            raise ValueError(
                "AP_PASSWORD em config.py precisa ter pelo menos 8 "
                "caracteres (exigencia do WPA2). Valor atual: '{}' "
                "({} caracteres).".format(config.AP_PASSWORD, len(config.AP_PASSWORD))
            )

        ap = network.WLAN(network.AP_IF)
        ap.active(True)
        ap.config(essid=config.AP_SSID, password=config.AP_PASSWORD, authmode=3)
        while not ap.active():
            pass
        ip = ap.ifconfig()[0]
        print("=" * 50)
        print("Rede Wi-Fi 'JukeBox' criada pelo proprio ESP32!")
        print("  Nome da rede (SSID): " + config.AP_SSID)
        print("  Senha:               " + config.AP_PASSWORD)
        print("No celular: conecte-se a essa rede Wi-Fi e depois")
        print("abra no navegador: http://" + ip)
        print("=" * 50)
        return ip

    # Modo estação: conecta a uma rede Wi-Fi já existente.
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    if not sta.isconnected():
        print("Conectando à rede Wi-Fi:", config.WIFI_SSID)
        sta.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
        while not sta.isconnected():
            pass
    ip = sta.ifconfig()[0]
    print("Conectado! Acesse a caixa de música em: http://" + ip)
    return ip


async def main():
    """Função principal assíncrona: cria as tarefas e roda para sempre."""
    ip = conectar_wifi()

    # Cria o player (controla o buzzer) e o servidor web (controla o
    # navegador do usuário). Os dois rodam "ao mesmo tempo" através
    # de tarefas (tasks) do uasyncio.
    player = MusicPlayer(buzzer_pin=config.PINO_BUZZER)
    await start_server(player, port=config.PORTA_SERVIDOR)

    print("Pronto! Abra http://{} no navegador para escolher a musica.".format(ip))

    # A tarefa do player roda em loop infinito, tocando a música
    # pedida pelo usuário ou uma aleatória (se o modo estiver ligado).
    await player.run()


# Ponto de entrada: inicia o loop de eventos do uasyncio.
try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Encerrado pelo usuário.")

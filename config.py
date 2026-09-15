# -*- coding: utf-8 -*-
"""
config.py
=========
Configurações do projeto. EDITE os valores abaixo antes de gravar
no ESP32.
"""

# Nome (SSID) e senha da rede Wi-Fi que o ESP32 deve usar para criar
# a página web (modo "estação", conectando a um roteador existente).
# Só valem se USAR_MODO_ACCESS_POINT (abaixo) estiver False.
WIFI_SSID = "NOME_DA_SUA_REDE"
WIFI_PASSWORD = "SENHA_DA_SUA_REDE"

# Se True, o ESP32 cria sua PRÓPRIA rede Wi-Fi (modo Ponto de Acesso,
# "Access Point") em vez de se conectar a uma rede existente. Assim,
# qualquer celular pode se conectar diretamente na rede do ESP32
# (nome/senha definidos em AP_SSID/AP_PASSWORD, logo abaixo), sem
# precisar de outra rede/roteador por perto — útil em festas, sítios,
# ou qualquer lugar sem Wi-Fi disponível.
#
# Ligado (True) por padrão nesta configuração, para o modo
# "JukeBox" funcionar direto, sem precisar de rede alguma por perto.
# Troque para False se preferir que o ESP32 entre na sua rede Wi-Fi
# de casa em vez de criar a dele própria (nesse caso, preencha
# WIFI_SSID/WIFI_PASSWORD acima).
USAR_MODO_ACCESS_POINT = True

# Nome e senha da rede Wi-Fi criada pelo ESP32, usados apenas se
# USAR_MODO_ACCESS_POINT for True. A senha precisa ter 8+ caracteres
# (exigência do protocolo WPA2, usado aqui) — "S2musica" tem 8.
AP_SSID = "JukeBox"
AP_PASSWORD = "S2musica"

# Pino GPIO onde o buzzer está conectado (mesmo do código original).
PINO_BUZZER = 25

# Porta do servidor web. 80 é a porta padrão (assim o usuário só
# precisa digitar o IP do ESP32 no navegador, sem ":porta" no final).
PORTA_SERVIDOR = 80


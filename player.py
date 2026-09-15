# -*- coding: utf-8 -*-
"""
player.py
=========
Motor de reprodução de música no buzzer, de forma ASSÍNCRONA
(usando uasyncio) para não travar o ESP32 enquanto uma música toca.

Por que assíncrono?
--------------------
No código original, `time.sleep_ms()` bloqueia o processador inteiro
enquanto uma nota está soando. Isso é um problema quando também
queremos rodar um servidor web ao mesmo tempo: se o ESP32 fica
"dormindo" tocando uma nota, ele não consegue responder a pedidos
HTTP do navegador do usuário.

A solução é trocar `time.sleep_ms()` por `await uasyncio.sleep_ms()`.
Isso "cede" o processador para outras tarefas (como o servidor web)
enquanto espera, e retoma a reprodução da nota seguinte depois.

Novidades desta versão
-----------------------
1) Botão "Parar": silencia o buzzer sem escolher outra música.
2) Persistência: a última música tocada, o modo aleatório e o volume
   são salvos em um arquivo (ESTADO_ARQUIVO) e recarregados quando o
   ESP32 liga de novo, então o estado não se perde num reinício.
3) Volume ajustável (0-100), controlado via duty cycle do PWM.
"""

import uasyncio as asyncio
import urandom
import ujson
from machine import Pin, PWM

from songs import SONGS

# Nome do arquivo onde o estado é salvo, na raiz do sistema de
# arquivos do ESP32 (mesmo local dos outros .py do projeto).
ESTADO_ARQUIVO = "estado.json"

# Duty cycle máximo usado quando o volume está em 100%. Em um buzzer
# passivo tocado com onda quadrada, 512 (50% de 1023) é o ponto que
# normalmente soa mais "cheio"/alto. Valores de volume menores usam
# uma fração deste duty. OBS: nem todo hardware de buzzer responde
# de forma perceptível a variações de duty cycle — alguns só têm,
# na prática, "ligado" e "desligado". Ajuste este valor se notar que
# o efeito de volume está diferente do esperado no seu buzzer.
DUTY_MAXIMO = 512


class MusicPlayer:
    """
    Guarda o estado atual do "toca-discos" do ESP32:
      - qual música está tocando agora (ou None se estiver parado)
      - se o modo aleatório está ligado
      - qual música foi pedida pelo usuário (fila de 1 posição)
      - um "pedido de pular" para interromper a música atual na hora
      - um "pedido de parar" (silenciar sem tocar outra coisa)
      - o volume atual (0 a 100)
      - a última música tocada (para restaurar depois de reiniciar)
    """

    def __init__(self, buzzer_pin=25, pwm_freq=1000):
        # Configura o pino do buzzer, igual ao código original.
        self.buzzer = PWM(Pin(buzzer_pin), freq=pwm_freq, duty=0)

        # Nome (chave) da música tocando agora, ou None se parado.
        self.current_key = None

        # Música que o usuário pediu pela página web (fila de 1).
        # O loop principal consome este valor assim que possível.
        self.requested_key = None

        # Quando True, pede para a música atual parar imediatamente
        # (usado tanto ao escolher uma nova música quanto ao apertar
        # o botão "Parar").
        self._skip_requested = False

        # Quando True, o player fica "mudo" de propósito (botão
        # Parar foi apertado) e ignora o modo aleatório até o
        # usuário pedir uma música nova ou reativar o aleatório.
        self._parado_manualmente = False

        # --- Valores com valor padrão, sobrescritos por _carregar_estado() ---
        self.random_mode = False
        self.volume = 70  # 0 a 100
        self.last_played_key = None

        # Restaura o que foi salvo da última vez que o ESP32 rodou
        # (última música, modo aleatório e volume), se existir.
        self._carregar_estado()

        # Se havia uma música tocando quando o ESP32 foi desligado e
        # o modo aleatório estava desligado, retoma essa música ao
        # ligar de novo. Se o modo aleatório estava ligado, deixamos
        # o próprio loop `run()` sortear uma música aleatória.
        if not self.random_mode and self.last_played_key in SONGS:
            self.requested_key = self.last_played_key

    # -----------------------------------------------------------
    # Persistência (salvar/carregar estado em arquivo)
    # -----------------------------------------------------------
    def _carregar_estado(self):
        """Lê estado.json (se existir) e restaura random_mode/volume/última música."""
        try:
            with open(ESTADO_ARQUIVO, "r") as arquivo:
                dados = ujson.load(arquivo)
        except (OSError, ValueError):
            # Arquivo não existe ainda (primeira vez) ou está corrompido:
            # seguimos com os valores padrão, sem travar o programa.
            print("Nenhum estado salvo encontrado, usando padrões.")
            return

        self.random_mode = bool(dados.get("random_mode", False))
        self.volume = int(dados.get("volume", 70))
        self.last_played_key = dados.get("last_song")
        print("Estado restaurado:", dados)

    def _salvar_estado(self):
        """Grava o estado atual em estado.json. Chamado só em mudanças (não a cada nota)."""
        dados = {
            "last_song": self.last_played_key,
            "random_mode": self.random_mode,
            "volume": self.volume,
        }
        try:
            with open(ESTADO_ARQUIVO, "w") as arquivo:
                ujson.dump(dados, arquivo)
        except OSError as erro:
            # Não é crítico se falhar (ex.: pouco espaço na flash);
            # a música continua funcionando normalmente.
            print("Aviso: não foi possível salvar o estado:", erro)

    # -----------------------------------------------------------
    # Métodos chamados pelo servidor web (tarefa HTTP)
    # -----------------------------------------------------------
    def request_song(self, key):
        """Chamado pelo servidor web quando o usuário escolhe uma música."""
        if key not in SONGS:
            return False
        self.requested_key = key
        self._parado_manualmente = False  # escolher música cancela o "parado"
        # Se já tem algo tocando, pede para parar logo para a nova
        # música começar sem esperar a atual terminar.
        if self.current_key is not None:
            self._skip_requested = True
        return True

    def stop(self):
        """
        Chamado pelo servidor web quando o usuário aperta "Parar".
        Silencia o buzzer imediatamente e mantém o player ocioso,
        mesmo que o modo aleatório esteja ligado, até o usuário
        escolher uma música ou reativar o aleatório manualmente.
        """
        self.requested_key = None
        self._parado_manualmente = True
        if self.current_key is not None:
            self._skip_requested = True
        # Silencia na hora (não espera o loop perceber o pedido).
        self.buzzer.duty(0)

    def set_random_mode(self, enabled):
        """Chamado pelo servidor web para ligar/desligar o modo aleatório."""
        self.random_mode = bool(enabled)
        if self.random_mode:
            # Ligar o aleatório manualmente também tira o player do
            # estado "parado", para o modo aleatório voltar a valer.
            self._parado_manualmente = False
        self._salvar_estado()

    def set_volume(self, valor):
        """
        Chamado pelo servidor web para ajustar o volume (0 a 100).
        Valores fora da faixa são "grudados" (clamp) no limite mais
        próximo, em vez de causar erro.
        """
        try:
            valor = int(valor)
        except (TypeError, ValueError):
            return False
        self.volume = max(0, min(100, valor))
        self._salvar_estado()
        return True

    def status(self):
        """Retorna um dicionário simples com o estado atual (para /api/status)."""
        display_name = None
        if self.current_key and self.current_key in SONGS:
            display_name = SONGS[self.current_key][2]
        return {
            "playing_key": self.current_key,
            "playing_name": display_name,
            "random_mode": self.random_mode,
            "volume": self.volume,
            "stopped": self._parado_manualmente and self.current_key is None,
        }

    # -----------------------------------------------------------
    # Motor de reprodução (roda dentro da tarefa assíncrona)
    # -----------------------------------------------------------
    def _duty_atual(self):
        """Calcula o duty cycle (0 a DUTY_MAXIMO) de acordo com o volume atual."""
        return int(DUTY_MAXIMO * self.volume / 100)

    async def _play_song(self, key):
        """
        Toca uma música (bloqueante apenas de forma "cooperativa": usa
        await asyncio.sleep_ms para não travar o servidor web).
        Pode ser interrompida a qualquer momento se _skip_requested
        for marcado como True (nova música escolhida, ou botão Parar).
        """
        melodia, tempo, _nome = SONGS[key]
        # Duração (em ms) de uma semibreve neste tempo (BPM).
        duracao_semibreve = (60000 * 4) / tempo

        tamanho = len(melodia)
        for i in range(0, tamanho, 2):
            # Se o usuário pediu para pular/parar, interrompe a música agora.
            if self._skip_requested:
                break

            nota = melodia[i]
            divisor = melodia[i + 1]

            if divisor > 0:
                duracao_nota = duracao_semibreve / divisor
            else:
                # Duração negativa = nota pontuada (1.5x mais longa).
                duracao_nota = (duracao_semibreve / abs(divisor)) * 1.5

            # Toca a nota, respeitando o volume configurado. O volume
            # é lido a cada nota (não guardado antes do laço) para que
            # uma mudança de volume no meio da música tenha efeito
            # imediato, sem esperar a música atual terminar.
            self.buzzer.freq(int(nota))
            self.buzzer.duty(self._duty_atual())
            await asyncio.sleep_ms(int(duracao_nota))

            # Pequena pausa entre notas (staccato), igual ao original.
            self.buzzer.duty(0)
            await asyncio.sleep_ms(50)

        # Garante que o buzzer fica em silêncio ao final da música.
        self.buzzer.duty(0)

    async def run(self):
        """
        Laço principal do "toca-discos". Deve ser criado como uma
        tarefa (asyncio.create_task) e rodar para sempre em paralelo
        com o servidor web.
        """
        while True:
            # 1) Se o usuário pediu uma música específica, ela tem prioridade.
            if self.requested_key is not None:
                key = self.requested_key
                self.requested_key = None

            # 2) Senão, se o modo aleatório estiver ligado E o usuário não
            #    tiver apertado "Parar" manualmente, sorteia uma música.
            elif self.random_mode and not self._parado_manualmente:
                chaves = list(SONGS.keys())
                indice = urandom.getrandbits(16) % len(chaves)
                key = chaves[indice]

            # 3) Senão, fica ocioso, checando periodicamente por pedidos novos.
            else:
                self.current_key = None
                await asyncio.sleep_ms(200)
                continue

            # IMPORTANTE: zera o pedido de pular/parar aqui, depois de já
            # termos decidido qual música vai tocar. Se isso ficasse só no
            # ramo "1" acima, uma música escolhida pelo modo aleatório
            # herdaria um _skip_requested=True deixado por um stop()
            # anterior e seria interrompida antes mesmo da primeira nota.
            self._skip_requested = False

            # Toca a música escolhida.
            self.current_key = key
            self.last_played_key = key
            self._salvar_estado()  # salva "qual foi a última música" só ao começar a tocar
            await self._play_song(key)
            self.current_key = None

            # Pequena pausa entre uma música e outra.
            await asyncio.sleep_ms(300)

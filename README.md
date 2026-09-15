# Caixa-de-Musicas-ESP32
Programa feito para emular um JukeBox com várias músicas em formatos polifônicos.

## Como usar
* Edite config.py:
- Preencha WIFI_SSID e WIFI_PASSWORD com os dados da sua rede.
- Ou defina USAR_MODO_ACCESS_POINT = True para o ESP32 criar sua própria rede Wi-Fi (útil sem roteador disponível).
- Confira PINO_BUZZER (padrão: GPIO 23, igual ao original).
* Copie os 5 arquivos (songs.py, player.py, web_server.py, config.py, main.py) para a raiz do sistema de arquivos do ESP32 (por exemplo, usando mpremote, ampy ou o Thonny).
* Ligue o ESP32. Observe no console serial a mensagem com o IP (algo como Conectado! Acesse a caixa de música em: http://192.168.0.42).
* Abra esse endereço no navegador de um celular/computador conectado à mesma rede.

## Músicas
    "asabranca":          ("Asa Branca - Luiz Gonzaga"),
    "passodoelefantinho": ("Baby Elephant Walk"),
    "bloodytears":        ("Bloody Tears (Castlevania II)"),
    "nananenem":          ("Ninar (Wiegenlied - Brahms)"),
    "bandadacantina":     ("Banda da Cantina (Star Wars)"),
    "furelise":           ("Fur Elise - Beethoven"),
    "gameofthrones":      ("Game of Thrones"),
    "greensleeves":       ("Greensleeves"),
    "parabens":           ("Parabens pra Voce"),
    "imperial":           ("Marcha Imperial (Star Wars)"),
    "starwars":           ("Star Wars - Tema Principal"),
    "harrypotter":        ("Harry Potter - Tema de Hedwig"),
    "songofstorms":       ("Song of Storms (Zelda)"),
    "tetris":             ("Tetris"),
    "zeldalullaby":       ("Cancao de Ninar de Zelda"),
    "merry":              ("We Wish You a Merry Christmas"),
    "minuet":             ("Minueto em Sol - Petzold"),
    "nevergonna":         ("Never Gonna Give You Up"),
    "ode":                ("Ode a Alegria - Beethoven"),
    "pacman":             ("Pac-Man"),
    "princeigor":         ("Principe Igor - Borodin"),
    "silentnight":        ("Noite Feliz"),
    "startrek":           ("Abertura de Star Trek"),
    "badinerie":          ("Badinerie - Bach"),
    "godfather":          ("Tema do Poderoso Chefao"),
    "thelionsleep":       ("The Lion Sleeps Tonight"),
    "jigglypuff":         ("Musica do Jigglypuff"),
    "pulodagaita":        ("Pulo da Gaita - Auto da Compadecida"),
    "mariobros":          ("Super Mario Bros - Tema"),
    "cannon":             ("Canone em Re - Pachelbel"),
    "takeonme":           ("Take On Me - A-ha"),
    "pantera":            ("Tema da Pantera Cor-de-Rosa"),

    # --- Musicas convertidas de RTTTL ---
    "thesimpsons":        ("Os Simpsons - Tema"),
    "indiana":            ("Indiana Jones - Tema"),
    "entertainer":        ("The Entertainer - Scott Joplin"),
    "muppets":            ("Os Muppets - Tema"),
    "xfiles":             ("Arquivo X - Tema"),
    "looney":             ("Looney Tunes - Tema"),
    "m20thcenfox":        ("20th Century Fox - Fanfarra"),
    "bond":               ("James Bond - Tema 007"),
    "mash":               ("Tema de MASH"),
    "goodbad":            ("Three Amigos (O Bom, o Mau e o Feio)"),
    "topgun":             ("Top Gun - Tema"),
    "ateam":              ("A-Team (Esquadrao Classe A)"),
    "flinstones":         ("Os Flintstones - Tema"),
    "jeopardy":           ("Jeopardy - Tema de Espera"),
    "gadget":             ("Inspetor Bugiganga - Tema"),
    "smurfs":             ("Os Smurfs - Tema"),
    "mahnamahna":         ("Mahna Mahna (Muppets)"),
    "leisuresuit":        ("Leisure Suit Larry - Tema"),
    "missionimp":         ("Missao Impossivel - Tema"),
    "smb":                ("Super Mario Bros (RTTTL)"),
    "smbundergr":         ("Super Mario Bros - Subsolo"),
    "smbwater":           ("Super Mario Bros - Fase Aquatica"),
    "smbdeath":           ("Super Mario Bros - Morte do Personagem"),

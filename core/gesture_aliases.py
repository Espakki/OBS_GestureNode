# Mapeamento canônico: código interno do detector → nome de exibição
# Fonte única de verdade — importado por gesture_detector, gesture_engine, main_window
GESTURE_ALIASES = {
    # Gestos com código UPPER_SNAKE_CASE
    "THUMBS_UP": "Joinha",
    "THUMBS_DOWN": "Deslike",
    "OPEN_HAND": "Mão aberta",
    "FIST": "Punho",
    "POINT": "Apontando p/ cima",
    "ROCK": "Rock",
    "THREE": "Três",
    "FOUR": "Quatro",
    "OK_SIGN": "OK",
    "CALL_ME": "Me liga",
    # Gestos cujo código já é o nome de exibição (passthrough)
    "V": "V",
    "Escoteiro": "Escoteiro",
    "Dedo do Meio": "Dedo do Meio",
    "Arminha": "Arminha",
}

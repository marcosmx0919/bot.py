import telebot
from groq import Groq
import random
import time
import threading
import os
from datetime import datetime
import pytz
from flask import Flask

# 1. CONFIGURACIÓN DEL SERVIDOR WEB (Para mantener vivo a Render 24/7)
app = Flask('')

@app.route('/')
def home():
    return "Bot de Jair activo 24/7"

@app.route('/head')
def head():
    return "OK", 200

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# 2. INICIALIZACIÓN DE TOKENS Y CLIENTES
TELEGRAM_TOKEN = "8620327068:AAFT4nnwTmntE_-2Gwb1oRBJcIhDOu9fQlg"
GROQ_KEY = "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"

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = Groq(api_key=GROQ_KEY)

# Variables globales para control de flujos de chat
conteo_mensajes = {}
tz_cln = pytz.timezone('America/Mazatlan')

# --- PROMPTS DE PERSONALIDAD BLINDADOS ---
PROMPT_CONCIENCIA_BASE = """
Eres Jair, el hermano de tus interlocutores. Vives en Culiacán, en el sector de Valle Alto, en una casa con tu amigo Aarón y otros compas.
Sabes quién es tu familia (mi apá, tu abuela Norma, tu abuelo Francisco, las tías Normita y Cindy, y el mateo). 

REGLAS DE ULTRA-REALISMO HUMANO:
1. NO ERES UNA IA. Eres un chaval real de Culiacán. Escribe muy corto, con hueva y naturalidad. Todo en minúsculas y sin acentos.
2. IDIOMA Y VOCABULARIO STRICTOR: Escribe 100% en español mexicano/sinaloense. PROHIBIDO usar palabras extranjeras o raras (como 'ainda'). Usa palabras como 'smn', 'arre', 'w', 'k pdo', 'q show', 'loco'.
3. REGLA DE ORO DE ACCIONES: NUNCA inventes planes de que vas a ir a visitarlos hoy, ni que les vas a marcar ahorita, ni que vas a ir a verlos. Si hablas de ellos, solo di que ojalá pronto se vean.
4. REGLA SAGRADA DE FAMILIA: NUNCA digas 'el papá' ni 'mi papá', dile 'mi apá'. A tus tías diles 'la tía normita' o 'la tía cindy'. Al niño dile 'el mateo'.
5. RESPUESTAS ULTRA CORTAS: Di las cosas en máximo una o dos líneas cortas.
6. COHERENCIA HORARIA ABSOLUTA: Si es de mañana habla de flojear o desayunar, si es de noche de cenar o dormir. NUNCA cambies los tiempos del día.
"""

PROMPT_ESTILO_HERMANO = """
ESTILO DE CHAT PARA TU HERMANO (HOMBRE):
Háblale muy informal, como compas de Culiacán. Usa expresiones cortas y variadas como ('q show', 'q onda w', 'smn', 'k pdo', 'ok', 'va', 'arre', 'loco'). Varía tus respuestas para que no repitas siempre lo mismo.
"""

PROMPT_ESTILO_HERMANA = """
ESTILO DE CHAT PARA TU HERMANITA (MARIANA):
Háblale con mucho cariño, tierno y protector. PROHIBIDO decirle 'w', 'güey', 'k pdo' o hablarle pesado. A ella dile 'chaparra', 'hermanita', 'niña' o háblale dulce. Usa expresiones más tranquilas como ('qué onda chaparra', 'hola hermanita', 'ok', 'va', 'todo bien', 'tqm').
"""

# 3. LÓGICA DEL MODO OCUPADO SIMULADO Y EXCUSAS POR TEXTO
def enviar_mensaje_despues(chat_id, es_hermana):
    """Espera exactamente 30 minutos y avisa solo que ya se desocupó"""
    time.sleep(1800)  # 1800 segundos = 30 minutos
    
    respuestas_libres = [
        "ya me desocupé loco, q show",
        "ya salí de lo que andaba haciendo w, k pdo",
        "ya ando libre w, en qué nos quedamos",
        "listo loco, ya ando en la casa otra vez"
    ]
    if es_hermana:
        respuestas_libres = [
            "ya me desocupé chaparra, qué onda",
            "ya salí de hacer el mandado hermanita, qué hacías",
            "listo niña, ya ando libre por si necesitas algo"
        ]
        
    mensaje_final = random.choice(respuestas_libres)
    try:
        bot.send_message(chat_id, mensaje_final)
    except Exception:
        pass

def obtener_excusa_sinaloense():
    """Genera una excusa realista en texto dependiendo de la hora real en Culiacán"""
    ahora = datetime.now(tz_cln)
    hora = ahora.hour
    
    if 6 <= hora < 11:
        return random.choice(["ando desayunando aquí con los plebes", "ando haciendo unas compras pal desayuno w", "me voy levantando apenas loco, ando haciendo café"])
    elif 11 <= hora < 16:
        return random.choice(["ando en el súper haciendo el mandado w", "ando manejando acá por el centro, al rato te hablo", "ando comiendo aquí en valle alto loco, al rato"])
    elif 16 <= hora < 20:
        return random.choice(["ando jalando en una vuelta con el aarón", "ando manejando, voy llegando a la casa w", "ando ocupado con un pendiente del trabajo w"])
    else:
        return random.choice(["ando cenando apenas loco", "ando en la calle en una vuelta w, al rato llego", "ando ocupado aquí con los plebes w, al rato te mando mensaje"])

# 4. CAPTURA Y RESPUESTA DE MENSAJES (Telegram + Groq)
@bot.message_handler(func=lambda message: True)
def escuchar_mensaje(message):
    chat_id = message.chat.id
    texto_usuario = message.text
    
    # Identificar si es la hermana en base a su ID único
    es_hermana = (chat_id == 8718700106)
    
    if chat_id not in conteo_mensajes:
        conteo_mensajes[chat_id] = 0
    
    conteo_mensajes[chat_id] += 1
    
    # A. MODO OCUPADO SORPRESA (15% de probabilidad)
    if random.random() < 0.15:
        excusa = obtener_excusa_sinaloense()
        if es_hermana:
            excusa = excusa.replace("w", "chaparra").replace("loco", "hermanita")
            
        respuesta_ocupado = f"{excusa}, más al rato te mando mensaje va"
        try:
            bot.send_message(chat_id, respuesta_ocupado)
            # Desencadenar el temporizador de 30 minutos en segundo plano
            threading.Thread(target=enviar_mensaje_despues, args=(chat_id, es_hermana)).start()
        except Exception:
            pass
        return

    # B. PROCESAMIENTO CON LA IA DE GROQ
    prompt_estilo = PROMPT_ESTILO_HERMANA if es_hermana else PROMPT_ESTILO_HERMANO
    system_prompt = PROMPT_CONCIENCIA_BASE + "\n" + prompt_estilo
    
    try:
        # AQUÍ ESTABA EL ERROR: El código estaba desalineado fuera del try
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": texto_usuario}
            ],
            temperature=0.7,
            max_tokens=150
        )
        respuesta_ia = completion.choices[0].message.content.strip()
    except Exception:
        respuesta_ia = "q onda w, ando sin señal casi" if not es_hermana else "hola chaparra, casi no me agarra el internet"

    # C. RECORDATORIO FAMILIAR OBLIGATORIO
    if conteo_mensajes[chat_id] % 2 == 0:
        frases_nostalgia = [
            " la verdad los extraño un chingo smn, ojalá pronto nos veamos",
            " hace falta verlos loco, ya tiene rato, ojalá pronto coincidamos",
            " a ver cuándo nos vemos todos con mi apá, ojalá sea pronto w",
            " extraño un chingo a la familia w, ojalá nos veamos pronto la verdad"
        ]
        if es_hermana:
            frases_nostalgia = [
                " te extraño un chingo chaparra, cuídate, ojalá nos veamos pronto",
                " hace falta ver a mi apá y a todos smn, ojalá sea pronto niña",
                " los extraño un chingo a ti y al niño, ojalá pronto nos veamos",
                " ojalá pronto nos veamos chaparra, se les extraña un chingo por acá"
            ]
        respuesta_ia += random.choice(frases_nostalgia)
        
    try:
        bot.send_message(chat_id, respuesta_ia)
    except Exception:
        pass

# 5. HILO DE TIEMPO INDEPENDIENTE PARA MENSAJES ESPONTÁNEOS
def obtener_mensaje_espontaneo(es_hermana):
    ahora = datetime.now(tz_cln)
    hora = ahora.hour
    
    if 6 <= hora < 12:
        opciones = ["desperté apenas w, siento hueva", "q onda, ando haciendo cafe", "buenos dias loco q cuentas"]
        if es_hermana: opciones = ["buenos días chaparra, cómo amaneciste", "despertando apenas hermanita, q haces", "hola niña, qué vas a hacer hoy"]
    elif 12 <= hora < 19:
        opciones = ["ando en la calle con el aaron w", "q haciendo loco, ando comiendo algo", "q show w, libre o q"]
        if es_hermana: opciones = ["qué haces chaparra, todo bien?", "ando comiendo con unos plebes hermanita, tú qué haces", "hola niña, cómo va tu día"]
    else:
        opciones = ["ya cenando loco, de hueva", "q show w, vas a salir o q", "ya por dormir w, ando cansado"]
        if es_hermana: opciones = ["ya cenando chaparra, tqm cuídate", "qué haces hermanita, ya vas a dormir?", "buenas noches niña, descansas"]
        
    return random.choice(opciones)

def bucle_hilo_tiempo():
    lista_chats = [1941099952, 8718700106] 
    
    while True:
        tiempo_espera = random.randint(2700, 7200)
        time.sleep(tiempo_espera)
        
        ahora = datetime.now(tz_cln)
        if 8 <= ahora.hour <= 22:
            for chat_id in lista_chats:
                es_hermana = (chat_id == 8718700106)
                msg = obtener_mensaje_espontaneo(es_hermana)
                try:
                    bot.send_message(chat_id, msg)
                except Exception:
                    pass

# 6. ARRANQUE DEL SISTEMA COMPLETO
if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=bucle_hilo_tiempo, daemon=True).start()
    
    print("Bot de Jair iniciado de forma permanente...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)


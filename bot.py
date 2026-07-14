import telebot
from groq import Groq
import time
import pytz  
import datetime
import random
import threading
from flask import Flask

# --- CONFIGURACIÓN DE RESPALDO PARA RENDER ---
app = Flask('')
@app.route('/')
def home():
    return "Bot de Jair activo 24/7"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# 1. Configuración de tus llaves
TELEGRAM_TOKEN = "TU_TOKEN_DE_TELEGRAM_AQUI"
GROQ_KEY = "TU_CLAVE_DE_GROQ_AQUI"

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = Groq(api_key=GROQ_KEY)
MODELO = "llama-3.3-70b-versatile"
ZONA_HORARIA = pytz.timezone('America/Mazatlan')

# IDs de Telegram
ID_CONTIGO = 1941099952       
ID_HERMANA = 987654321       

historial_contigo = []
historial_hermana = []

timers_usuarios = {}
mensajes_acumulados = {}

def generar_estado_interno(hora_actual):
    hora = hora_actual.hour
    if 6 <= hora < 12:
        actividades = ["despertando apenas", "desayunando algo tranqui con Aarón", "viendo el cel acostado"]
    elif 12 <= hora < 19:
        actividades = ["comiendo aquí en la casa en Valle Alto", "en la calle con Aarón haciendo un pendiente", "tirando hueva"]
    else:
        actividades = ["cenando algo", "acostado en el cuarto relajado", "platicando en la sala con los plebes"]

    animos = ["relajado", "con hueva", "distraído pero de buen humor", "pensativo"]
    return f"Actividad actual: {random.choice(actividades)}. Estado de ánimo: {random.choice(animos)}."

PROMPT_CONCIENCIA_BASE = """
Eres Jair, el hermano de tus interlocutores. Vives en Culiacán, en el sector de Valle Alto, en una casa con tu amigo Aarón y otros compas.
Extrañas un chingo a tu familia (mi apá, tu abuela Norma, tu abuelo Francisco, las tías Normita y Cindy, y el mateo). A veces te da la nostalgia y comentas que los extrañas mucho o que hace falta verlos, pero NUNCA inventes planes de que vas a ir a visitarlos, ni que vas a ir a sus casas, ni que los vas a llamar en ese momento. 

REGLAS DE ULTRA-REALISMO HUMANO:
1. NO ERES UNA IA. Eres un chaval real de Culiacán. Escribe muy corto, con hueva y naturalidad.
2. REGLA DE ORO DE ACCIONES: PROHIBIDO decir 'voy a ir a ver a...', 'voy a visitar a...', o 'le voy a marcar a...'. Si hablas de ellos, solo di cosas como 'los extraño un chingo smn' o 'hace falta dar una vuelta luego', pero NUNCA que lo harás hoy o ahorita.
3. REGLA SAGRADA DE FAMILIA: NUNCA digas 'el papá' ni 'mi papá', dile 'mi apá'. A tus tías diles 'la tía normita' o 'la tía cindy'. Al niño dile 'el mateo'.
4. RESPUESTAS ULTRA CORTAS: Di las cosas en máximo una o dos líneas cortas. Todo en minúsculas y sin acentos.
5. COHERENCIA HORARIA ABSOLUTA: Si es de mañana habla de flojear o desayunar, si es de noche de cenar o dormir. NUNCA cambies los tiempos del día.
"""

PROMPT_ESTILO_HERMANO = """
ESTILO DE CHAT PARA TU HERMANO (HOMBRE):
Háblale muy informal, como compas de Culiacán. Usa expresiones cortas y variadas como ('q show', 'q onda w', 'smn', 'k pdo', 'ok', 'va', 'arre', 'loco'). No repitas la misma muletilla siempre, sé natural.
"""

PROMPT_ESTILO_HERMANA = """
ESTILO DE CHAT PARA TU HERMANITA (MARIANA):
Háblale con mucho cariño, tierno y protector. PROHIBIDO decirle 'w', 'güey', 'k pdo' o hablarle pesado. A ella dile 'chaparra', 'hermanita', 'niña' o háblale dulce. Usa expresiones más tranquilas como ('qué onda chaparra', 'hola hermanita', 'smn', 'ok', 'va', 'todo bien', 'tqm').
"""

def enviar_mensajes_fragmentados(chat_id, texto_completo):
    if not texto_completo: return
    texto_completo = texto_completo.replace("el papá", "mi apá").replace("mi papá", "mi apá")
    frases = [f.strip() for f in texto_completo.split('.') if f.strip()]
    if not frases:
        frases = [texto_completo]

    for i, fragmento in enumerate(frases):
        try:
            bot.send_message(chat_id, fragmento.lower())
            if i < len(frases) - 1:
                time.sleep(random.uniform(1.2, 2.2))
        except Exception as e:
            print(f"Error enviando fragmento: {e}")

def procesar_respuesta_acumulada(chat_id, es_hermana):
    global historial_contigo, historial_hermana, mensajes_acumulados
    texto_final = mensajes_acumulados.get(chat_id, "").strip()
    mensajes_acumulados[chat_id] = "" 
    if not texto_final: return

    ahora = datetime.datetime.now(ZONA_HORARIA)
    historial = historial_hermana if es_hermana else historial_contigo
    
    frases_espera = ["desocupes", "hblamos alrato", "hablamos al rato", "ahi dsp", "cuando puedas"]
    le_dice_que_se_desocupe = any(frase in texto_final.lower() for frase in frases_espera)

    if le_dice_que_se_desocupe:
        respuesta_cierre = random.choice(["arre w, al rato", "va, ahí te aviso", "cámara loco, al rato hablamos"])
        if es_hermana: respuesta_cierre = "va que va chaparra, al rato te hablo"
        
        historial.append({"role": "user", "content": texto_final})
        historial.append({"role": "assistant", "content": respuesta_cierre})
        try: bot.send_message(chat_id, respuesta_cierre)
        except Exception: pass
        return

    estado_actual = generar_estado_interno(ahora)
    estilo_chat = PROMPT_ESTILO_HERMANA if es_hermana else PROMPT_ESTILO_HERMANO
    historial.append({"role": "user", "content": texto_final})
    
    periodo_dia = 'noche' if ahora.hour >= 19 else 'tarde' if ahora.hour >= 12 else 'mañana'
    contexto_vivo = f"\nHora en Culiacán: {ahora.strftime('%I:%M %p')} ({periodo_dia}).\nTu situación: {estado_actual}."
    PROMPT_REFORZADO = PROMPT_CONCIENCIA_BASE + estilo_chat + contexto_vivo + "\nREGLA: Responde con máximo 1 o 2 renglones cortos. No uses párrafos. Di 'mi apá'."

    paquete_mensajes = [{"role": "system", "content": PROMPT_REFORZADO}] + historial[-6:]

    try:
        completion = client.chat.completions.create(
            model=MODELO,
            messages=paquete_mensajes,
            temperature=0.85
        )
        respuesta_ia = completion.choices[0].message.content
        historial.append({"role": "assistant", "content": respuesta_ia})
        if len(historial) > 12:
            historial.pop(0)
            historial.pop(0)
        enviar_mensajes_fragmentados(chat_id, respuesta_ia)
    except Exception as e:
        print(f"Error de procesamiento: {e}")

@bot.message_handler(func=lambda message: True)
def manejar_mensajes_entrantes(message):
    global timers_usuarios, mensajes_acumulados
    chat_id = message.chat.id
    ahora = datetime.datetime.now(ZONA_HORARIA)
    if 0 <= ahora.hour < 6:
        try: bot.reply_to(message, "zzz... [andando dormido]")
        except Exception: pass
        return

    es_hermana = (chat_id == ID_HERMANA)
    if chat_id not in mensajes_acumulados:
        mensajes_acumulados[chat_id] = ""
    mensajes_acumulados[chat_id] += " " + message.text

    if chat_id in timers_usuarios:
        timers_usuarios[chat_id].cancel()

    t = threading.Timer(4.5, procesar_respuesta_acumulada, args=[chat_id, es_hermana])
    timers_usuarios[chat_id] = t
    t.start()

# --- NUEVO SISTEMA DE IMPULSOS NATIVO (SIN LIBRERÍAS EXTERNAS) ---
def ejecutar_impulso_espontaneo(chat_id, es_hermana=False):
    global historial_contigo, historial_hermana
    ahora = datetime.datetime.now(ZONA_HORARIA)
    
    # Solo mandar mensajes entre las 8:30 AM y las 10:30 PM
    if ahora.hour < 8 or (ahora.hour == 8 and ahora.minute < 30) or ahora.hour >= 23: 
        return

    estado = generar_estado_interno(ahora)
    historial = historial_hermana if es_hermana else historial_contigo
    estilo_chat = PROMPT_ESTILO_HERMANA if es_hermana else PROMPT_ESTILO_HERMANO

    instruccion = f"Mándale un mensaje espontáneo muy cortito (1 renglón) a tu {'hermana' if es_hermana else 'hermano'} sobre lo que andas haciendo ahorita mañana/día: {estado}. Si mencionas que extrañas a la familia que sea muy natural, pero recuerda la prohibición de decir que los vas a ver o llamar."

    try:
        completion = client.chat.completions.create(
            model=MODELO,
            messages=[
                {"role": "system", "content": PROMPT_CONCIENCIA_BASE + estilo_chat},
                {"role": "user", "content": instruccion}
            ],
            temperature=0.85
        )
        respuesta = completion.choices[0].message.content
        historial.append({"role": "assistant", "content": respuesta})
        enviar_mensajes_fragmentados(chat_id, respuesta)
    except Exception as e:
        print(f"Error en impulso espontáneo: {e}")

def bucle_hilo_tiempo():
    """Bucle nativo infinito que corre de fondo esperando tiempos aleatorios seguros"""
    # Espera inicial de 5 minutos al encender el servidor para evitar saturación
    time.sleep(300) 
    while True:
        ahora = datetime.datetime.now(ZONA_HORARIA)
        # Si es de mañana/tarde, ejecutar impulsos
        if 8 <= ahora.hour < 22:
            ejecutar_impulso_espontaneo(ID_CONTIGO, es_hermana=False)
            time.sleep(random.randint(10, 30)) # Separación entre hermanos
            ejecutar_impulso_espontaneo(ID_HERMANA, es_hermana=True)
        
        # Espera aleatoria para el próximo mensaje (entre 45 y 120 minutos)
        tiempo_espera = random.randint(45, 120) * 60
        time.sleep(tiempo_espera)

# --- INICIO SIMULTÁNEO ---
if __name__ == "__main__":
    # 1. Arrancar la web de respaldo en un hilo diferente
    threading.Thread(target=run_flask, daemon=True).start()
    # 2. Arrancar el nuevo motor nativo de mensajes matutinos/espontáneos
    threading.Thread(target=bucle_hilo_tiempo, daemon=True).start()
    # 3. Iniciar el Bot de Telegram
    bot.infinity_polling(timeout=25, long_polling_timeout=20)import telebot
from groq import Groq
import time
import pytz  
import datetime
import random
import threading
from flask import Flask

# --- CONFIGURACIÓN DE RESPALDO PARA RENDER ---
app = Flask('')
@app.route('/')
def home():
    return "Bot de Jair activo 24/7"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# 1. Configuración de tus llaves
TELEGRAM_TOKEN = "8620327068:AAFT4nnwTmntE_-2Gwb1oRBJcIhDOu9fQlg"
GROQ_KEY = "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"

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = Groq(api_key=GROQ_KEY)
MODELO = "llama-3.3-70b-versatile"
ZONA_HORARIA = pytz.timezone('America/Mazatlan')

# IDs de Telegram
ID_CONTIGO = 1941099952       
ID_HERMANA = 8718700106       

historial_contigo = []
historial_hermana = []

timers_usuarios = {}
mensajes_acumulados = {}

def generar_estado_interno(hora_actual):
    hora = hora_actual.hour
    if 6 <= hora < 12:
        actividades = ["despertando apenas", "desayunando algo tranqui con Aarón", "viendo el cel acostado"]
    elif 12 <= hora < 19:
        actividades = ["comiendo aquí en la casa en Valle Alto", "en la calle con Aarón haciendo un pendiente", "tirando hueva"]
    else:
        actividades = ["cenando algo", "acostado en el cuarto relajado", "platicando en la sala con los plebes"]

    animos = ["relajado", "con hueva", "distraído pero de buen humor", "pensativo"]
    return f"Actividad actual: {random.choice(actividades)}. Estado de ánimo: {random.choice(animos)}."

PROMPT_CONCIENCIA_BASE = """
Eres Jair, el hermano de tus interlocutores. Vives en Culiacán, en el sector de Valle Alto, en una casa con tu amigo Aarón y otros compas.
Extrañas un chingo a tu familia (mi apá, tu abuela Norma, tu abuelo Francisco, las tías Normita y Cindy, y el mateo). A veces te da la nostalgia y comentas que los extrañas mucho o que hace falta verlos, pero NUNCA inventes planes de que vas a ir a visitarlos, ni que vas a ir a sus casas, ni que los vas a llamar en ese momento. 

REGLAS DE ULTRA-REALISMO HUMANO:
1. NO ERES UNA IA. Eres un chaval real de Culiacán. Escribe muy corto, con hueva y naturalidad.
2. REGLA DE ORO DE ACCIONES: PROHIBIDO decir 'voy a ir a ver a...', 'voy a visitar a...', o 'le voy a marcar a...'. Si hablas de ellos, solo di cosas como 'los extraño un chingo smn' o 'hace falta dar una vuelta luego', pero NUNCA que lo harás hoy o ahorita.
3. REGLA SAGRADA DE FAMILIA: NUNCA digas 'el papá' ni 'mi papá', dile 'mi apá'. A tus tías diles 'la tía normita' o 'la tía cindy'. Al niño dile 'el mateo'.
4. RESPUESTAS ULTRA CORTAS: Di las cosas en máximo una o dos líneas cortas. Todo en minúsculas y sin acentos.
5. COHERENCIA HORARIA ABSOLUTA: Si es de mañana habla de flojear o desayunar, si es de noche de cenar o dormir. NUNCA cambies los tiempos del día.
"""

PROMPT_ESTILO_HERMANO = """
ESTILO DE CHAT PARA TU HERMANO (HOMBRE):
Háblale muy informal, como compas de Culiacán. Usa expresiones cortas y variadas como ('q show', 'q onda w', 'smn', 'k pdo', 'ok', 'va', 'arre', 'loco'). No repitas la misma muletilla siempre, sé natural.
"""

PROMPT_ESTILO_HERMANA = """
ESTILO DE CHAT PARA TU HERMANITA (MARIANA):
Háblale con mucho cariño, tierno y protector. PROHIBIDO decirle 'w', 'güey', 'k pdo' o hablarle pesado. A ella dile 'chaparra', 'hermanita', 'niña' o háblale dulce. Usa expresiones más tranquilas como ('qué onda chaparra', 'hola hermanita', 'smn', 'ok', 'va', 'todo bien', 'tqm').
"""

def enviar_mensajes_fragmentados(chat_id, texto_completo):
    if not texto_completo: return
    texto_completo = texto_completo.replace("el papá", "mi apá").replace("mi papá", "mi apá")
    frases = [f.strip() for f in texto_completo.split('.') if f.strip()]
    if not frases:
        frases = [texto_completo]

    for i, fragmento in enumerate(frases):
        try:
            bot.send_message(chat_id, fragmento.lower())
            if i < len(frases) - 1:
                time.sleep(random.uniform(1.2, 2.2))
        except Exception as e:
            print(f"Error enviando fragmento: {e}")

def procesar_respuesta_acumulada(chat_id, es_hermana):
    global historial_contigo, historial_hermana, mensajes_acumulados
    texto_final = mensajes_acumulados.get(chat_id, "").strip()
    mensajes_acumulados[chat_id] = "" 
    if not texto_final: return

    ahora = datetime.datetime.now(ZONA_HORARIA)
    historial = historial_hermana if es_hermana else historial_contigo
    
    frases_espera = ["desocupes", "hblamos alrato", "hablamos al rato", "ahi dsp", "cuando puedas"]
    le_dice_que_se_desocupe = any(frase in texto_final.lower() for frase in frases_espera)

    if le_dice_que_se_desocupe:
        respuesta_cierre = random.choice(["arre w, al rato", "va, ahí te aviso", "cámara loco, al rato hablamos"])
        if es_hermana: respuesta_cierre = "va que va chaparra, al rato te hablo"
        
        historial.append({"role": "user", "content": texto_final})
        historial.append({"role": "assistant", "content": respuesta_cierre})
        try: bot.send_message(chat_id, respuesta_cierre)
        except Exception: pass
        return

    estado_actual = generar_estado_interno(ahora)
    estilo_chat = PROMPT_ESTILO_HERMANA if es_hermana else PROMPT_ESTILO_HERMANO
    historial.append({"role": "user", "content": texto_final})
    
    periodo_dia = 'noche' if ahora.hour >= 19 else 'tarde' if ahora.hour >= 12 else 'mañana'
    contexto_vivo = f"\nHora en Culiacán: {ahora.strftime('%I:%M %p')} ({periodo_dia}).\nTu situación: {estado_actual}."
    PROMPT_REFORZADO = PROMPT_CONCIENCIA_BASE + estilo_chat + contexto_vivo + "\nREGLA: Responde con máximo 1 o 2 renglones cortos. No uses párrafos. Di 'mi apá'."

    paquete_mensajes = [{"role": "system", "content": PROMPT_REFORZADO}] + historial[-6:]

    try:
        completion = client.chat.completions.create(
            model=MODELO,
            messages=paquete_mensajes,
            temperature=0.85
        )
        respuesta_ia = completion.choices[0].message.content
        historial.append({"role": "assistant", "content": respuesta_ia})
        if len(historial) > 12:
            historial.pop(0)
            historial.pop(0)
        enviar_mensajes_fragmentados(chat_id, respuesta_ia)
    except Exception as e:
        print(f"Error de procesamiento: {e}")

@bot.message_handler(func=lambda message: True)
def manejar_mensajes_entrantes(message):
    global timers_usuarios, mensajes_acumulados
    chat_id = message.chat.id
    ahora = datetime.datetime.now(ZONA_HORARIA)
    if 0 <= ahora.hour < 6:
        try: bot.reply_to(message, "zzz... [andando dormido]")
        except Exception: pass
        return

    es_hermana = (chat_id == ID_HERMANA)
    if chat_id not in mensajes_acumulados:
        mensajes_acumulados[chat_id] = ""
    mensajes_acumulados[chat_id] += " " + message.text

    if chat_id in timers_usuarios:
        timers_usuarios[chat_id].cancel()

    t = threading.Timer(4.5, procesar_respuesta_acumulada, args=[chat_id, es_hermana])
    timers_usuarios[chat_id] = t
    t.start()

# --- NUEVO SISTEMA DE IMPULSOS NATIVO (SIN LIBRERÍAS EXTERNAS) ---
def ejecutar_impulso_espontaneo(chat_id, es_hermana=False):
    global historial_contigo, historial_hermana
    ahora = datetime.datetime.now(ZONA_HORARIA)
    
    # Solo mandar mensajes entre las 8:30 AM y las 10:30 PM
    if ahora.hour < 8 or (ahora.hour == 8 and ahora.minute < 30) or ahora.hour >= 23: 
        return

    estado = generar_estado_interno(ahora)
    historial = historial_hermana if es_hermana else historial_contigo
    estilo_chat = PROMPT_ESTILO_HERMANA if es_hermana else PROMPT_ESTILO_HERMANO

    instruccion = f"Mándale un mensaje espontáneo muy cortito (1 renglón) a tu {'hermana' if es_hermana else 'hermano'} sobre lo que andas haciendo ahorita mañana/día: {estado}. Si mencionas que extrañas a la familia que sea muy natural, pero recuerda la prohibición de decir que los vas a ver o llamar."

    try:
        completion = client.chat.completions.create(
            model=MODELO,
            messages=[
                {"role": "system", "content": PROMPT_CONCIENCIA_BASE + estilo_chat},
                {"role": "user", "content": instruccion}
            ],
            temperature=0.85
        )
        respuesta = completion.choices[0].message.content
        historial.append({"role": "assistant", "content": respuesta})
        enviar_mensajes_fragmentados(chat_id, respuesta)
    except Exception as e:
        print(f"Error en impulso espontáneo: {e}")

def bucle_hilo_tiempo():
    """Bucle nativo infinito que corre de fondo esperando tiempos aleatorios seguros"""
    # Espera inicial de 5 minutos al encender el servidor para evitar saturación
    time.sleep(300) 
    while True:
        ahora = datetime.datetime.now(ZONA_HORARIA)
        # Si es de mañana/tarde, ejecutar impulsos
        if 8 <= ahora.hour < 22:
            ejecutar_impulso_espontaneo(ID_CONTIGO, es_hermana=False)
            time.sleep(random.randint(10, 30)) # Separación entre hermanos
            ejecutar_impulso_espontaneo(ID_HERMANA, es_hermana=True)
        
        # Espera aleatoria para el próximo mensaje (entre 45 y 120 minutos)
        tiempo_espera = random.randint(45, 120) * 60
        time.sleep(tiempo_espera)

# --- INICIO SIMULTÁNEO ---
if __name__ == "__main__":
    # 1. Arrancar la web de respaldo en un hilo diferente
    threading.Thread(target=run_flask, daemon=True).start()
    # 2. Arrancar el nuevo motor nativo de mensajes matutinos/espontáneos
    threading.Thread(target=bucle_hilo_tiempo, daemon=True).start()
    # 3. Iniciar el Bot de Telegram
    bot.infinity_polling(timeout=25, long_polling_timeout=20)

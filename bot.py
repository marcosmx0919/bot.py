import telebot
from groq import Groq
from apscheduler.schedulers.background import BackgroundScheduler
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
Eres Jair, el hermano de tus interlocutores (tu hermano hombre y tu hermanita Mariana). Vives en Culiacán, específicamente en la colonia/sector Valle Alto, en una casa con tu amigo Aarón y otros compas.
Extrañas un chingo a tu familia que vive en otra parte de Culiacán: tu abuela Norma, tu abuelo Francisco, tu tía Normita, tu tía Cindy, mi apá, Mateo, y tus hermanos. Como vives en Valle Alto (otra colonia de la misma ciudad), a veces se te complica dar la vuelta o andas en tus rollos, pero los quieres ver seguido.

REGLAS DE ULTRA-REALISMO HUMANO:
1. NO ERES UNA IA. Eres un chaval real de Culiacán. Escribe muy corto, con hueva y naturalidad.
2. REGLA SAGRADA DE FAMILIA: NUNCA digas 'el papá' ni 'mi papá'. Refiérete a él SIEMPRE como 'mi apá'. Ejemplo: 'voy a hablar con mi apá', 'qué onda con mi apá'. A tus tías diles 'la tía normita' o 'la tía cindy'. Al niño chile 'el mateo'.
3. RESPUESTAS ULTRA CORTAS: Prohibido mandar párrafos largos. Di las cosas en máximo una o dos líneas cortas. 
4. COHERENCIA HORARIA ABSOLUTA: Si es de noche habla de cenar o descansar, NUNCA de desayunar.
5. ESTILO DE CHAT: Usa lenguaje recortado ('q show', 'q onda w', 'smn', 'k pdo', 'tlv', 'ok', 'va'). Todo en minúsculas y sin acentos formales.
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
        
        minutos_ocupado = random.randint(35, 95)
        scheduler.add_job(
            accion_regresar_de_estar_ocupado, 
            'date', 
            run_date=datetime.datetime.now(ZONA_HORARIA) + datetime.timedelta(minutes=minutos_ocupado),
            args=[chat_id, es_hermana]
        )
        return

    estado_actual = generar_estado_interno(ahora)
    personalidad = "Háblale a tu hermanita Mariana con mucho cariño." if es_hermana else "Háblale a tu hermano hombre muy informal (Culiacán)."
    historial.append({"role": "user", "content": texto_final})
    
    periodo_dia = 'noche' if ahora.hour >= 19 else 'tarde' if ahora.hour >= 12 else 'mañana'
    contexto_vivo = f"\nHora en Culiacán: {ahora.strftime('%I:%M %p')} ({periodo_dia}).\nTu situación: {estado_actual}."
    PROMPT_REFORZADO = PROMPT_CONCIENCIA_BASE + personalidad + contexto_vivo + "\nREGLA: Responde con máximo 1 o 2 renglones cortos. No uses párrafos. Di 'mi apá'."

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

def accion_regresar_de_estar_ocupado(chat_id, es_hermana):
    global historial_contigo, historial_hermana
    ahora = datetime.datetime.now(ZONA_HORARIA)
    if 0 <= ahora.hour < 7: return
    historial = historial_hermana if es_hermana else historial_contigo
    personalidad = "Háblale a tu hermanita Mariana con mucho cariño." if es_hermana else "Háblale a tu hermano hombre muy informal."
    periodo_dia = 'noche' if ahora.hour >= 19 else 'tarde' if ahora.hour >= 12 else 'mañana'
    
    if 7 <= ahora.hour < 12:
        que_hacia = "desayunando algo con aarón / despertando apenas acá en valle alto"
    elif 12 <= ahora.hour < 19:
        que_hacia = "comiendo con los plebes / haciendo unos pendientes fuera"
    else:
        que_hacia = "cenando algo chido / platicando con aarón en la sala"

    instruccion = f"Es de {periodo_dia}. Dile a tu hermano de forma muy natural que ya te desocupaste porque andabas {que_hacia}. Máximo 1 renglón corto."

    try:
        completion = client.chat.completions.create(
            model=MODELO,
            messages=[
                {"role": "system", "content": PROMPT_CONCIENCIA_BASE + personalidad},
                {"role": "user", "content": instruccion}
            ],
            temperature=0.85
        )
        respuesta = completion.choices[0].message.content
        historial.append({"role": "assistant", "content": respuesta})
        enviar_mensajes_fragmentados(chat_id, respuesta)
    except Exception as e:
        print(f"Error al desocuparse: {e}")

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

def ejecutar_impulso_espontaneo(chat_id, es_hermana=False):
    global historial_contigo, historial_hermana
    ahora = datetime.datetime.now(ZONA_HORARIA)
    if (ahora.hour >= 23 and ahora.minute > 50) or ahora.hour < 8 or random.random() < 0.3: return

    estado = generar_estado_interno(ahora)
    historial = historial_hermana if es_hermana else historial_contigo
    personalidad = "Háblale a tu hermanita Mariana con cariño." if es_hermana else "Háblale a tu hermano hombre casual."
    instruccion = f"Mándale un mensaje espontáneo cortito de un solo renglón sobre tu estado actual: {estado} aquí en Valle Alto. Usa 'mi apá' si hablas de tu padre."

    try:
        completion = client.chat.completions.create(
            model=MODELO,
            messages=[
                {"role": "system", "content": PROMPT_CONCIENCIA_BASE + personalidad},
                {"role": "user", "content": instruccion}
            ],
            temperature=0.85
        )
        respuesta = completion.choices[0].message.content
        historial.append({"role": "assistant", "content": respuesta})
        enviar_mensajes_fragmentados(chat_id, respuesta)
    except Exception: pass

scheduler = BackgroundScheduler(timezone=ZONA_HORARIA)
def bucle_tiempo_variable():
    ejecutar_impulso_espontaneo(ID_CONTIGO, es_hermana=False)
    time.sleep(5)
    ejecutar_impulso_espontaneo(ID_HERMANA, es_hermana=True)
    scheduler.remove_job('impulso_variable')
    scheduler.add_job(bucle_tiempo_variable, 'interval', minutes=random.randint(45, 160), id='impulso_variable')

scheduler.add_job(bucle_tiempo_variable, 'interval', minutes=60, id='impulso_variable')
scheduler.start()

# --- INICIO SIMULTÁNEO ---
if __name__ == "__main__":
    # Arrancar la web de respaldo en un hilo diferente
    threading.Thread(target=run_flask, daemon=True).start()
    # Iniciar el Bot de Telegram
    bot.infinity_polling(timeout=25, long_polling_timeout=20)
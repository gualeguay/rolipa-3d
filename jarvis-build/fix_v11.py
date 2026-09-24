from pathlib import Path
import sys

root = Path(sys.argv[1])
p = root / "app/src/main/java/com/rolipa/jarviscasa/JarvisService.java"
s = p.read_text(encoding="utf-8")

s = s.replace(
"""        if (intent != null && ACTION_TEST_LISTEN.equals(intent.getAction())) {
            main.post(this::beginCommandListening);
        }
        return START_STICKY;""",
"""        if (intent != null && ACTION_TEST_LISTEN.equals(intent.getAction())) {
            // En modo prueba no arrancamos Porcupine primero: algunos teléfonos tardan
            // unas décimas en liberar el micrófono y SpeechRecognizer fallaba al instante.
            main.postDelayed(this::beginCommandListening, 250);
            return START_STICKY;
        }
        // Inicio normal de la escucha continua.
        main.postDelayed(this::startHotword, 200);
        return START_STICKY;"""
)

s = s.replace(
"""            porcupine = new PorcupineManager.Builder()
                    .setAccessKey(key)
                    .setKeyword(Porcupine.BuiltInKeyword.JARVIS)
                    .setSensitivity(0.65f)
                    .build(this, keywordIndex -> main.post(this::onWakeWord));
            startHotword();""",
"""            porcupine = new PorcupineManager.Builder()
                    .setAccessKey(key)
                    .setKeyword(Porcupine.BuiltInKeyword.JARVIS)
                    .setSensitivity(0.65f)
                    .build(this, keywordIndex -> main.post(this::onWakeWord));
            updateNotification("Jarvis preparado");"""
)

s = s.replace(
"""            @Override
            public void onError(int error) {
                recognizing = false;
                if (error != SpeechRecognizer.ERROR_CLIENT) {
                    speak("No te entendí");
                }
                main.postDelayed(JarvisService.this::startHotword, 700);
            }""",
"""            @Override
            public void onError(int error) {
                recognizing = false;
                String label = speechErrorLabel(error);
                updateNotification("Reconocimiento: " + label);

                switch (error) {
                    case SpeechRecognizer.ERROR_SPEECH_TIMEOUT:
                    case SpeechRecognizer.ERROR_NO_MATCH:
                        speak("No te entendí");
                        break;
                    case SpeechRecognizer.ERROR_AUDIO:
                    case SpeechRecognizer.ERROR_RECOGNIZER_BUSY:
                        speak("El micrófono estaba ocupado. Probá de nuevo");
                        break;
                    case SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS:
                        speak("Falta permiso de micrófono");
                        break;
                    case SpeechRecognizer.ERROR_NETWORK:
                    case SpeechRecognizer.ERROR_NETWORK_TIMEOUT:
                    case SpeechRecognizer.ERROR_SERVER:
                        speak("No pude conectar con el reconocimiento de voz");
                        break;
                    case SpeechRecognizer.ERROR_CLIENT:
                        break;
                    default:
                        speak("No pude escuchar la orden");
                        break;
                }
                main.postDelayed(JarvisService.this::startHotword, 1200);
            }"""
)

old_begin = """    private void beginCommandListening() {
        if (recognizing || speechRecognizer == null) return;
        stopHotword();
        recognizing = true;

        Intent recognizer = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
        recognizer.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
        recognizer.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "es-AR");
        recognizer.putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE, "es-AR");
        recognizer.putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, false);
        recognizer.putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 3);
        recognizer.putExtra(RecognizerIntent.EXTRA_PREFER_OFFLINE, true);
        recognizer.putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_COMPLETE_SILENCE_LENGTH_MILLIS, 1100L);
        recognizer.putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_POSSIBLY_COMPLETE_SILENCE_LENGTH_MILLIS, 800L);

        try {
            speechRecognizer.startListening(recognizer);
        } catch (Exception e) {
            recognizing = false;
            speak("No pude abrir el reconocimiento de voz");
            main.postDelayed(this::startHotword, 800);
        }
    }"""

new_begin = """    private void beginCommandListening() {
        if (recognizing || speechRecognizer == null) return;

        // Porcupine y SpeechRecognizer usan el mismo micrófono. En varios Android,
        // arrancar el segundo inmediatamente después de parar el primero devuelve
        // ERROR_AUDIO / ERROR_RECOGNIZER_BUSY. Le damos tiempo real para liberarlo.
        recognizing = true;
        stopHotword();
        updateNotification("Preparando micrófono…");
        main.postDelayed(this::startSpeechRecognitionNow, 550);
    }

    private void startSpeechRecognitionNow() {
        if (!recognizing || speechRecognizer == null) return;

        Intent recognizer = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
        recognizer.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
        recognizer.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "es-AR");
        recognizer.putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE, "es-AR");
        recognizer.putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, false);
        recognizer.putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 3);

        // No forzamos reconocimiento offline: si el teléfono no tiene descargado
        // el paquete español, algunos servicios fallan apenas se abre el micrófono.
        recognizer.putExtra(RecognizerIntent.EXTRA_PREFER_OFFLINE, false);
        recognizer.putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_COMPLETE_SILENCE_LENGTH_MILLIS, 1800L);
        recognizer.putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_POSSIBLY_COMPLETE_SILENCE_LENGTH_MILLIS, 1200L);
        recognizer.putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_MINIMUM_LENGTH_MILLIS, 700L);

        try {
            speechRecognizer.startListening(recognizer);
        } catch (Exception e) {
            recognizing = false;
            updateNotification("Error al abrir reconocimiento de voz");
            speak("No pude abrir el reconocimiento de voz");
            main.postDelayed(this::startHotword, 1200);
        }
    }"""

if old_begin not in s:
    raise SystemExit("No se encontró bloque beginCommandListening esperado")
s = s.replace(old_begin, new_begin)

anchor = """    private static String shortMessage(String msg) {"""
helper = """    private static String speechErrorLabel(int error) {
        switch (error) {
            case SpeechRecognizer.ERROR_NETWORK_TIMEOUT: return "NETWORK_TIMEOUT (1)";
            case SpeechRecognizer.ERROR_NETWORK: return "NETWORK (2)";
            case SpeechRecognizer.ERROR_AUDIO: return "AUDIO (3)";
            case SpeechRecognizer.ERROR_SERVER: return "SERVER (4)";
            case SpeechRecognizer.ERROR_CLIENT: return "CLIENT (5)";
            case SpeechRecognizer.ERROR_SPEECH_TIMEOUT: return "SPEECH_TIMEOUT (6)";
            case SpeechRecognizer.ERROR_NO_MATCH: return "NO_MATCH (7)";
            case SpeechRecognizer.ERROR_RECOGNIZER_BUSY: return "RECOGNIZER_BUSY (8)";
            case SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS: return "PERMISSIONS (9)";
            default: return "ERROR (" + error + ")";
        }
    }

"""
if helper not in s:
    s = s.replace(anchor, helper + anchor)

p.write_text(s, encoding="utf-8")

g = root / "app/build.gradle"
t = g.read_text(encoding="utf-8")
t = t.replace("versionCode 1", "versionCode 2")
t = t.replace("versionName '1.0'", "versionName '1.1'")
g.write_text(t, encoding="utf-8")

print("Jarvis Casa v1.1 speech fix aplicado")

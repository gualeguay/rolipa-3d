from pathlib import Path
import re, sys

root=Path(sys.argv[1])

# Gradle: replace Picovoice with openWakeWord + JitPack
p=root/"app/build.gradle"
s=p.read_text(encoding="utf-8")
s=s.replace("versionCode 2","versionCode 3").replace("versionName '1.1'","versionName '1.2'")
s=s.replace("implementation 'ai.picovoice:porcupine-android:4.0.2'","implementation 'com.github.msnilsen:openwakeword-android:0.1.0'")
p.write_text(s,encoding="utf-8")

p=root/"settings.gradle"
s=p.read_text(encoding="utf-8")
if "https://jitpack.io" not in s:
    s=s.replace("        mavenCentral()\n","        mavenCentral()\n        maven { url = uri(\"https://jitpack.io\") }\n")
p.write_text(s,encoding="utf-8")

# UI: no Picovoice key needed
p=root/"app/src/main/java/com/rolipa/jarviscasa/MainActivity.java"
s=p.read_text(encoding="utf-8")
s=s.replace("    private EditText picovoiceKey;\n","")
s=s.replace("Decí “Jarvis” y después la orden. Diseñada para seguir escuchando con la pantalla bloqueada.",
            "Decí “Hey Jarvis” y después la orden. El wake word se detecta localmente, sin cuenta ni clave externa.")
s=s.replace('''        root.addView(section("1. Palabra de activación"));
        picovoiceKey = edit("AccessKey de Picovoice", true);
        root.addView(picovoiceKey);
        root.addView(help("Porcupine usa JARVIS como palabra integrada. Pegá acá tu AccessKey gratuito de Picovoice."));''',
'''        root.addView(section("1. Palabra de activación"));
        root.addView(help("Wake word local: “Hey Jarvis”. No necesita Picovoice, cuenta, API key ni Internet para detectar la palabra de activación."));''')
s=s.replace('''        if (!store.hasPicovoiceKey()) {
            toast("Falta el AccessKey de Picovoice");
            return;
        }
''',"")
s=s.replace("Jarvis activado. Probá bloquear el teléfono y decir “Jarvis”.","Jarvis activado. Probá decir “Hey Jarvis”.")
s=s.replace("Necesito permiso de micrófono para escuchar “Jarvis”","Necesito permiso de micrófono para escuchar “Hey Jarvis”")
s=s.replace('''        store.save(
                picovoiceKey.getText().toString(),''','''        store.save(
                "",''')
s=s.replace("        picovoiceKey.setText(store.getPicovoiceKey());\n","")
s=s.replace("• “Jarvis, prendé la luz de la pieza”\\n• “Jarvis, apagá la luz”\\n• “Jarvis, apagá la luz en 5 minutos”\\n• “Jarvis, cancelá el temporizador”",
            "• “Hey Jarvis” → “prendé la luz de la pieza”\\n• “Hey Jarvis” → “apagá la luz”\\n• “Hey Jarvis” → “apagá la luz en 5 minutos”\\n• “Hey Jarvis” → “cancelá el temporizador”")
p.write_text(s,encoding="utf-8")

# Service: replace Porcupine with local openWakeWord
p=root/"app/src/main/java/com/rolipa/jarviscasa/JarvisService.java"
s=p.read_text(encoding="utf-8")
s=s.replace("import ai.picovoice.porcupine.Porcupine;\nimport ai.picovoice.porcupine.PorcupineException;\nimport ai.picovoice.porcupine.PorcupineManager;\n",
            "import com.openwakeword.OpenWakeWord;\n")
s=s.replace("    private PorcupineManager porcupine;\n","    private OpenWakeWord wakeWordDetector;\n")

start=s.index("    private void initWakeWord() {")
end=s.index("    private void initSpeechRecognizer() {")
wake='''    private void initWakeWord() {
        try {
            wakeWordDetector = new OpenWakeWord.Builder(this)
                    .setModel(OpenWakeWord.BuiltInModel.HEY_JARVIS)
                    .setThreshold(0.45f)
                    .setDebounceMs(2500L)
                    .build();
            updateNotification("Jarvis preparado · wake word local");
        } catch (Exception e) {
            updateNotification("Error al preparar wake word: " + shortMessage(e.getMessage()));
        }
    }

    private void startHotword() {
        if (wakeWordDetector == null || hotwordStarted || recognizing) return;
        try {
            hotwordStarted = true;
            wakeWordDetector.start(score -> main.post(() -> onWakeWord(score)));
            updateNotification("Escuchando “Hey Jarvis”");
        } catch (Exception e) {
            hotwordStarted = false;
            updateNotification("No pude iniciar wake word: " + shortMessage(e.getMessage()));
        }
    }

    private void stopHotword() {
        if (wakeWordDetector == null || !hotwordStarted) return;
        try { wakeWordDetector.stop(); } catch (Exception ignored) { }
        hotwordStarted = false;
    }

    private void onWakeWord(float score) {
        if (recognizing) return;
        updateNotification("Hey Jarvis detectado");
        tone.startTone(ToneGenerator.TONE_PROP_ACK, 120);
        beginCommandListening();
    }

'''
s=s[:start]+wake+s[end:]
s=s.replace("// Porcupine y SpeechRecognizer usan el mismo micrófono. En varios Android,",
            "// openWakeWord y SpeechRecognizer usan el mismo micrófono. En varios Android,")
s=s.replace("main.postDelayed(this::startSpeechRecognitionNow, 550);","main.postDelayed(this::startSpeechRecognitionNow, 650);")
s=s.replace('''        if (porcupine != null) {
            porcupine.delete();
            porcupine = null;
        }''','''        if (wakeWordDetector != null) {
            try { wakeWordDetector.release(); } catch (Exception ignored) { }
            wakeWordDetector = null;
        }''')
p.write_text(s,encoding="utf-8")
print("Jarvis Casa v1.2 openWakeWord aplicado")

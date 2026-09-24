from pathlib import Path
import sys

root=Path(sys.argv[1])

# Copy diagnostic detector into app sources
src=Path("jarvis-build/LocalWakeWordDetector.java")
dst=root/"app/src/main/java/com/rolipa/jarviscasa/LocalWakeWordDetector.java"
dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

# Service changes
p=root/"app/src/main/java/com/rolipa/jarviscasa/JarvisService.java"
s=p.read_text(encoding="utf-8")

s=s.replace("import com.openwakeword.OpenWakeWord;\n","")
s=s.replace("    private OpenWakeWord wakeWordDetector;\n","    private LocalWakeWordDetector wakeWordDetector;\n")

start=s.index("    private void initWakeWord() {")
end=s.index("    private void initSpeechRecognizer() {")
wake='''    private void initWakeWord() {
        try {
            wakeWordDetector = new LocalWakeWordDetector(
                    this,
                    0.18f,
                    new LocalWakeWordDetector.Listener() {
                        @Override
                        public void onDetected(float score) {
                            main.post(() -> onWakeWord(score));
                        }

                        @Override
                        public void onStatus(String status) {
                            main.post(() -> updateNotification(status));
                        }
                    }
            );
            updateNotification("Jarvis preparado · diagnóstico activo");
        } catch (Exception e) {
            updateNotification("Error al preparar wake word: " + shortMessage(e.getMessage()));
        }
    }

    private void startHotword() {
        if (wakeWordDetector == null || hotwordStarted || recognizing) return;
        try {
            hotwordStarted = true;
            wakeWordDetector.start();
            updateNotification("Iniciando micrófono local…");
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
        updateNotification("Hey Jarvis detectado · score " + String.format(java.util.Locale.US, "%.2f", score));
        tone.startTone(ToneGenerator.TONE_PROP_ACK, 120);
        beginCommandListening();
    }

'''
s=s[:start]+wake+s[end:]

s=s.replace("main.postDelayed(this::startSpeechRecognitionNow, 650);","main.postDelayed(this::startSpeechRecognitionNow, 750);")

s=s.replace('''        if (wakeWordDetector != null) {
            try { wakeWordDetector.release(); } catch (Exception ignored) { }
            wakeWordDetector = null;
        }''','''        if (wakeWordDetector != null) {
            try { wakeWordDetector.release(); } catch (Exception ignored) { }
            wakeWordDetector = null;
        }''')

p.write_text(s,encoding="utf-8")

# MainActivity wording
p=root/"app/src/main/java/com/rolipa/jarviscasa/MainActivity.java"
s=p.read_text(encoding="utf-8")
s=s.replace("Wake word local: “Hey Jarvis”. No necesita Picovoice, cuenta, API key ni Internet para detectar la palabra de activación.",
            "Wake word local: “Hey Jarvis”. Esta versión muestra diagnóstico en la notificación: nivel de micrófono, score y umbral.")
s=s.replace("Jarvis activado. Probá decir “Hey Jarvis”.",
            "Jarvis activado. Mirá la notificación: debe mostrar nivel de micrófono y score mientras hablás.")
p.write_text(s,encoding="utf-8")

# version
p=root/"app/build.gradle"
s=p.read_text(encoding="utf-8").replace("versionCode 3","versionCode 4").replace("versionName '1.2'","versionName '1.3'")
p.write_text(s,encoding="utf-8")

print("Jarvis Casa v1.3 diagnostico aplicado")

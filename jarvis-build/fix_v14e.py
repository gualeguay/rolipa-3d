from pathlib import Path
import sys
root=Path(sys.argv[1])
p=root/"app/src/main/java/com/rolipa/jarviscasa/JarvisService.java"
s=p.read_text(encoding="utf-8")

s=s.replace("    private Runnable delayedOffRunnable;",
            "    private Runnable lightDelayedOffRunnable;\n    private Runnable heaterDelayedOffRunnable;")

start=s.index("    private void handleCommand(String spoken) {")
end=s.index("    private void restartAfterSpeech() {")
block='''    private void handleCommand(String spoken) {
        CommandRouter.Command command = CommandRouter.parse(
                spoken, settings.getAliases(), settings.getHeaterAliases());

        switch (command.type) {
            case ON:
                executePower(command.target, true);
                break;
            case OFF:
                cancelDelayedOff(command.target, false);
                executePower(command.target, false);
                break;
            case OFF_DELAYED:
                scheduleOff(command.target, command.delayMs);
                break;
            case ON_TIMED:
                executeTimedOn(command.target, command.delayMs);
                break;
            case CANCEL_TIMER:
                cancelDelayedOff(command.target, true);
                restartAfterSpeech();
                break;
            case UNKNOWN:
            default:
                speak("No conozco esa orden todavía");
                restartAfterSpeech();
                break;
        }
    }

    private void executePower(CommandRouter.Target target, boolean on) {
        String id = deviceIdFor(target);
        String code = codeFor(target);
        String label = labelFor(target);

        if (id.isEmpty()) {
            speak("Falta configurar " + label);
            restartAfterSpeech();
            return;
        }

        updateNotification((on ? "Encendiendo " : "Apagando ") + label.toLowerCase() + "…");
        tuya.setPower(id, code, label, on, (success, message) -> main.post(() -> {
            speak(success ? message : "No pude hacerlo. " + message);
            restartAfterSpeech();
        }));
    }

    private void executeTimedOn(CommandRouter.Target target, long delayMs) {
        cancelDelayedOff(target, false);
        String id = deviceIdFor(target);
        String code = codeFor(target);
        String label = labelFor(target);

        if (id.isEmpty()) {
            speak("Falta configurar " + label);
            restartAfterSpeech();
            return;
        }

        updateNotification("Encendiendo " + label.toLowerCase() + " con temporizador…");
        tuya.setPower(id, code, label, true, (success, message) -> main.post(() -> {
            if (!success) {
                speak("No pude hacerlo. " + message);
                restartAfterSpeech();
                return;
            }

            Runnable off = () -> executePower(target, false);
            setTimerRunnable(target, off);
            main.postDelayed(off, delayMs);

            long minutes = Math.max(1L, Math.round(delayMs / 60000.0));
            speak(label + " encendido por " + minutes + (minutes == 1 ? " minuto" : " minutos"));
            restartAfterSpeech();
        }));
    }

    private void scheduleOff(CommandRouter.Target target, long delayMs) {
        cancelDelayedOff(target, false);
        Runnable off = () -> executePower(target, false);
        setTimerRunnable(target, off);
        main.postDelayed(off, delayMs);

        long minutes = Math.max(1L, Math.round(delayMs / 60000.0));
        speak("Listo. " + labelFor(target) + " se apaga en " + minutes
                + (minutes == 1 ? " minuto" : " minutos"));
        restartAfterSpeech();
    }

    private void setTimerRunnable(CommandRouter.Target target, Runnable value) {
        if (target == CommandRouter.Target.HEATER) heaterDelayedOffRunnable = value;
        else if (target == CommandRouter.Target.LIGHT) lightDelayedOffRunnable = value;
    }

    private void cancelDelayedOff(CommandRouter.Target target, boolean announce) {
        boolean cancelled = false;

        if ((target == CommandRouter.Target.LIGHT || target == CommandRouter.Target.UNKNOWN)
                && lightDelayedOffRunnable != null) {
            main.removeCallbacks(lightDelayedOffRunnable);
            lightDelayedOffRunnable = null;
            cancelled = true;
        }

        if ((target == CommandRouter.Target.HEATER || target == CommandRouter.Target.UNKNOWN)
                && heaterDelayedOffRunnable != null) {
            main.removeCallbacks(heaterDelayedOffRunnable);
            heaterDelayedOffRunnable = null;
            cancelled = true;
        }

        if (announce) {
            speak(cancelled ? "Temporizador cancelado" : "No hay ningún temporizador activo");
        }
    }

    private String deviceIdFor(CommandRouter.Target target) {
        if (target == CommandRouter.Target.HEATER) return settings.getHeaterDeviceId().trim();
        if (target == CommandRouter.Target.LIGHT) return settings.getTuyaDeviceId().trim();
        return "";
    }

    private String codeFor(CommandRouter.Target target) {
        if (target == CommandRouter.Target.HEATER) return settings.getHeaterSwitchCode().trim();
        if (target == CommandRouter.Target.LIGHT) return settings.getTuyaSwitchCode().trim();
        return "";
    }

    private String labelFor(CommandRouter.Target target) {
        return target == CommandRouter.Target.HEATER ? "Termotanque" : "Luz";
    }

'''
s=s[:start]+block+s[end:]

s=s.replace("cancelDelayedOff(false);","cancelDelayedOff(CommandRouter.Target.UNKNOWN, false);")

p.write_text(s,encoding="utf-8")
print("v1.4 service")

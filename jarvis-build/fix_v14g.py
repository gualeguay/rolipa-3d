from pathlib import Path
import sys, re
root=Path(sys.argv[1])

router=root/"app/src/main/java/com/rolipa/jarviscasa/CommandRouter.java"
router.write_text(r'''package com.rolipa.jarviscasa;

import java.text.Normalizer;
import java.util.Locale;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public final class CommandRouter {
    public enum Type { ON, OFF, OFF_DELAYED, ON_TIMED, CANCEL_TIMER, UNKNOWN }
    public enum Target { LIGHT, HEATER, UNKNOWN }

    public static final class Command {
        public final Type type;
        public final Target target;
        public final long delayMs;
        public final String raw;

        public Command(Type type, Target target, long delayMs, String raw) {
            this.type = type;
            this.target = target;
            this.delayMs = delayMs;
            this.raw = raw;
        }
    }

    private static final Pattern DELAY_MINUTES =
            Pattern.compile("(?:en|dentro de)\\s+(\\d+)\\s*(?:minuto|minutos|min)");
    private static final Pattern DELAY_SECONDS =
            Pattern.compile("(?:en|dentro de)\\s+(\\d+)\\s*(?:segundo|segundos|seg)");
    private static final Pattern FOR_MINUTES =
            Pattern.compile("(?:por|durante)\\s+(\\d+)\\s*(?:minuto|minutos|min)");
    private static final Pattern FOR_SECONDS =
            Pattern.compile("(?:por|durante)\\s+(\\d+)\\s*(?:segundo|segundos|seg)");

    public static Command parse(String spoken, String lightAliasesCsv, String heaterAliasesCsv) {
        if (spoken == null) return new Command(Type.UNKNOWN, Target.UNKNOWN, 0, "");
        String s = normalize(spoken);
        Target target = detectTarget(s, lightAliasesCsv, heaterAliasesCsv);

        if (s.contains("cancela") && (s.contains("temporizador") || s.contains("timer"))) {
            return new Command(Type.CANCEL_TIMER, target, 0, spoken);
        }

        if (target == Target.UNKNOWN) return new Command(Type.UNKNOWN, Target.UNKNOWN, 0, spoken);

        boolean wantsOff = containsAny(s, "apaga", "apagar", "desactiva", "desactivar");
        boolean wantsOn = containsAny(s, "prende", "prender", "enciende", "encender", "activa", "activar");

        if (wantsOff) {
            long delay = parseDelay(s);
            if (delay > 0) return new Command(Type.OFF_DELAYED, target, delay, spoken);
            return new Command(Type.OFF, target, 0, spoken);
        }

        if (wantsOn) {
            long duration = parseDuration(s);
            if (duration > 0) return new Command(Type.ON_TIMED, target, duration, spoken);
            return new Command(Type.ON, target, 0, spoken);
        }

        return new Command(Type.UNKNOWN, target, 0, spoken);
    }

    private static Target detectTarget(String s, String lightAliasesCsv, String heaterAliasesCsv) {
        if (s.contains("termotanque") || matchesAliases(s, heaterAliasesCsv)) return Target.HEATER;
        if (s.contains("luz") || matchesAliases(s, lightAliasesCsv)) return Target.LIGHT;
        return Target.UNKNOWN;
    }

    private static boolean matchesAliases(String s, String aliasesCsv) {
        if (aliasesCsv == null) return false;
        for (String alias : aliasesCsv.split(",")) {
            String a = normalize(alias.trim());
            if (!a.isEmpty() && s.contains(a)) return true;
        }
        return false;
    }

    private static long parseDelay(String s) {
        Matcher m = DELAY_MINUTES.matcher(s);
        if (m.find()) return Long.parseLong(m.group(1)) * 60000L;
        Matcher sec = DELAY_SECONDS.matcher(s);
        if (sec.find()) return Long.parseLong(sec.group(1)) * 1000L;
        return 0;
    }

    private static long parseDuration(String s) {
        Matcher m = FOR_MINUTES.matcher(s);
        if (m.find()) return Long.parseLong(m.group(1)) * 60000L;
        Matcher sec = FOR_SECONDS.matcher(s);
        if (sec.find()) return Long.parseLong(sec.group(1)) * 1000L;
        return 0;
    }

    private static boolean containsAny(String s, String... values) {
        for (String v : values) if (s.contains(v)) return true;
        return false;
    }

    private static String normalize(String s) {
        String n = Normalizer.normalize(s.toLowerCase(Locale.ROOT), Normalizer.Form.NFD);
        return n.replaceAll("\\p{M}", "").replaceAll("[^a-z0-9 ]", " ").replaceAll("\\s+", " ").trim();
    }
}
''', encoding="utf-8")

main=root/"app/src/main/java/com/rolipa/jarviscasa/MainActivity.java"
s=main.read_text(encoding="utf-8")
s=re.sub(
    r'\s*root\.addView\(help\("TERMOTANQUE:.*?\)\);\s*(?=TextView note = text\("IMPORTANTE:)',
    '\n        root.addView(help("TERMOTANQUE:\\\\n• Hey Jarvis → prendé el termotanque\\\\n• Hey Jarvis → apagá el termotanque\\\\n• Hey Jarvis → prendé el termotanque por 30 minutos\\\\n• Hey Jarvis → apagá el termotanque en 20 minutos"));\n\n        ',
    s,
    flags=re.S
)
main.write_text(s,encoding="utf-8")
print("v1.4 syntax fixes")

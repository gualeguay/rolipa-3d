from pathlib import Path
import sys
root=Path(sys.argv[1])
p=root/"app/src/main/java/com/rolipa/jarviscasa/MainActivity.java"
s=p.read_text(encoding="utf-8")

s=s.replace(
"""    private EditText aliases;
    private boolean startAfterPermission = false;""",
"""    private EditText aliases;
    private EditText heaterDeviceId;
    private EditText heaterSwitchCode;
    private EditText heaterAliases;
    private boolean startAfterPermission = false;"""
)

anchor='''        root.addView(aliases);

        root.addView(help("Para Argentina normalmente probamos primero Western America. El código del interruptor suele ser switch_led, switch_1 o switch."));
'''
replacement='''        root.addView(aliases);

        root.addView(help("Para Argentina normalmente probamos primero Western America. El código de la luz suele ser switch_led, switch_1 o switch."));

        root.addView(section("3. Termotanque"));
        heaterDeviceId = edit("Device ID del enchufe del termotanque", false);
        heaterSwitchCode = edit("Código del enchufe (probamos switch_1)", false);
        heaterAliases = edit("Nombres: termotanque, agua caliente…", false);
        root.addView(heaterDeviceId);
        root.addView(heaterSwitchCode);
        root.addView(heaterAliases);
        root.addView(help("Usa las mismas credenciales Tuya. Jarvis trata el termotanque como un dispositivo independiente."));
'''
if anchor not in s: raise SystemExit("bloque Tuya UI no encontrado")
s=s.replace(anchor,replacement)

s=s.replace('Button on = button("Probar ENCENDER");','Button on = button("Probar LUZ ON");')
s=s.replace('Button off = button("Probar APAGAR");','Button off = button("Probar LUZ OFF");')
s=s.replace("on.setOnClickListener(v -> testTuya(true));","on.setOnClickListener(v -> testTuyaLight(true));")
s=s.replace("off.setOnClickListener(v -> testTuya(false));","off.setOnClickListener(v -> testTuyaLight(false));")

marker='''        off.setOnClickListener(v -> testTuyaLight(false));

        root.addView(section("3. Activar Jarvis"));'''
replacement='''        off.setOnClickListener(v -> testTuyaLight(false));

        LinearLayout heaterTests = horizontal();
        Button heaterOn = button("Probar TERMO ON");
        Button heaterOff = button("Probar TERMO OFF");
        heaterTests.addView(heaterOn, weighted());
        heaterTests.addView(heaterOff, weighted());
        root.addView(heaterTests);
        heaterOn.setOnClickListener(v -> testTuyaHeater(true));
        heaterOff.setOnClickListener(v -> testTuyaHeater(false));

        root.addView(section("4. Activar Jarvis"));'''
if marker not in s: raise SystemExit("bloque botones no encontrado")
s=s.replace(marker,replacement)

start=s.index("    private void testTuya(")
end=s.index("    private void startJarvis() {")
tests='''    private void testTuyaLight(boolean turnOn) {
        saveSettings();
        if (!store.hasTuyaConfig()) {
            toast("Completá la configuración de la luz");
            return;
        }
        testTuyaDevice(store.getTuyaDeviceId(), store.getTuyaSwitchCode(), "Luz", turnOn);
    }

    private void testTuyaHeater(boolean turnOn) {
        saveSettings();
        if (!store.hasHeaterConfig()) {
            toast("Falta el Device ID del termotanque");
            return;
        }
        testTuyaDevice(store.getHeaterDeviceId(), store.getHeaterSwitchCode(), "Termotanque", turnOn);
    }

    private void testTuyaDevice(String id, String code, String label, boolean turnOn) {
        toast((turnOn ? "Probando encendido de " : "Probando apagado de ") + label.toLowerCase() + "…");
        TuyaClient client = new TuyaClient(this);
        client.setPower(id, code, label, turnOn, (success, message) -> runOnUiThread(() -> {
            toast(message);
            client.shutdown();
        }));
    }

'''
s=s[:start]+tests+s[end:]

old='''                deviceId.getText().toString(),
                switchCode.getText().toString(),
                aliases.getText().toString()
        );'''
new='''                deviceId.getText().toString(),
                switchCode.getText().toString(),
                aliases.getText().toString(),
                heaterDeviceId.getText().toString(),
                heaterSwitchCode.getText().toString(),
                heaterAliases.getText().toString()
        );'''
if old not in s: raise SystemExit("saveSettings no encontrado")
s=s.replace(old,new)

s=s.replace(
"""        aliases.setText(store.getAliases());
        String savedRegion = store.getTuyaRegion();""",
"""        aliases.setText(store.getAliases());
        heaterDeviceId.setText(store.getHeaterDeviceId());
        heaterSwitchCode.setText(store.getHeaterSwitchCode());
        heaterAliases.setText(store.getHeaterAliases());
        String savedRegion = store.getTuyaRegion();"""
)

needle='''        TextView note = text("IMPORTANTE:'''
idx=s.find(needle)
if idx < 0: raise SystemExit("nota importante no encontrada")
extra='''        root.addView(help("TERMOTANQUE:\n• “Hey Jarvis” → “prendé el termotanque”\n• “Hey Jarvis” → “apagá el termotanque”\n• “Hey Jarvis” → “prendé el termotanque por 30 minutos”\n• “Hey Jarvis” → “apagá el termotanque en 20 minutos”"));

'''
s=s[:idx]+extra+s[idx:]

p.write_text(s,encoding="utf-8")
print("v1.4 main UI")

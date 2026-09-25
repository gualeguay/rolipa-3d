from pathlib import Path
import sys
root=Path(sys.argv[1])

p=root/"app/src/main/java/com/rolipa/jarviscasa/SettingsStore.java"
s=p.read_text(encoding="utf-8")
s=s.replace('''    public String getAliases() { return prefs.getString("aliases", "luz de la pieza,luz del dormitorio,luz"); }
''','''    public String getAliases() { return prefs.getString("aliases", "luz de la pieza,luz del dormitorio,luz"); }
    public String getHeaterDeviceId() { return prefs.getString("heater_device_id", "ebd96177c559bd1253aidy"); }
    public String getHeaterSwitchCode() { return prefs.getString("heater_switch_code", "switch_1"); }
    public String getHeaterAliases() { return prefs.getString("heater_aliases", "termotanque,termotanque electrico,agua caliente"); }
''')
s=s.replace('''    public void save(String picovoiceKey, String region, String accessId, String accessSecret,
                     String deviceId, String switchCode, String aliases) {''','''    public void save(String picovoiceKey, String region, String accessId, String accessSecret,
                     String deviceId, String switchCode, String aliases,
                     String heaterDeviceId, String heaterSwitchCode, String heaterAliases) {''')
s=s.replace('''                .putString("aliases", safe(aliases))
                .apply();''','''                .putString("aliases", safe(aliases))
                .putString("heater_device_id", safe(heaterDeviceId))
                .putString("heater_switch_code", safe(heaterSwitchCode).isEmpty() ? "switch_1" : safe(heaterSwitchCode))
                .putString("heater_aliases", safe(heaterAliases))
                .apply();''')
s=s.replace('''    public boolean hasTuyaConfig() {
        return !getTuyaAccessId().trim().isEmpty()
                && !getTuyaAccessSecret().trim().isEmpty()
                && !getTuyaDeviceId().trim().isEmpty();
    }''','''    public boolean hasTuyaCredentials() {
        return !getTuyaAccessId().trim().isEmpty()
                && !getTuyaAccessSecret().trim().isEmpty();
    }
    public boolean hasTuyaConfig() {
        return hasTuyaCredentials() && !getTuyaDeviceId().trim().isEmpty();
    }
    public boolean hasHeaterConfig() {
        return hasTuyaCredentials() && !getHeaterDeviceId().trim().isEmpty();
    }''')
p.write_text(s,encoding="utf-8")
print("v1.4 settings multi-device")

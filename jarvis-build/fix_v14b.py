from pathlib import Path
import sys
root=Path(sys.argv[1])
p=root/"app/src/main/java/com/rolipa/jarviscasa/TuyaClient.java"
s=p.read_text(encoding="utf-8")
old='''    public void setPower(boolean on, Callback callback) {
        executor.execute(() -> {
            try {
                if (!settings.hasTuyaConfig()) {
                    callback.onResult(false, "Falta configurar Tuya");
                    return;
                }

                ensureToken();
                String deviceId = settings.getTuyaDeviceId();
                String code = settings.getTuyaSwitchCode();
                String path = "/v1.0/iot-03/devices/" + deviceId + "/commands";

                JSONObject command = new JSONObject();
                command.put("code", code);
                command.put("value", on);

                JSONArray commands = new JSONArray();
                commands.put(command);

                JSONObject body = new JSONObject();
                body.put("commands", commands);

                JSONObject response = request("POST", path, body.toString(), true);
                boolean ok = response.optBoolean("success", false) && response.optBoolean("result", true);
                if (ok) {
                    callback.onResult(true, on ? "Luz encendida" : "Luz apagada");
                } else {
                    callback.onResult(false, response.optString("msg", "Tuya rechazó el comando"));
                }
            } catch (Exception e) {
                callback.onResult(false, "Error Tuya: " + e.getMessage());
            }
        });
    }
'''
new='''    public void setPower(boolean on, Callback callback) {
        setPower(settings.getTuyaDeviceId(), settings.getTuyaSwitchCode(), "Luz", on, callback);
    }

    public void setPower(String deviceId, String code, String label, boolean on, Callback callback) {
        executor.execute(() -> {
            try {
                if (!settings.hasTuyaConfig()) {
                    callback.onResult(false, "Falta configurar Tuya");
                    return;
                }
                if (deviceId == null || deviceId.trim().isEmpty()) {
                    callback.onResult(false, "Falta dispositivo");
                    return;
                }

                ensureToken();
                String path = "/v1.0/iot-03/devices/" + deviceId.trim() + "/commands";
                JSONObject command = new JSONObject();
                command.put("code", code == null || code.trim().isEmpty() ? "switch_1" : code.trim());
                command.put("value", on);
                JSONArray commands = new JSONArray();
                commands.put(command);
                JSONObject body = new JSONObject();
                body.put("commands", commands);

                JSONObject response = request("POST", path, body.toString(), true);
                boolean ok = response.optBoolean("success", false) && response.optBoolean("result", true);
                callback.onResult(ok, ok ? label + (on ? " encendido" : " apagado")
                        : response.optString("msg", "Tuya rechazó el comando"));
            } catch (Exception e) {
                callback.onResult(false, "Error Tuya: " + e.getMessage());
            }
        });
    }
'''
if old not in s: raise SystemExit("setPower original no encontrado")
p.write_text(s.replace(old,new),encoding="utf-8")
print("v1.4 tuya multi")

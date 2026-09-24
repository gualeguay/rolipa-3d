package com.rolipa.jarviscasa;

import android.Manifest;
import android.content.Context;
import android.content.pm.PackageManager;
import android.media.AudioFormat;
import android.media.AudioRecord;
import android.media.MediaRecorder;
import android.os.Handler;
import android.os.Looper;

import androidx.core.content.ContextCompat;

import ai.onnxruntime.OnnxTensor;
import ai.onnxruntime.OrtEnvironment;
import ai.onnxruntime.OrtSession;

import java.nio.FloatBuffer;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Detector local de "Hey Jarvis" basado en los modelos openWakeWord.
 * No usa nube ni API key. Esta clase incorpora diagnostico de audio y score
 * para poder ver en la notificacion si el microfono realmente recibe voz.
 */
public final class LocalWakeWordDetector {
    public interface Listener {
        void onDetected(float score);
        void onStatus(String status);
    }

    private static final int SAMPLE_RATE = 16000;
    private static final int FRAME_SAMPLES = 1280; // 80 ms
    private static final int MEL_CONTEXT_SAMPLES = 480;
    private static final int MEL_BINS = 32;
    private static final int MEL_WINDOW_FRAMES = 76;
    private static final int EMBEDDING_DIM = 96;
    private static final int FEATURE_WINDOW = 16;
    private static final int FEATURE_BUFFER_MAX = 120;
    private static final int MEL_BUFFER_MAX = 970;
    private static final int SKIP_INITIAL_PREDICTIONS = 5;
    private static final int RAW_BUFFER_SECONDS = 10;

    private final Context context;
    private final float threshold;
    private final Listener listener;
    private final Handler main = new Handler(Looper.getMainLooper());

    private OrtEnvironment env;
    private OrtSession melSession;
    private OrtSession embeddingSession;
    private OrtSession wakeSession;
    private String wakeInputName;

    private AudioRecord audioRecord;
    private Thread thread;
    private volatile boolean running;

    private float[] rawBuffer;
    private int rawWritePos;
    private long rawTotalWritten;
    private final ArrayList<float[]> melBuffer = new ArrayList<>();
    private final ArrayList<float[]> featureBuffer = new ArrayList<>();
    private int predictionCount;
    private long lastDetectionMs;
    private long lastStatusMs;
    private float maxScoreSinceStatus;
    private double levelSumSinceStatus;
    private int levelCountSinceStatus;
    private int audioSourceInUse = -1;

    public LocalWakeWordDetector(Context context, float threshold, Listener listener) {
        this.context = context.getApplicationContext();
        this.threshold = Math.max(0.01f, Math.min(0.99f, threshold));
        this.listener = listener;
    }

    public synchronized void start() {
        if (running) return;
        running = true;
        thread = new Thread(this::runLoop, "JarvisLocalWakeWord");
        thread.start();
    }

    public synchronized void stop() {
        running = false;
        releaseAudio();
        if (thread != null && thread != Thread.currentThread()) {
            try { thread.join(1500); } catch (InterruptedException ignored) { }
        }
        thread = null;
    }

    public synchronized void release() {
        stop();
        try { if (wakeSession != null) wakeSession.close(); } catch (Exception ignored) { }
        try { if (embeddingSession != null) embeddingSession.close(); } catch (Exception ignored) { }
        try { if (melSession != null) melSession.close(); } catch (Exception ignored) { }
        try { if (env != null) env.close(); } catch (Exception ignored) { }
        wakeSession = null;
        embeddingSession = null;
        melSession = null;
        env = null;
    }

    private void runLoop() {
        android.os.Process.setThreadPriority(android.os.Process.THREAD_PRIORITY_AUDIO);
        try {
            status("Cargando modelo local…");
            if (melSession == null) initModels();
            initBuffers();

            if (!initAudio()) {
                status("ERROR: no pude abrir el micrófono a 16 kHz");
                running = false;
                return;
            }

            status("Micrófono iniciado · decí Hey Jarvis");
            audioRecord.startRecording();
            short[] frame = new short[FRAME_SAMPLES];

            while (running) {
                int read = audioRecord.read(frame, 0, FRAME_SAMPLES);
                if (read < 0) {
                    status("ERROR de audio: " + read);
                    break;
                }
                if (read == 0) continue;

                updateLevel(frame, read);
                if (read != FRAME_SAMPLES) continue;

                addToRawBuffer(frame);
                if (rawTotalWritten < FRAME_SAMPLES + MEL_CONTEXT_SAMPLES) {
                    maybeReportStatus();
                    continue;
                }

                float[] audioSlice = getLastSamples(FRAME_SAMPLES + MEL_CONTEXT_SAMPLES);
                List<float[]> newMel = computeMel(audioSlice);
                if (newMel == null) {
                    maybeReportStatus();
                    continue;
                }

                melBuffer.addAll(newMel);
                while (melBuffer.size() > MEL_BUFFER_MAX) melBuffer.remove(0);

                if (melBuffer.size() >= MEL_WINDOW_FRAMES) {
                    int start = melBuffer.size() - MEL_WINDOW_FRAMES;
                    List<float[]> window = new ArrayList<>(MEL_WINDOW_FRAMES);
                    for (int i = start; i < melBuffer.size(); i++) window.add(melBuffer.get(i));
                    float[] embedding = computeEmbedding(window);
                    if (embedding != null) {
                        featureBuffer.add(embedding);
                        while (featureBuffer.size() > FEATURE_BUFFER_MAX) featureBuffer.remove(0);
                    }
                }

                if (featureBuffer.size() >= FEATURE_WINDOW) {
                    predictionCount++;
                    if (predictionCount > SKIP_INITIAL_PREDICTIONS) {
                        int start = featureBuffer.size() - FEATURE_WINDOW;
                        List<float[]> features = new ArrayList<>(FEATURE_WINDOW);
                        for (int i = start; i < featureBuffer.size(); i++) features.add(featureBuffer.get(i));
                        float score = runWakeModel(features);
                        if (score > maxScoreSinceStatus) maxScoreSinceStatus = score;

                        if (score >= threshold) {
                            long now = System.currentTimeMillis();
                            if (now - lastDetectionMs > 2500L) {
                                lastDetectionMs = now;
                                float detectedScore = score;
                                main.post(() -> listener.onDetected(detectedScore));
                            }
                        }
                    }
                }

                maybeReportStatus();
            }
        } catch (Throwable t) {
            status("ERROR wake local: " + shortMessage(t.getMessage()));
        } finally {
            releaseAudio();
        }
    }

    private void initModels() throws Exception {
        env = OrtEnvironment.getEnvironment();
        OrtSession.SessionOptions opts = new OrtSession.SessionOptions();
        opts.setIntraOpNumThreads(1);
        opts.setInterOpNumThreads(1);

        melSession = env.createSession(loadAsset("openwakeword/melspectrogram.onnx"), opts);
        embeddingSession = env.createSession(loadAsset("openwakeword/embedding_model.onnx"), opts);
        wakeSession = env.createSession(loadAsset("openwakeword/hey_jarvis_v0.1.onnx"), opts);
        wakeInputName = wakeSession.getInputNames().iterator().next();
    }

    private byte[] loadAsset(String path) throws Exception {
        try (java.io.InputStream in = context.getAssets().open(path);
             java.io.ByteArrayOutputStream out = new java.io.ByteArrayOutputStream()) {
            byte[] buf = new byte[8192];
            int n;
            while ((n = in.read(buf)) != -1) out.write(buf, 0, n);
            return out.toByteArray();
        }
    }

    private void initBuffers() {
        rawBuffer = new float[SAMPLE_RATE * RAW_BUFFER_SECONDS];
        rawWritePos = 0;
        rawTotalWritten = 0;
        melBuffer.clear();
        for (int i = 0; i < MEL_WINDOW_FRAMES; i++) {
            float[] row = new float[MEL_BINS];
            java.util.Arrays.fill(row, 1.0f);
            melBuffer.add(row);
        }
        featureBuffer.clear();
        for (int i = 0; i < FEATURE_WINDOW; i++) featureBuffer.add(new float[EMBEDDING_DIM]);
        predictionCount = 0;
        lastDetectionMs = 0;
        lastStatusMs = 0;
        maxScoreSinceStatus = 0f;
        levelSumSinceStatus = 0;
        levelCountSinceStatus = 0;
    }

    private boolean initAudio() {
        if (ContextCompat.checkSelfPermission(context, Manifest.permission.RECORD_AUDIO)
                != PackageManager.PERMISSION_GRANTED) {
            status("ERROR: falta permiso de micrófono");
            return false;
        }

        // MIC primero: varios teléfonos viejos entregan silencio con VOICE_RECOGNITION.
        int[] sources = new int[]{MediaRecorder.AudioSource.MIC, MediaRecorder.AudioSource.VOICE_RECOGNITION};
        int min = AudioRecord.getMinBufferSize(
                SAMPLE_RATE, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT);
        if (min <= 0) return false;

        for (int source : sources) {
            try {
                AudioRecord candidate = new AudioRecord(
                        source,
                        SAMPLE_RATE,
                        AudioFormat.CHANNEL_IN_MONO,
                        AudioFormat.ENCODING_PCM_16BIT,
                        Math.max(min, FRAME_SAMPLES * 6)
                );
                if (candidate.getState() == AudioRecord.STATE_INITIALIZED) {
                    audioRecord = candidate;
                    audioSourceInUse = source;
                    return true;
                }
                candidate.release();
            } catch (Exception ignored) { }
        }
        return false;
    }

    private void releaseAudio() {
        AudioRecord ar = audioRecord;
        audioRecord = null;
        if (ar != null) {
            try { ar.stop(); } catch (Exception ignored) { }
            try { ar.release(); } catch (Exception ignored) { }
        }
    }

    private void updateLevel(short[] frame, int n) {
        double sum = 0;
        for (int i = 0; i < n; i++) {
            double v = frame[i] / 32768.0;
            sum += v * v;
        }
        double rms = Math.sqrt(sum / Math.max(1, n));
        levelSumSinceStatus += rms;
        levelCountSinceStatus++;
    }

    private void maybeReportStatus() {
        long now = System.currentTimeMillis();
        if (now - lastStatusMs < 1800L) return;
        lastStatusMs = now;

        double rms = levelCountSinceStatus == 0 ? 0 : levelSumSinceStatus / levelCountSinceStatus;
        int pct = (int)Math.round(Math.min(100.0, rms * 500.0));
        float score = maxScoreSinceStatus;

        String src = audioSourceInUse == MediaRecorder.AudioSource.MIC ? "MIC" : "VOICE";
        status("Mic " + src + " " + pct + "% · score " + String.format(java.util.Locale.US, "%.2f", score)
                + " · umbral " + String.format(java.util.Locale.US, "%.2f", threshold));

        maxScoreSinceStatus = 0f;
        levelSumSinceStatus = 0;
        levelCountSinceStatus = 0;
    }

    private void addToRawBuffer(short[] frame) {
        for (short sample : frame) {
            rawBuffer[rawWritePos] = (float) sample;
            rawWritePos = (rawWritePos + 1) % rawBuffer.length;
        }
        rawTotalWritten += frame.length;
    }

    private float[] getLastSamples(int n) {
        float[] result = new float[n];
        int available = (int)Math.min(Math.min((long)n, (long)rawBuffer.length), rawTotalWritten);
        int readPos = (rawWritePos - available + rawBuffer.length) % rawBuffer.length;
        for (int i = 0; i < available; i++) {
            result[n - available + i] = rawBuffer[readPos];
            readPos = (readPos + 1) % rawBuffer.length;
        }
        return result;
    }

    private List<float[]> computeMel(float[] audio) {
        try (OnnxTensor input = OnnxTensor.createTensor(
                env, FloatBuffer.wrap(audio), new long[]{1, audio.length});
             OrtSession.Result result = melSession.run(Collections.singletonMap("input", input))) {

            OnnxTensor output = (OnnxTensor) result.get(0);
            long[] shape = output.getInfo().getShape();
            FloatBuffer flat = output.getFloatBuffer();
            int frames = (int) shape[2];
            int bins = (int) shape[3];

            ArrayList<float[]> out = new ArrayList<>(frames);
            for (int f = 0; f < frames; f++) {
                float[] row = new float[bins];
                for (int b = 0; b < bins; b++) row[b] = flat.get(f * bins + b) / 10.0f + 2.0f;
                out.add(row);
            }
            return out;
        } catch (Exception e) {
            status("ERROR mel: " + shortMessage(e.getMessage()));
            return null;
        }
    }

    private float[] computeEmbedding(List<float[]> melWindow) {
        try {
            float[] flatData = new float[MEL_WINDOW_FRAMES * MEL_BINS];
            for (int i = 0; i < MEL_WINDOW_FRAMES; i++) {
                System.arraycopy(melWindow.get(i), 0, flatData, i * MEL_BINS, MEL_BINS);
            }

            try (OnnxTensor input = OnnxTensor.createTensor(
                    env, FloatBuffer.wrap(flatData),
                    new long[]{1, MEL_WINDOW_FRAMES, MEL_BINS, 1});
                 OrtSession.Result result = embeddingSession.run(Collections.singletonMap("input_1", input))) {

                FloatBuffer buf = ((OnnxTensor) result.get(0)).getFloatBuffer();
                float[] embedding = new float[EMBEDDING_DIM];
                for (int i = 0; i < EMBEDDING_DIM; i++) embedding[i] = buf.get(i);
                return embedding;
            }
        } catch (Exception e) {
            status("ERROR embedding: " + shortMessage(e.getMessage()));
            return null;
        }
    }

    private float runWakeModel(List<float[]> features) {
        try {
            float[] flatData = new float[FEATURE_WINDOW * EMBEDDING_DIM];
            for (int i = 0; i < FEATURE_WINDOW; i++) {
                System.arraycopy(features.get(i), 0, flatData, i * EMBEDDING_DIM, EMBEDDING_DIM);
            }

            try (OnnxTensor input = OnnxTensor.createTensor(
                    env, FloatBuffer.wrap(flatData),
                    new long[]{1, FEATURE_WINDOW, EMBEDDING_DIM});
                 OrtSession.Result result = wakeSession.run(Collections.singletonMap(wakeInputName, input))) {
                return ((OnnxTensor) result.get(0)).getFloatBuffer().get(0);
            }
        } catch (Exception e) {
            status("ERROR modelo Jarvis: " + shortMessage(e.getMessage()));
            return 0f;
        }
    }

    private void status(String text) {
        main.post(() -> listener.onStatus(text));
    }

    private static String shortMessage(String s) {
        if (s == null || s.trim().isEmpty()) return "desconocido";
        s = s.replace('\n', ' ').trim();
        return s.length() > 90 ? s.substring(0, 90) : s;
    }
}

package truman.demo.whatsup;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Intent;
import android.os.Environment;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.util.Log;

import androidx.core.app.NotificationCompat;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.security.cert.X509Certificate;

import javax.net.ssl.HttpsURLConnection;
import javax.net.ssl.SSLContext;
import javax.net.ssl.SSLSocketFactory;
import javax.net.ssl.TrustManager;
import javax.net.ssl.X509TrustManager;

public class ConnectivityService extends Service {

    private static final String TAG = ConnectivityService.class.getSimpleName() + ".2ruman";

    public static final String ACTION_START_SYNC = "truman.demo.whatsup.START_SYNC";
    public static final String ACTION_STOP_SYNC  = "truman.demo.whatsup.STOP_SYNC";
    public static final String ACTION_PLAY       = "truman.demo.whatsup.PLAY";

    public static final String EXTRA_TEXT_MSG   = "extra_text_msg";
    public static final String EXTRA_IMAGE_PATH = "extra_image_path";

    private static final String CHANNEL_ID     = "whatsup_channel";
    private static final String SVC_CHANNEL_ID = "whatsup_svc_channel";
    private static final int    NOTIF_ID       = 1;
    private static final int    MSG_NOTIF_ID   = 2;

    private static final int SYNC_INTERVAL_MS = 5000;

    private final Handler handler = new Handler(Looper.getMainLooper());
    private boolean syncRunning = false;

    // Runnables for HTTP and TLS sync loops
    private Runnable syncHttpRunnable;
    private Runnable syncTlsRunnable;

    @Override
    public void onCreate() {
        super.onCreate();
        createNotificationChannel();
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent == null) return START_STICKY;

        String action = intent.getAction();
        if (action == null) return START_STICKY;

        switch (action) {
            case ACTION_START_SYNC:
                startForeground(NOTIF_ID, buildForegroundNotification("Syncing..."));
                startSync();
                break;
            case ACTION_STOP_SYNC:
                stopSync();
                stopForeground(STOP_FOREGROUND_REMOVE);
                stopSelf();
                break;
            case ACTION_PLAY:
                startForeground(NOTIF_ID, buildForegroundNotification("Playing..."));
                startPlay();
                break;
        }
        return START_STICKY;
    }

    private void startSync() {
        if (syncRunning) return;
        syncRunning = true;

        String ip       = Prefs.getServerIp(this);
        String httpPort = Prefs.getServerPort(this);
        String tlsPort  = Prefs.getTlsPort(this);

        syncHttpRunnable = new Runnable() {
            @Override
            public void run() {
                if (!syncRunning) return;
                new Thread(() -> {
                    boolean acked = doSyncRequest("http://" + ip + ":" + httpPort + "/sync");
                    handler.post(() -> {
                        if (!syncRunning) return;
                        if (acked) {
                            syncRunning = false;
                            handler.removeCallbacks(syncTlsRunnable);
                            stopForeground(STOP_FOREGROUND_REMOVE);
                            stopSelf();
                        } else {
                            handler.postDelayed(syncHttpRunnable, SYNC_INTERVAL_MS);
                        }
                    });
                }).start();
            }
        };

        syncTlsRunnable = new Runnable() {
            @Override
            public void run() {
                if (!syncRunning) return;
                new Thread(() -> {
                    boolean acked = doSyncRequest("https://" + ip + ":" + tlsPort + "/sync");
                    handler.post(() -> {
                        if (!syncRunning) return;
                        if (acked) {
                            syncRunning = false;
                            handler.removeCallbacks(syncHttpRunnable);
                            stopForeground(STOP_FOREGROUND_REMOVE);
                            stopSelf();
                        } else {
                            handler.postDelayed(syncTlsRunnable, SYNC_INTERVAL_MS);
                        }
                    });
                }).start();
            }
        };

        handler.post(syncHttpRunnable);
        handler.post(syncTlsRunnable);
    }

    private void stopSync() {
        syncRunning = false;
        if (syncHttpRunnable != null) handler.removeCallbacks(syncHttpRunnable);
        if (syncTlsRunnable  != null) handler.removeCallbacks(syncTlsRunnable);
    }

    private boolean doSyncRequest(String urlStr) {
        Log.i(TAG, "doSync() - url: " + urlStr);
        try {
            URL url = new URL(urlStr);
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            if (conn instanceof HttpsURLConnection) {
                HttpsURLConnection https = (HttpsURLConnection) conn;
                https.setSSLSocketFactory(getTrustAllSslSocketFactory());
                https.setHostnameVerifier((hostname, session) -> true);
            }
            conn.setRequestMethod("GET");
            conn.setConnectTimeout(3000);
            conn.setReadTimeout(3000);
            int code = conn.getResponseCode();
            conn.disconnect();
            return code == HttpURLConnection.HTTP_OK;
        } catch (Exception e) {
            Log.d(TAG, "Filed to sync: " + e);
            return false;
        }
    }

    private SSLSocketFactory getTrustAllSslSocketFactory() {
        try {
            TrustManager[] trustAll = new TrustManager[]{
                new X509TrustManager() {
                    public void checkClientTrusted(X509Certificate[] chain, String authType) {}
                    public void checkServerTrusted(X509Certificate[] chain, String authType) {}
                    public X509Certificate[] getAcceptedIssuers() { return new X509Certificate[0]; }
                }
            };
            SSLContext sc = SSLContext.getInstance("TLS");
            sc.init(null, trustAll, new java.security.SecureRandom());
            return sc.getSocketFactory();
        } catch (Exception e) {
            Log.e(TAG, "getTrustAllSslSocketFactory failed: " + e);
            return null;
        }
    }

    private void startPlay() {
        int timeGap = Prefs.getTimeGap(this);
        String url  = "http://" + Prefs.getServerIp(this) + ":" + Prefs.getServerPort(this) + "/message";

        new Thread(() -> {
            try {
                Thread.sleep(timeGap);
            } catch (InterruptedException ignored) {}

            // Step 1: receive image (no notification)
            String imagePath = fetchImage(url);

            // Step 2: receive text message → show notification
            String text = fetchText(url);
            if (text != null) {
                sendMessageNotification(text, imagePath);
            }
        }).start();
    }

    private String fetchImage(String urlStr) {
        try {
            HttpURLConnection conn = openConnection(urlStr);
            if (conn == null) return null;
            String contentType = conn.getContentType();
            if (contentType != null && contentType.startsWith("image/")) {
                String path = saveImageFromConnection(conn);
                conn.disconnect();
                return path;
            }
            conn.disconnect();
        } catch (Exception e) {
            Log.e(TAG, "fetchImage failed: " + e.getMessage());
        }
        return null;
    }

    private String fetchText(String urlStr) {
        try {
            HttpURLConnection conn = openConnection(urlStr);
            if (conn == null) return null;
            byte[] bytes = readAllBytes(conn.getInputStream());
            conn.disconnect();
            return new String(bytes).trim();
        } catch (Exception e) {
            Log.e(TAG, "fetchText failed: " + e.getMessage());
        }
        return null;
    }

    private HttpURLConnection openConnection(String urlStr) {
        try {
            URL url = new URL(urlStr);
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("GET");
            conn.setConnectTimeout(5000);
            conn.setReadTimeout(5000);
            if (conn.getResponseCode() != HttpURLConnection.HTTP_OK) {
                conn.disconnect();
                return null;
            }
            return conn;
        } catch (Exception e) {
            Log.e(TAG, "openConnection failed: " + e.getMessage());
            return null;
        }
    }

    private String saveImageFromConnection(HttpURLConnection conn) {
        File dir = new File(Environment.getExternalStorageDirectory(),
                "Android/media/truman.demo.whatsup/WhatsUp/Media/WhatsUp Images");
        if (!dir.exists() && !dir.mkdirs()) {
            Log.e(TAG, "Cannot create media directory");
            return null;
        }
        File outFile = new File(dir, "wa_img_" + System.currentTimeMillis() + ".jpg");
        try (InputStream in = conn.getInputStream();
             FileOutputStream out = new FileOutputStream(outFile)) {
            byte[] buf = new byte[4096];
            int len;
            while ((len = in.read(buf)) != -1) out.write(buf, 0, len);
            return outFile.getAbsolutePath();
        } catch (IOException e) {
            Log.e(TAG, "saveImage failed: " + e.getMessage());
            return null;
        }
    }

    private void sendMessageNotification(String text, String imagePath) {
        Intent chatIntent = new Intent(this, ChatActivity.class);
        chatIntent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        if (text      != null) chatIntent.putExtra(EXTRA_TEXT_MSG,   text);
        if (imagePath != null) chatIntent.putExtra(EXTRA_IMAGE_PATH, imagePath);

        PendingIntent pi = PendingIntent.getActivity(this, 0, chatIntent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);

        String preview = (text != null) ? text : "📷 Photo";
        Notification notif = new NotificationCompat.Builder(this, CHANNEL_ID)
                .setSmallIcon(android.R.drawable.ic_dialog_email)
                .setContentTitle(Prefs.getPartnerName(this))
                .setContentText(preview)
                .setContentIntent(pi)
                .setAutoCancel(true)
                .setPriority(NotificationCompat.PRIORITY_HIGH)
                .setDefaults(NotificationCompat.DEFAULT_ALL)
                .build();

        NotificationManager nm = getSystemService(NotificationManager.class);
        nm.notify(MSG_NOTIF_ID, notif);
    }

    private Notification buildForegroundNotification(String text) {
        return new NotificationCompat.Builder(this, SVC_CHANNEL_ID)
                .setSmallIcon(android.R.drawable.ic_dialog_info)
                .setContentTitle("WhatsUp")
                .setContentText(text)
                .setPriority(NotificationCompat.PRIORITY_MIN)
                .build();
    }

    private void createNotificationChannel() {
        NotificationManager nm = getSystemService(NotificationManager.class);

        // 메시지 알림 채널 (팝업)
        NotificationChannel msgCh = new NotificationChannel(
                CHANNEL_ID, "WhatsUp Messages", NotificationManager.IMPORTANCE_HIGH);
        nm.createNotificationChannel(msgCh);

        // 서비스 상태 채널 (완전 무음, 상태바 아이콘 없음)
        NotificationChannel svcCh = new NotificationChannel(
                SVC_CHANNEL_ID, "WhatsUp Service", NotificationManager.IMPORTANCE_MIN);
        svcCh.setShowBadge(false);
        nm.createNotificationChannel(svcCh);
    }

    private byte[] readAllBytes(InputStream in) throws IOException {
        byte[] buf = new byte[4096];
        java.io.ByteArrayOutputStream baos = new java.io.ByteArrayOutputStream();
        int len;
        while ((len = in.read(buf)) != -1) baos.write(buf, 0, len);
        return baos.toByteArray();
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    @Override
    public void onDestroy() {
        stopSync();
        super.onDestroy();
    }
}

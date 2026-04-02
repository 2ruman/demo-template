package truman.demo.whatsup;

import android.content.Context;
import android.content.SharedPreferences;

public class Prefs {
    private static final String PREF_NAME = "app_global";

    public static final String KEY_START_ON_CMD = "start_on_cmd";
    public static final String KEY_SERVER_IP    = "server_ip";
    public static final String KEY_SERVER_PORT  = "server_port";
    public static final String KEY_TLS_PORT     = "tls_port";
    public static final String KEY_PARTNER_NAME = "partner_name";
    public static final String KEY_TIME_GAP     = "time_gap";
    public static final String KEY_ECHO_MODE    = "echo_mode";

    public static SharedPreferences get(Context ctx) {
        return ctx.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
    }

    public static boolean isStartOnCmd(Context ctx) {
        return get(ctx).getBoolean(KEY_START_ON_CMD, true);
    }

    public static String getServerIp(Context ctx) {
        return get(ctx).getString(KEY_SERVER_IP, "127.0.0.1");
    }

    public static String getServerPort(Context ctx) {
        return get(ctx).getString(KEY_SERVER_PORT, "12345");
    }

    public static String getTlsPort(Context ctx) {
        return get(ctx).getString(KEY_TLS_PORT, "23456");
    }

    public static String getPartnerName(Context ctx) {
        return get(ctx).getString(KEY_PARTNER_NAME, "Mallory");
    }

    public static int getTimeGap(Context ctx) {
        return get(ctx).getInt(KEY_TIME_GAP, 5000);
    }

    public static boolean isEchoMode(Context ctx) {
        return get(ctx).getBoolean(KEY_ECHO_MODE, false);
    }
}

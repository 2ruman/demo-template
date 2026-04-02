package truman.demo.whatsup;

import android.content.SharedPreferences;
import android.os.Bundle;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.widget.SwitchCompat;

public class SettingsActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_settings);

        SwitchCompat swStartOnCmd = findViewById(R.id.sw_start_on_cmd);
        SwitchCompat swEchoMode   = findViewById(R.id.sw_echo_mode);
        EditText etServerIp       = findViewById(R.id.et_server_ip);
        EditText etServerPort     = findViewById(R.id.et_server_port);
        EditText etTlsPort        = findViewById(R.id.et_tls_port);
        EditText etPartnerName    = findViewById(R.id.et_partner_name);
        EditText etTimeGap        = findViewById(R.id.et_time_gap);
        Button   btnSave          = findViewById(R.id.btn_save);

        // Load current values
        swStartOnCmd.setChecked(Prefs.isStartOnCmd(this));
        swEchoMode.setChecked(Prefs.isEchoMode(this));
        etServerIp.setText(Prefs.getServerIp(this));
        etServerPort.setText(Prefs.getServerPort(this));
        etTlsPort.setText(Prefs.getTlsPort(this));
        etPartnerName.setText(Prefs.getPartnerName(this));
        etTimeGap.setText(String.valueOf(Prefs.getTimeGap(this)));

        btnSave.setOnClickListener(v -> {
            SharedPreferences.Editor editor = Prefs.get(this).edit();
            editor.putBoolean(Prefs.KEY_START_ON_CMD, swStartOnCmd.isChecked());
            editor.putBoolean(Prefs.KEY_ECHO_MODE,    swEchoMode.isChecked());
            editor.putString(Prefs.KEY_SERVER_IP,   etServerIp.getText().toString().trim());
            editor.putString(Prefs.KEY_SERVER_PORT, etServerPort.getText().toString().trim());
            editor.putString(Prefs.KEY_TLS_PORT,    etTlsPort.getText().toString().trim());
            editor.putString(Prefs.KEY_PARTNER_NAME, etPartnerName.getText().toString().trim());
            try {
                editor.putInt(Prefs.KEY_TIME_GAP,
                        Integer.parseInt(etTimeGap.getText().toString().trim()));
            } catch (NumberFormatException e) {
                editor.putInt(Prefs.KEY_TIME_GAP, 5000);
            }
            editor.apply();
            Toast.makeText(this, "Saved", Toast.LENGTH_SHORT).show();
            finish();
        });
    }
}

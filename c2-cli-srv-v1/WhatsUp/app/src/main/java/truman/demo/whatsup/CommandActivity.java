package truman.demo.whatsup;

import android.content.Intent;
import android.os.Bundle;
import android.widget.Button;

import androidx.appcompat.app.AppCompatActivity;

public class CommandActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_command);

        Button btnSettings = findViewById(R.id.btn_settings);
        Button btnStart    = findViewById(R.id.btn_start);
        Button btnStop     = findViewById(R.id.btn_stop);
        Button btnPlay     = findViewById(R.id.btn_play);
        Button btnChat     = findViewById(R.id.btn_chat);

        btnSettings.setOnClickListener(v ->
                startActivity(new Intent(this, SettingsActivity.class)));

        btnStart.setOnClickListener(v -> {
            Intent svc = new Intent(this, ConnectivityService.class);
            svc.setAction(ConnectivityService.ACTION_START_SYNC);
            startForegroundService(svc);
        });

        btnStop.setOnClickListener(v -> {
            Intent svc = new Intent(this, ConnectivityService.class);
            svc.setAction(ConnectivityService.ACTION_STOP_SYNC);
            startService(svc);
        });

        btnPlay.setOnClickListener(v -> {
            Intent svc = new Intent(this, ConnectivityService.class);
            svc.setAction(ConnectivityService.ACTION_PLAY);
            startForegroundService(svc);
            finish();
        });

        btnChat.setOnClickListener(v ->
                startActivity(new Intent(this, ChatActivity.class)));
    }
}

package truman.demo.whatsup;

import android.content.Intent;
import android.os.Bundle;
import android.text.TextUtils;
import android.widget.EditText;

import androidx.appcompat.app.AppCompatActivity;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.google.android.material.floatingactionbutton.FloatingActionButton;

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Locale;
import java.util.regex.Pattern;

public class ChatActivity extends AppCompatActivity {

    private static final Pattern CMD_PATTERN = Pattern.compile("^\\..+");

    private static final List<Message> messageHistory = new ArrayList<>();

    private MessageAdapter adapter;
    private RecyclerView   rvMessages;
    private EditText       etMessage;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        setContentView(R.layout.activity_chat);

        String partnerName = Prefs.getPartnerName(this);
        android.widget.TextView tvName = findViewById(R.id.tv_partner_name);
        if (tvName != null) tvName.setText(partnerName);

        findViewById(R.id.btn_back).setOnClickListener(v -> finish());

        applyWindowInsets();

        rvMessages = findViewById(R.id.rv_messages);
        etMessage  = findViewById(R.id.et_message);
        FloatingActionButton btnSend = findViewById(R.id.btn_send);

        adapter = new MessageAdapter(messageHistory);
        rvMessages.setLayoutManager(new LinearLayoutManager(this));
        rvMessages.setAdapter(adapter);
        scrollToBottom();

        btnSend.setOnClickListener(v -> handleSend());

        handleIncomingIntent(getIntent());
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        handleIncomingIntent(intent);
    }

    private void handleIncomingIntent(Intent intent) {
        if (intent == null) return;
        String text      = intent.getStringExtra(ConnectivityService.EXTRA_TEXT_MSG);
        String imagePath = intent.getStringExtra(ConnectivityService.EXTRA_IMAGE_PATH);
        if (imagePath != null) {
            addMessage(new Message(Message.TYPE_RECEIVED, null, imagePath, now()));
        }
        if (text != null) {
            addMessage(new Message(Message.TYPE_RECEIVED, text, null, now()));
        }
    }

    private void handleSend() {
        String input = etMessage.getText().toString().trim();
        if (TextUtils.isEmpty(input)) return;
        etMessage.setText("");

        if (CMD_PATTERN.matcher(input).matches()) {
            handleCommand(input);
        } else {
            addMessage(new Message(Message.TYPE_SENT, input, null, now()));
            if (Prefs.isEchoMode(this)) {
                addMessage(new Message(Message.TYPE_RECEIVED, input, null, now()));
            }
        }
    }

    private void handleCommand(String cmd) {
        switch (cmd) {
            case ".settings":
                startActivity(new Intent(this, SettingsActivity.class));
                break;
            case ".cmd":
                startActivity(new Intent(this, CommandActivity.class));
                finish();
                break;
            case ".clear":
                messageHistory.clear();
                adapter.notifyDataSetChanged();
                break;
            case ".play":
                Intent svc = new Intent(this, ConnectivityService.class);
                svc.setAction(ConnectivityService.ACTION_PLAY);
                startForegroundService(svc);
                break;
            default:
                addMessage(new Message(Message.TYPE_RECEIVED,
                        "Unknown command: " + cmd, null, now()));
                break;
        }
    }

    private void addMessage(Message msg) {
        messageHistory.add(msg);
        adapter.notifyItemInserted(messageHistory.size() - 1);
        scrollToBottom();
    }

    private void scrollToBottom() {
        if (!messageHistory.isEmpty()) {
            rvMessages.scrollToPosition(messageHistory.size() - 1);
        }
    }

    private String now() {
        return new SimpleDateFormat("HH:mm", Locale.getDefault()).format(new Date());
    }

    private void applyWindowInsets() {
        android.view.View toolbar  = findViewById(R.id.toolbar);
        android.view.View inputBar = (android.view.View) findViewById(R.id.btn_send).getParent();
        int baseBottom = inputBar.getPaddingBottom();
        ViewCompat.setOnApplyWindowInsetsListener(findViewById(android.R.id.content), (v, insets) -> {
            int statusBar = insets.getInsets(WindowInsetsCompat.Type.statusBars()).top;
            int navBar    = insets.getInsets(WindowInsetsCompat.Type.navigationBars()).bottom;
            int ime       = insets.getInsets(WindowInsetsCompat.Type.ime()).bottom;
            toolbar.setPadding(toolbar.getPaddingLeft(), statusBar,
                    toolbar.getPaddingRight(), toolbar.getPaddingBottom());
            int bottom = ime > 0 ? ime : Math.max(navBar, baseBottom);
            inputBar.setPadding(inputBar.getPaddingLeft(), inputBar.getPaddingTop(),
                    inputBar.getPaddingRight(), bottom);
            return insets;
        });
    }
}

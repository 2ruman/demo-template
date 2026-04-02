package truman.demo.whatsup;

public class Message {
    public static final int TYPE_SENT     = 0;
    public static final int TYPE_RECEIVED = 1;

    public final int    type;
    public final String text;
    public final String imagePath; // null if text-only
    public final String time;

    public Message(int type, String text, String imagePath, String time) {
        this.type      = type;
        this.text      = text;
        this.imagePath = imagePath;
        this.time      = time;
    }
}

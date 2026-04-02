package truman.demo.whatsup;

import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Matrix;
import android.os.Bundle;
import android.view.MotionEvent;
import android.view.ScaleGestureDetector;
import android.widget.ImageView;

import androidx.appcompat.app.AppCompatActivity;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;

public class ImageViewerActivity extends AppCompatActivity {

    public static final String EXTRA_IMAGE_PATH = "extra_image_path";

    private ImageView ivFull;
    private Matrix matrix = new Matrix();
    private float scaleFactor = 1.0f;
    private ScaleGestureDetector scaleDetector;

    // 드래그용
    private float lastX, lastY;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_image_viewer);

        ivFull = findViewById(R.id.iv_full);
        android.view.View btnClose = findViewById(R.id.btn_close);
        btnClose.setOnClickListener(v -> finish());
        ViewCompat.setOnApplyWindowInsetsListener(btnClose, (v, insets) -> {
            int statusBar = insets.getInsets(WindowInsetsCompat.Type.statusBars()).top;
            android.view.ViewGroup.MarginLayoutParams lp =
                    (android.view.ViewGroup.MarginLayoutParams) v.getLayoutParams();
            lp.topMargin = statusBar + (int) (16 * getResources().getDisplayMetrics().density);
            v.setLayoutParams(lp);
            return insets;
        });

        String path = getIntent().getStringExtra(EXTRA_IMAGE_PATH);
        if (path != null) {
            Bitmap bmp = BitmapFactory.decodeFile(path);
            if (bmp != null) {
                ivFull.setImageBitmap(bmp);
                ivFull.setScaleType(ImageView.ScaleType.MATRIX);
                ivFull.setImageMatrix(matrix);
            }
        }

        scaleDetector = new ScaleGestureDetector(this, new ScaleGestureDetector.SimpleOnScaleGestureListener() {
            @Override
            public boolean onScale(ScaleGestureDetector detector) {
                float factor = detector.getScaleFactor();
                scaleFactor = Math.max(0.5f, Math.min(scaleFactor * factor, 8.0f));
                matrix.setScale(scaleFactor, scaleFactor,
                        detector.getFocusX(), detector.getFocusY());
                ivFull.setImageMatrix(matrix);
                return true;
            }
        });

        ivFull.setOnTouchListener((v, event) -> {
            scaleDetector.onTouchEvent(event);
            if (!scaleDetector.isInProgress()) {
                switch (event.getActionMasked()) {
                    case MotionEvent.ACTION_DOWN:
                        lastX = event.getX();
                        lastY = event.getY();
                        break;
                    case MotionEvent.ACTION_MOVE:
                        matrix.postTranslate(event.getX() - lastX, event.getY() - lastY);
                        ivFull.setImageMatrix(matrix);
                        lastX = event.getX();
                        lastY = event.getY();
                        break;
                }
            }
            return true;
        });
    }
}

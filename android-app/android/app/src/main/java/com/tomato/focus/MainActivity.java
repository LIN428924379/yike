package com.tomato.focus;

import android.graphics.Color;
import android.os.Build;
import android.os.Bundle;
import android.view.View;

import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {

    @Override
    public void onCreate(Bundle savedInstanceState) {
        // 注册自定义插件（必须在 super.onCreate 之前）
        registerPlugin(ShellPlugin.class);

        super.onCreate(savedInstanceState);

        // 让窗口铺满整屏 —— 也就是"网页一直画到状态栏、导航栏底下"。
        // 系统栏那块由网页自己上色，这样上下就不会再出现两条对不上的色条。
        //
        // 说明：安卓 15 起系统强制边到边，光靠主题里的 statusBarColor 已经无效
        // （那个属性被废弃了），所以必须在这里从窗口层面处理。
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            getWindow().setDecorFitsSystemWindows(false);
        } else {
            getWindow().getDecorView().setSystemUiVisibility(
                    View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                            | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                            | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN);
        }

        getWindow().setStatusBarColor(Color.TRANSPARENT);
        getWindow().setNavigationBarColor(Color.TRANSPARENT);
    }
}

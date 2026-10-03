package com.tomato.focus;

import android.graphics.Color;
import android.os.Build;
import android.view.View;
import android.view.WindowInsets;
import android.view.WindowInsetsController;

import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

/**
 * 让"网页铺满整屏"这件事真正成立的小工具。
 *
 * 为什么要自己写：安卓 15 起系统强制边到边，主题里 statusBarColor 之类的设置
 * 全部被废弃；Capacitor 自带的 SystemBars 又要求网页内核版本 >= 140 才肯让网页
 * 铺满（版本不够就把网页缩进，露出底下的窗口底色 —— 也就是用户看到的那两条色条）。
 * 而安卓 WebView 本身不支持 env(safe-area-inset-*)，网页根本拿不到系统栏高度。
 *
 * 所以这里从原生侧把三件事补齐：
 *   1. 告诉网页系统栏有多高，它好留出正确的内边距
 *   2. 窗口底色跟着 App 主题走（铺满后露出来的就是它）
 *   3. 状态栏图标颜色跟着主题走（不然浅色主题下白图标会看不见）
 */
@CapacitorPlugin(name = "Shell")
public class ShellPlugin extends Plugin {

    private float density() {
        return getActivity().getResources().getDisplayMetrics().density;
    }

    /** 系统栏高度，单位 dp —— 网页里 1dp 正好等于 1 个 CSS 像素 */
    @PluginMethod
    public void insets(PluginCall call) {
        JSObject out = new JSObject();
        int top = 0;
        int bottom = 0;
        try {
            WindowInsets insets = getActivity().getWindow().getDecorView().getRootWindowInsets();
            if (insets != null) {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                    android.graphics.Insets bars = insets.getInsets(WindowInsets.Type.systemBars());
                    top = bars.top;
                    bottom = bars.bottom;
                } else {
                    top = insets.getSystemWindowInsetTop();
                    bottom = insets.getSystemWindowInsetBottom();
                }
            }
        } catch (Exception err) {
            // 拿不到就报 0，网页会用兜底值
        }
        out.put("top", Math.round(top / density()));
        out.put("bottom", Math.round(bottom / density()));
        call.resolve(out);
    }

    /** 跟着 App 主题走：窗口底色 + 系统栏图标颜色 */
    @PluginMethod
    public void theme(final PluginCall call) {
        final boolean light = Boolean.TRUE.equals(call.getBoolean("light", Boolean.FALSE));

        getActivity().runOnUiThread(() -> {
            try {
                // 铺满之后系统栏是透明的，底下露出来的是窗口底色 ——
                // 设成和界面同一个颜色，上下就不会有色条。
                int background = Color.parseColor(light ? "#F2F4F9" : "#0F1116");
                getActivity().getWindow().getDecorView().setBackgroundColor(background);
                getActivity().getWindow().setStatusBarColor(Color.TRANSPARENT);
                getActivity().getWindow().setNavigationBarColor(Color.TRANSPARENT);

                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                    WindowInsetsController controller = getActivity().getWindow().getInsetsController();
                    if (controller != null) {
                        int mask = WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS
                                | WindowInsetsController.APPEARANCE_LIGHT_NAVIGATION_BARS;
                        // light = true 表示"背景是浅色，图标请用深色"
                        controller.setSystemBarsAppearance(light ? mask : 0, mask);
                    }
                } else {
                    View decor = getActivity().getWindow().getDecorView();
                    int flags = decor.getSystemUiVisibility();
                    if (light) {
                        flags |= View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR;
                    } else {
                        flags &= ~View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR;
                    }
                    decor.setSystemUiVisibility(flags);
                }
            } catch (Exception err) {
                // 主题没跟上也不影响用
            }
            call.resolve();
        });
    }
}

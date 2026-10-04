package com.tomato.focus;

import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.content.Context;
import android.content.Intent;
import android.graphics.Color;
import android.media.AudioAttributes;
import android.net.Uri;
import android.os.Build;
import android.os.PowerManager;
import android.provider.Settings;
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

    /** 到点提醒的通知通道 id。
        换 id 是唯一的"改通道设置"的办法：建好之后系统不允许再改。
        但试过两次换成 v3，两次通知都不响了 —— 所以退回 v2，不再动。 */
    private static final String ALARM_CHANNEL_ID = "focus-alarm-v2";

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

    /**
     * 问一句：系统有没有把本 App 限制在省电模式里（也就是"允许后台耗电"关了没）。
     */
    @PluginMethod
    public void checkBackgroundPower(final PluginCall call) {
        JSObject out = new JSObject();
        boolean ignoring = false;
        try {
            PowerManager power = (PowerManager) getContext().getSystemService(Context.POWER_SERVICE);
            if (power != null) {
                ignoring = power.isIgnoringBatteryOptimizations(getContext().getPackageName());
            }
        } catch (Exception err) {
            // 查不到就当"没限制"，别打扰用户
            ignoring = true;
        }
        out.put("ignoring", ignoring);
        call.resolve(out);
    }

    /**
     * 弹出系统的「是否允许后台运行 / 忽略电池优化」对话框。
     *
     * 为什么必须做这一步：小米、华为这类系统，如果没把 App 加进"允许后台耗电"，
     * 那么 App 被清掉之后，系统【不再叫醒它】—— 于是一切都排好了、权限也给了，
     * 到点就是不响。而这个开关藏在设置里很深，让用户自己找太折磨人。
     *
     * ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS 会直接弹一个系统对话框，
     * 用户点一下「允许」就行 —— 比翻五层设置友好得多。
     */
    @PluginMethod
    public void requestBackgroundPower(final PluginCall call) {
        JSObject out = new JSObject();
        boolean ignoring = false;
        boolean opened = false;
        try {
            PowerManager power = (PowerManager) getContext().getSystemService(Context.POWER_SERVICE);
            String pkg = getContext().getPackageName();
            if (power != null) ignoring = power.isIgnoringBatteryOptimizations(pkg);

            if (!ignoring && getActivity() != null) {
                Intent intent = new Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS);
                intent.setData(Uri.parse("package:" + pkg));
                getActivity().startActivity(intent);
                opened = true;
            }
        } catch (Exception err) {
            // 打不开就退回让用户自己去设置里找
        }
        out.put("ignoring", ignoring);
        out.put("opened", opened);
        call.resolve(out);
    }

    /**
     * 建好「到点提醒」的通知通道，并把结果告诉网页。
     *
     * 为什么自己建、不用通知插件：安卓的**铃声和震动模式是挂在通道上的**，
     * 而 Capacitor 那个插件只能"开/关震动"，给不了自定义的震动节奏 ✗
     * 铃声也只能填 res/raw 里的文件名，填 "default" 会被当成真去找一个叫
     * default 的音频文件（找不到就变成静音通道 ✗ —— 之前那个 bug 就是这么来的）。
     *
     * 两个血的教训写在这里：
     *  1. 通道【必须】建成功 —— 通知发到一个不存在的通道，系统会静默丢掉，
     *     用户什么都看不到。所以设置铃声失败时，要退回一个"没有自定义铃声、
     *     但至少存在"的通道，绝不能让 createNotificationChannel 被跳过。
     *  2. 返回值必须能看出"到底建成功没有"，网页那边要靠它判断。
     */
    @PluginMethod
    public void prepareAlarm(final PluginCall call) {
        JSObject out = new JSObject();
        out.put("ok", false);
        out.put("sound", false);

        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) {
            // 安卓 8 以下没有通道这个概念，直接用系统默认
            out.put("ok", true);
            call.resolve(out);
            return;
        }

        try {
            NotificationManager manager =
                    (NotificationManager) getContext().getSystemService(Context.NOTIFICATION_SERVICE);
            if (manager == null) {
                call.resolve(out);
                return;
            }

            // 已经建好了就不动它（通道设置建好之后系统不允许改）
            if (manager.getNotificationChannel(ALARM_CHANNEL_ID) != null) {
                out.put("ok", true);
                out.put("sound", true);
                call.resolve(out);
                return;
            }

            boolean soundOk = false;
            try {
                NotificationChannel channel = new NotificationChannel(
                        ALARM_CHANNEL_ID, "到点提醒", NotificationManager.IMPORTANCE_HIGH);
                channel.setDescription("番茄钟结束时提醒你");
                channel.enableVibration(true);
                channel.setVibrationPattern(new long[]{0, 700, 300, 700, 300, 700, 300, 1300});

                // 铃声：用打包在 App 里的 pomodoro.wav（3.6 秒，音量拉满）
                int soundId = getContext().getResources()
                        .getIdentifier("pomodoro", "raw", getContext().getPackageName());
                if (soundId != 0) {
                    AudioAttributes attributes = new AudioAttributes.Builder()
                            .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                            .setUsage(AudioAttributes.USAGE_NOTIFICATION)
                            .build();
                    channel.setSound(
                            Uri.parse("android.resource://" + getContext().getPackageName() + "/" + soundId),
                            attributes);
                    soundOk = true;
                }
                manager.createNotificationChannel(channel);
            } catch (Exception err) {
                soundOk = false;
            }

            // 兜底：上面那步要是没建成，这里必须补一个"能用的"通道。
            // 没有通道 = 通知被系统丢掉 = 用户什么都看不到。
            if (manager.getNotificationChannel(ALARM_CHANNEL_ID) == null) {
                try {
                    NotificationChannel fallback = new NotificationChannel(
                            ALARM_CHANNEL_ID, "到点提醒", NotificationManager.IMPORTANCE_HIGH);
                    fallback.setDescription("番茄钟结束时提醒你");
                    fallback.enableVibration(true);
                    fallback.setVibrationPattern(new long[]{0, 700, 300, 700, 300, 700, 300, 1300});
                    manager.createNotificationChannel(fallback);
                } catch (Exception err) {
                    // 实在建不了就没办法了，下面的 ok 会是 false
                }
            }

            out.put("ok", manager.getNotificationChannel(ALARM_CHANNEL_ID) != null);
            out.put("sound", soundOk);
        } catch (Exception err) {
            // 兜底失败
        }
        call.resolve(out);
    }
}

# -*- coding: utf-8 -*-
"""
金属链板成本计算器 — Android 版 (Kivy)
复用与桌面版完全相同的计算引擎 chainplate_calc.py（纯 Python，无界面依赖）。
运行: python main.py  (桌面测试) / 由 buildozer 打包为 APK (手机)
"""
import math
import os

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.graphics import Color, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.switch import Switch
from kivy.uix.textinput import TextInput

from chainplate_calc import (DEFAULT_FORMULAS, MATERIAL_KEYS, MATERIAL_NAMES,
                             PITCHES, SAMPLE_ENV, compute, default_settings,
                             eval_expr, format_result, load_settings,
                             save_settings)

# ==================== 注册中文字体 ====================
# Kivy 默认字体(Roboto)不含中文，必须注册一个支持中文的 TTF 字体。
# 字体文件 chinese_font.ttf 需要与 main.py 放在同一目录（buildozer 会打包进去）。
_FONT_DIR = os.path.dirname(os.path.abspath(__file__))
_FONT_PATH = os.path.join(_FONT_DIR, "chinese_font.ttf")
if os.path.exists(_FONT_PATH):
    LabelBase.register(name="Chinese", regular=_FONT_PATH)
    _FONT_NAME = "Chinese"
else:
    _FONT_NAME = "Roboto"  # 回退：开发环境缺少字体文件时用默认字体

# 键盘弹出时避免遮挡输入框
try:
    Window.softinput_mode = "below_target"
except Exception:
    pass

MAT_OPTIONS = [MATERIAL_NAMES[k] for k in MATERIAL_KEYS]
SAME_OPTION = "与板相同"

# (显示名, 公式槽位, 变量提示)
FORMULA_FIELDS = [
    ("板价格", "plate", "变量: pin_d pitch thickness width sheet_price density pin_pi cut_fee punch_fee weld_fee"),
    ("穿杆价格", "pin", "变量: pin_d width chain_width sheet_price pin_coef pin_fee"),
    ("横挡板价格", "cross", "变量: length height thickness sheet_price density flight_margin cross_fee"),
    ("侧挡板价格", "side", "变量: pitch chain_width height thickness sheet_price density flight_margin side_fee"),
    ("切割费·薄板档 平费", "cut_b1_flat", "变量: flat_fee"),
    ("切割费·薄板档 超宽", "cut_b1_wide", "变量: width"),
    ("切割费·中板档 平费", "cut_b2_flat", "变量: flat_fee"),
    ("切割费·中板档 超宽", "cut_b2_wide", "变量: width formula_extra"),
    ("切割费·厚板档 平费", "cut_b3_flat", "变量: flat_fee"),
    ("切割费·厚板档 超宽", "cut_b3_wide", "变量: width formula_extra"),
    ("焊接费·小直径", "weld_small", "变量: fee_small"),
    ("焊接费·大直径", "weld_large", "变量: fee_large"),
    ("冲孔·自动平费", "punch_auto_flat", "变量: auto_flat_fee"),
    ("冲孔·自动超宽", "punch_auto_wide", "变量: width"),
    ("每米总价", "total", "变量: per_meter plate pin chain_total side_total cross_total punch ball_total wheel_total labor"),
]

COLOR_TOTAL_BG = (1.00, 0.96, 0.84, 1)   # 醒目总价底色(浅黄)
COLOR_TOTAL_FG = (0.75, 0.22, 0.17, 1)   # 醒目总价文字(红)
COLOR_ERR = (0.85, 0.20, 0.20, 1)
COLOR_NORMAL = (0.10, 0.10, 0.10, 1)

# 移动端适配的尺寸常量
_LABEL_WIDTH = 100       # 标签固定宽度(dp)
_ROW_HEIGHT = 48         # 每行高度(dp)
_INPUT_HEIGHT = 46       # 输入框高度(dp)
_TITLE_HEIGHT = 44       # 标题栏高度(dp)
_BTN_HEIGHT = 54         # 按钮行高度(dp)
_TOTAL_BAR_HEIGHT = 72   # 总价栏高度(dp)
_FS_LABEL = 15           # 标签字号
_FS_INPUT = 16           # 输入框字号
_FS_TITLE = 19           # 标题字号
_FS_BTN_MAIN = 20        # 主按钮字号
_FS_BTN_SUB = 15         # 副按钮字号
_FS_TOTAL = 24           # 总价字号
_FS_DETAIL = 14          # 明细字号


def _label(text, height=None, **kw):
    """创建统一字体的标签"""
    if height is None:
        height = _ROW_HEIGHT
    lbl = Label(text=text, size_hint_y=None, height=height,
                font_name=_FONT_NAME, font_size=_FS_LABEL, **kw)
    return lbl


def _num_input(text="", filt="float", hint=""):
    """创建统一字体的数字输入框"""
    return TextInput(text=text, input_filter=filt, multiline=False,
                     size_hint_y=None, height=_INPUT_HEIGHT, hint_text=hint,
                     font_name=_FONT_NAME, font_size=_FS_INPUT)


def _btn(text, font_size=None, **kw):
    """创建统一字体的按钮"""
    if font_size is None:
        font_size = _FS_BTN_SUB
    return Button(text=text, font_name=_FONT_NAME, font_size=font_size, **kw)


def _spinner(text, values):
    """创建统一字体的下拉框"""
    return Spinner(text=text, values=values,
                   size_hint_y=None, height=_INPUT_HEIGHT,
                   font_name=_FONT_NAME, font_size=_FS_INPUT)


class ChainPlateApp(App):
    title = "金属链板成本计算器"

    # ---------------- 初始化 ----------------
    def build(self):
        self.settings = self._load_settings()
        self.ti = {}   # key -> 数字输入框
        self.sw = {}   # 配件名 -> 开关

        root = BoxLayout(orientation="vertical", padding=6, spacing=4)

        # 标题
        root.add_widget(Label(text="金属链板成本计算器", bold=True,
                              font_name=_FONT_NAME, font_size=_FS_TITLE,
                              size_hint_y=None, height=_TITLE_HEIGHT))

        # 可滚动表单 + 明细
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        self.content = BoxLayout(orientation="vertical", spacing=6, padding=6,
                                 size_hint_y=None)
        self.content.bind(minimum_height=self.content.setter("height"))

        self._build_form()
        scroll.add_widget(self.content)
        root.add_widget(scroll)

        # 醒目总价(固定显示, 无需滚动)
        root.add_widget(self._build_total_bar())

        # 底部按钮行: 计算 + 设置公式
        btn_row = BoxLayout(size_hint_y=None, height=_BTN_HEIGHT, spacing=8)
        btn_calc = _btn("计 算", font_size=_FS_BTN_MAIN,
                        background_color=(0.20, 0.52, 0.90, 1))
        btn_calc.bind(on_press=lambda *a: self.compute_and_show(silent=False))
        btn_settings = _btn("设置公式",
                            background_color=(0.45, 0.45, 0.48, 1))
        btn_settings.bind(on_press=lambda *a: self.open_formula_settings())
        btn_row.add_widget(btn_calc)
        btn_row.add_widget(btn_settings)
        root.add_widget(btn_row)

        self._bind_live()
        return root

    def _settings_paths(self):
        paths = []
        try:
            paths.append(os.path.join(self.user_data_dir, "settings.json"))
        except Exception:
            pass
        try:
            paths.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "settings.json"))
        except Exception:
            pass
        paths.append("settings.json")
        return paths

    def _load_settings(self):
        s = default_settings()
        for p in self._settings_paths():
            if os.path.exists(p):
                try:
                    s = load_settings(p)
                    break
                except Exception:
                    pass
        return s

    def _save_settings(self):
        ud = self.user_data_dir
        os.makedirs(ud, exist_ok=True)
        save_settings(self.settings, os.path.join(ud, "settings.json"))

    # ---------------- 界面构建 ----------------
    def _build_form(self):
        c = self.content

        def row(label_text, widget):
            """一行: 左侧标签 + 右侧控件"""
            box = BoxLayout(orientation="horizontal", spacing=6, size_hint_y=None,
                            height=max(_ROW_HEIGHT, widget.height if hasattr(widget, "height") else _ROW_HEIGHT))
            lbl = _label(label_text, size_hint_x=None, width=_LABEL_WIDTH,
                         halign="left", valign="middle")
            lbl.bind(size=self._on_label_size)
            box.add_widget(lbl)
            box.add_widget(widget)
            c.add_widget(box)

        # ---- 材质 ----
        self.sp_plate = _spinner(MAT_OPTIONS[0], MAT_OPTIONS)
        row("板材质", self.sp_plate)

        self.sp_chain = _spinner(SAME_OPTION, [SAME_OPTION] + MAT_OPTIONS)
        row("链条材质", self.sp_chain)

        self.sp_pin = _spinner(SAME_OPTION, [SAME_OPTION] + MAT_OPTIONS)
        row("穿杆材质", self.sp_pin)

        # ---- 节距 ----
        self.sp_pitch = _spinner("50.8", PITCHES)
        row("节距(mm)", self.sp_pitch)

        # ---- 基础尺寸 ----
        self.ti["width"] = _num_input("500", "float", "有效宽度mm")
        row("有效宽度", self.ti["width"])
        self.ti["thickness"] = _num_input("2.0", "float", "板厚mm")
        row("板厚(mm)", self.ti["thickness"])
        self.ti["pin_d"] = _num_input("8", "float", "穿杆直径mm")
        row("穿杆直径", self.ti["pin_d"])

        # ---- 选配件 ----
        self._acc("cross", "横挡板", [
            ("长度(mm)", "cross_len", "100", "float"),
            ("高度(mm)", "cross_h", "50", "float"),
            ("厚度(mm)", "cross_t", "2.0", "float"),
            ("间隔(mm)", "cross_iv", "500", "float"),
        ])
        self._acc("side", "侧挡板", [
            ("高度(mm)", "side_h", "30", "float"),
            ("厚度(mm)", "side_t", "2.0", "float"),
        ])
        self._acc("ball", "载重滚珠", [("排数", "ball_rows", "1", "int")])
        self._acc("wheel", "载重支轮", [("排数", "wheel_rows", "1", "int")])
        self._acc("punch", "冲孔", [("元/片", "punch_price", "1.0", "float")])

        # ---- 明细(跨整行, 可自动增高) ----
        self.lbl_detail = Label(text="点【计 算】查看明细",
                                font_name=_FONT_NAME, font_size=_FS_DETAIL,
                                halign="left", valign="top",
                                size_hint_y=None, color=COLOR_NORMAL,
                                padding=(4, 4))
        self.lbl_detail.bind(width=lambda w, val: setattr(w, "text_size", (val, None)))
        self.lbl_detail.bind(texture_size=lambda w, val: setattr(w, "height", val[1] + 8))
        c.add_widget(self.lbl_detail)

    @staticmethod
    def _on_label_size(instance, value):
        """标签尺寸变化时更新 text_size，使文本正确对齐"""
        instance.text_size = (value[0] - 8, None)  # 留一点内边距

    def _acc(self, key, name, params):
        c = self.content

        def row_acc(label_text, widget):
            box = BoxLayout(orientation="horizontal", spacing=6,
                             size_hint_y=None, height=_ROW_HEIGHT)
            lbl = _label(label_text, size_hint_x=None, width=_LABEL_WIDTH,
                         halign="left", valign="middle")
            lbl.bind(size=self._on_label_size)
            box.add_widget(lbl)
            box.add_widget(widget)
            c.add_widget(box)
            return lbl

        sw = Switch(active=False, size_hint_x=None, width=58)
        sw_label = row_acc(name, sw)
        self.sw[key] = sw

        entries = []  # (label, input)
        for (plabel, tikey, default, filt) in params:
            ti = _num_input(default, filt, plabel)
            lbl = row_acc(plabel, ti)
            self.ti[tikey] = ti
            entries.append((lbl, ti))

        def toggle(instance, value):
            sw_label.color = COLOR_NORMAL if value else (0.5, 0.5, 0.5, 1)
            for (lbl, ti) in entries:
                ti.disabled = not value
                lbl.opacity = 1.0 if value else 0.35
                ti.opacity = 1.0 if value else 0.35
        sw.bind(active=toggle)
        toggle(sw, sw.active)

    def _build_total_bar(self):
        bar = BoxLayout(size_hint_y=None, height=_TOTAL_BAR_HEIGHT, padding=(12, 6))
        with bar.canvas.before:
            Color(*COLOR_TOTAL_BG)
            self._total_rect = Rectangle(pos=bar.pos, size=bar.size)
        bar.bind(pos=lambda *a: setattr(self._total_rect, "pos", bar.pos),
                 size=lambda *a: setattr(self._total_rect, "size", bar.size))
        self.lbl_total = Label(text="每米总价：—— 元/米", bold=True,
                               font_name=_FONT_NAME, font_size=_FS_TOTAL,
                               color=COLOR_TOTAL_FG)
        bar.add_widget(self.lbl_total)
        return bar

    # ---------------- 交互 ----------------
    def _bind_live(self):
        for sp in (self.sp_plate, self.sp_chain, self.sp_pin, self.sp_pitch):
            sp.bind(text=lambda *a: self._schedule_compute())
        for ti in self.ti.values():
            ti.bind(text=lambda *a: self._schedule_compute())
        for sw in self.sw.values():
            sw.bind(active=lambda *a: self._schedule_compute())

    def _schedule_compute(self):
        Clock.unschedule(self._debounced_compute)
        Clock.schedule_once(self._debounced_compute, 0.5)

    def _debounced_compute(self, dt):
        self.compute_and_show(silent=True)

    # ---------------- 计算 ----------------
    def _mat_key(self, text):
        if text == SAME_OPTION:
            return None
        return MATERIAL_KEYS[MAT_OPTIONS.index(text)]

    def _parse_float(self, ti, name):
        raw = ti.text.strip()
        try:
            v = float(raw)
        except ValueError:
            raise ValueError(f"{name} 输入无效：{raw!r}")
        if not math.isfinite(v) or v <= 0:
            raise ValueError(f"{name} 必须为大于 0 的有限数字")
        return v

    def _parse_int(self, ti, name):
        v = self._parse_float(ti, name)
        if v != int(v):
            raise ValueError(f"{name} 必须是整数")
        return int(v)

    def _build_params(self):
        plate_mat = MATERIAL_KEYS[MAT_OPTIONS.index(self.sp_plate.text)]
        chain_mat = self._mat_key(self.sp_chain.text) or plate_mat
        pin_mat = self._mat_key(self.sp_pin.text) or plate_mat
        p = {
            "pitch": self.sp_pitch.text,
            "plate_mat": plate_mat,
            "chain_mat": chain_mat,
            "pin_mat": pin_mat,
            "width": self._parse_float(self.ti["width"], "有效宽度"),
            "thickness": self._parse_float(self.ti["thickness"], "板厚"),
            "pin_d": self._parse_float(self.ti["pin_d"], "穿杆直径"),
        }
        if self.sw["cross"].active:
            p["cross"] = {
                "length": self._parse_float(self.ti["cross_len"], "横挡板长度"),
                "height": self._parse_float(self.ti["cross_h"], "横挡板高度"),
                "thickness": self._parse_float(self.ti["cross_t"], "横挡板厚度"),
                "interval": self._parse_float(self.ti["cross_iv"], "横挡板间隔"),
            }
        if self.sw["side"].active:
            p["side"] = {
                "height": self._parse_float(self.ti["side_h"], "侧挡板高度"),
                "thickness": self._parse_float(self.ti["side_t"], "侧挡板厚度"),
            }
        if self.sw["ball"].active:
            p["ball_rows"] = self._parse_int(self.ti["ball_rows"], "滚珠排数")
        if self.sw["wheel"].active:
            p["wheel_rows"] = self._parse_int(self.ti["wheel_rows"], "支轮排数")
        if self.sw["punch"].active:
            p["punch"] = True
            p["punch_manual"] = self._parse_float(self.ti["punch_price"], "冲孔价格")
        return p

    def compute_and_show(self, silent=False):
        try:
            params = self._build_params()
            r = compute(params, self.settings)
        except ValueError as e:
            self.lbl_total.text = "每米总价：—— 元/米"
            if not silent:
                self.lbl_detail.text = f"错误：{e}"
                self.lbl_detail.color = COLOR_ERR
            return
        self.lbl_detail.text = format_result(r)
        self.lbl_detail.color = COLOR_NORMAL
        self.lbl_total.text = f"每米总价：{r['total_per_meter']:.2f} 元/米"

    # ---------------- 公式设置 ----------------
    def open_formula_settings(self):
        content = BoxLayout(orientation="vertical", spacing=6, padding=10)

        content.add_widget(Label(
            text="修改计算公式（每条下方灰色小字为可用变量）",
            font_name=_FONT_NAME, size_hint_y=None, height=40,
            font_size=14, color=(0.3, 0.3, 0.3, 1)))

        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        inner = BoxLayout(orientation="vertical", spacing=8, padding=4,
                          size_hint_y=None)
        inner.bind(minimum_height=inner.setter("height"))

        self.formula_inputs = {}
        for (name, slot, hint) in FORMULA_FIELDS:
            lbl = Label(text=name, size_hint_y=None, height=28,
                        font_name=_FONT_NAME, font_size=15,
                        bold=True, halign="left", valign="middle")
            lbl.bind(size=self._on_label_size)
            inner.add_widget(lbl)

            expr = (self.settings.get("formulas") or {}).get(slot) or DEFAULT_FORMULAS[slot]
            ti = TextInput(text=expr, multiline=True,
                           font_name=_FONT_NAME, font_size=14,
                           size_hint_y=None, height=60, padding=(8, 6))
            ti.bind(minimum_height=lambda w, val: setattr(w, "height", max(52, val + 8)))
            self.formula_inputs[slot] = ti
            inner.add_widget(ti)

            h = Label(text=hint, size_hint_y=None, height=32,
                      font_name=_FONT_NAME, font_size=11,
                      color=(0.55, 0.55, 0.55, 1), halign="left", valign="top")
            h.bind(size=lambda w, s: setattr(w, "text_size", (s[0] - 8, None)))
            inner.add_widget(h)

        scroll.add_widget(inner)
        content.add_widget(scroll)

        self.lbl_formula_status = Label(text="", size_hint_y=None, height=70,
                                        font_name=_FONT_NAME, font_size=13,
                                        color=COLOR_ERR,
                                        halign="left", valign="top")
        self.lbl_formula_status.bind(size=lambda w, s: setattr(w, "text_size", s))
        content.add_widget(self.lbl_formula_status)

        bar = BoxLayout(size_hint_y=None, height=52, spacing=8)
        btn_default = _btn("恢复默认公式", font_size=14)
        btn_default.bind(on_press=lambda *a: self._restore_default_formulas())
        btn_save = _btn("保存", font_size=17,
                        background_color=(0.20, 0.60, 0.30, 1))
        btn_save.bind(on_press=lambda *a: self._save_formulas())
        btn_close = _btn("关闭", font_size=14)
        btn_close.bind(on_press=lambda *a: self._settings_popup.dismiss())
        bar.add_widget(btn_default)
        bar.add_widget(btn_save)
        bar.add_widget(btn_close)
        content.add_widget(bar)

        self._settings_popup = Popup(title="设置公式", content=content,
                                     size_hint=(0.96, 0.94))
        self._settings_popup.open()

    def _restore_default_formulas(self):
        for (name, slot, hint) in FORMULA_FIELDS:
            if slot in self.formula_inputs:
                self.formula_inputs[slot].text = DEFAULT_FORMULAS[slot]
        self.lbl_formula_status.text = "已恢复默认公式，点【保存】后生效"
        self.lbl_formula_status.color = (0.2, 0.6, 0.3, 1)

    def _save_formulas(self):
        new_formulas = {}
        errs = []
        for (name, slot, hint) in FORMULA_FIELDS:
            expr = self.formula_inputs[slot].text.strip()
            new_formulas[slot] = expr
            try:
                eval_expr(expr, SAMPLE_ENV)
            except ValueError as e:
                errs.append(f"「{name}」: {e}")
        if errs:
            self.lbl_formula_status.text = "保存失败：\n" + "\n".join(errs[:4])
            self.lbl_formula_status.color = COLOR_ERR
            return
        self.settings["formulas"] = new_formulas
        try:
            self._save_settings()
        except OSError as e:
            self.lbl_formula_status.text = f"保存失败：{e}"
            self.lbl_formula_status.color = COLOR_ERR
            return
        self._settings_popup.dismiss()
        self.compute_and_show(silent=False)


if __name__ == "__main__":
    ChainPlateApp().run()

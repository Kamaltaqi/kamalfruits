from kivy.lang import Builder
from kivy.core.window import Window
from kivy.graphics.texture import Texture
from kivy.clock import Clock
from kivy.config import Config
from kivy.core.text import LabelBase
from kivymd.app import MDApp
from kivymd.uix.button import MDFloatingActionButton, MDFlatButton
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.dialog import MDDialog
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.navigationdrawer import MDNavigationDrawer, MDNavigationLayout
from kivymd.uix.list import OneLineListItem
from kivymd.uix.snackbar import Snackbar
from kivy.uix.camera import Camera
import cv2
import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing import image

# مكتبات النصوص العربية
import arabic_reshaper
from bidi.algorithm import get_display

# صلاحيات أندرويد
from android.permissions import request_permissions, Permission
from kivy.utils import platform

# إعدادات التطبيق
Config.set('kivy', 'keyboard_mode', 'system')
Config.set('kivy', 'log_level', 'debug')
Window.size = (400, 600) if platform != 'android' else (360, 640)

# تسجيل الخطوط العربية
LabelBase.register(
    name='ArbFont',
    fn_regular='fonts/Amiri-Regular.ttf',
    fn_bold='fonts/Amiri-Bold.ttf'
)

# تسجيل خطوط الروبوت
LabelBase.register(
    name='Roboto',
    fn_regular='fonts/Roboto-Regular.ttf',
    fn_bold='fonts/Roboto-Bold.ttf'
)

KV = '''
MDNavigationLayout:
    md_bg_color: 1, 1, 1, 1
    ScreenManager:
        id: screen_manager
        MDScreen:
            MDBoxLayout:
                orientation: 'vertical'
                spacing: '10dp'
                padding: '10dp'

                MDTopAppBar:
                    title: app.reshape_text("تعرّف على الفواكه")
                    elevation: 4
                    right_action_items: [["menu", lambda x: nav_drawer.set_state("open")]]
                    left_action_items: [["information", lambda x: app.show_developer_info()]]
                    md_bg_color: app.theme_cls.primary_color
                    font_name: 'ArbFont'
                    anchor_title: 'center'
                    size_hint_y: None
                    height: dp(56)
                    pos_hint: {'top': 1}

                ScrollView:
                    MDBoxLayout:
                        orientation: 'vertical'
                        spacing: '20dp'
                        padding: '10dp'
                        size_hint_y: None
                        height: self.minimum_height
                        md_bg_color: 1, 1, 1, 1

                        MDCard:
                            id: image_card
                            orientation: 'vertical'
                            size_hint: 1, None
                            height: "260dp"
                            elevation: 4
                            radius: [25,]
                            md_bg_color: 1, 1, 1, 1
                            FitImage:
                                id: img
                                source: ''
                                size_hint: 1, 1
                                radius: [20,]
                            MDFloatingActionButton:
                                id: close_cam_btn
                                icon: 'close'
                                pos_hint: {'top': 1, 'left': 1}
                                elevation: 8
                                on_release: app.close_camera()
                                opacity: 0

                        MDCard:
                            id: result_card
                            orientation: 'vertical'
                            size_hint: 1, None
                            height: "120dp"
                            elevation: 4
                            radius: [25,]
                            md_bg_color: 1, 1, 1, 1
                            MDLabel:
                                id: result_label
                                text: app.reshape_text("اختر صورة للبدء")
                                halign: 'right'
                                valign: 'center'
                                font_name: 'ArbFont'
                                font_size: '20sp'
                                size_hint_y: None
                                height: self.texture_size[1]

                        MDGridLayout:
                            cols: 2
                            size_hint: None, None
                            width: "160dp"
                            height: "60dp"
                            pos_hint: {'center_x': 0.5}
                            spacing: "20dp"

                            MDFloatingActionButton:
                                icon: 'folder'
                                on_release: app.file_manager_open()
                                md_bg_color: app.theme_cls.primary_color
                                elevation: 6

                            MDFloatingActionButton:
                                icon: 'camera'
                                on_release: app.toggle_camera()
                                md_bg_color: app.theme_cls.primary_color
                                elevation: 6

    MDNavigationDrawer:
        id: nav_drawer
        radius: (25, 0, 0, 25)
        anchor: 'right'
        md_bg_color: 1, 1, 1, 1
        MDBoxLayout:
            orientation: 'vertical'
            spacing: '10dp'
            padding: '10dp'

            FitImage:
                source: 'assets/yemen_fruits.jpg'
                size_hint_y: None
                height: dp(150)
                radius: [15, 15, 0, 0]

            MDLabel:
                text: app.reshape_text("الفواكه اليمنية")
                halign: 'right'
                font_name: 'ArbFont'
                font_style: "H5"
                size_hint_y: None
                height: self.texture_size[1]
                padding: [0, 10, 0, 20]

            ScrollView:
                MDList:
                    OneLineListItem:
                        text: app.reshape_text("المانجو")
                        font_name: 'ArbFont'
                        font_size: '18sp'
                        halign: 'right'
                        on_release: app.show_fruit_info("المانجو")

                    OneLineListItem:
                        text: app.reshape_text("الموز")
                        font_name: 'ArbFont'
                        font_size: '18sp'
                        halign: 'right'
                        on_release: app.show_fruit_info("الموز")

                    OneLineListItem:
                        text: app.reshape_text("الجوافة")
                        font_name: 'ArbFont'
                        font_size: '18sp'
                        halign: 'right'
                        on_release: app.show_fruit_info("الجوافة")

                    OneLineListItem:
                        text: app.reshape_text("الرمان")
                        font_name: 'ArbFont'
                        font_size: '18sp'
                        halign: 'right'
                        on_release: app.show_fruit_info("الرمان")
'''

class MainApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.capture = None
        self.is_camera_open = False
        self.interpreter = None
        self.file_manager = None
        self.class_labels = {
            'Apple__Healthy': 'تفاح سليم',
            'Apple__Rotten': 'تفاح فاسد',
            'Banana__Healthy': 'موز سليم',
            'Banana__Rotten': 'موز فاسد',
            'Grape__Healthy': 'عنب سليم',
            'Grape__Rotten': 'عنب فاسد',
            'Guava__Healthy': 'جوافة سليمة',
            'Guava__Rotten': 'جوافة فاسدة',
            'Mango__Healthy': 'مانجو سليمة',
            'Mango__Rotten': 'مانجو فاسدة',
            'Orange__Healthy': 'برتقال سليم',
            'Orange__Rotten': 'برتقال فاسد',
            'Pomegranate__Healthy': 'رمان سليم',
            'Pomegranate__Rotten': 'رمان فاسد',
            'Tomato__Healthy': 'طماطم سليمة',
            'Tomato__Rotten': 'طماطم فاسدة'
        }
        
        self.fruit_info = {
            "المانجو": {
                "description": "المانجو اليمنية تتميز بحلاوة الطعم ورائحتها الزكية، وتعتبر من أجود أنواع المانجو في العالم.",
                "history": "تُزرع المانجو في اليمن منذ أكثر من 1000 عام، خاصة في مناطق تهامة والحديدة.",
                "benefits": "غنية بفيتامينات (أ، ج، ب6)، تعزز المناعة وتحسن صحة العيون.",
                "cultivation": "تزرع في المناطق الساحلية الدافئة مع توفر الري الكافي."
            },
            "الموز": {
                "description": "الموز اليمني معروف بكثافة لبه وحلاوة مذاقه، ويُعد مصدرًا غذائيًا مهمًا.",
                "history": "من أقدم الفواكه المزروعة في اليمن، ذكرت في النقوش السبئية القديمة.",
                "benefits": "مصدر غني بالبوتاسيوم والألياف، يحسن الهضم وصحة القلب.",
                "cultivation": "ينمو في المناطق الاستوائية وشبه الاستوائية خاصة محافظة الحديدة."
            },
            "الجوافة": {
                "description": "الجوافة اليمنية تتميز بلونها الوردي من الداخل وطعمها المميز الغني بالفيتامينات.",
                "history": "دخلت اليمن في القرن 18 عبر الموانئ التجارية في عدن.",
                "benefits": "تحتوي على فيتامين سي أكثر من البرتقال، تقوي المناعة وتحافظ على البشرة.",
                "cultivation": "تزرع في المناطق المعتدلة مع تربة جيدة الصرف."
            },
            "الرمان": {
                "description": "الرمان اليمني ذو حبات قرمزية لامعة وطعم حلو حامضي متوازن.",
                "history": "ذكر في الموروث اليمني القديم كرمز للخصوبة والحكمة.",
                "benefits": "غني بمضادات الأكسدة، يحارب السرطان ويعزز صحة القلب.",
                "cultivation": "ينمو في المرتفعات الجبلية مثل إب وذمار."
            }
        }

        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.accent_palette = "Orange"

    def build(self):
        try:
            if platform == 'android':
                request_permissions([
                    Permission.CAMERA,
                    Permission.WRITE_EXTERNAL_STORAGE,
                    Permission.READ_EXTERNAL_STORAGE
                ])
            
            self.load_model()
            return Builder.load_string(KV)
        except Exception as e:
            self.show_error_dialog(f"خطأ أثناء بناء التطبيق: {str(e)}")

    def load_model(self):
        try:
            self.interpreter = tf.lite.Interpreter(model_path='frutits_kamaltaqi1.tflite')
            self.interpreter.allocate_tensors()
            self.show_snackbar("تم تحميل النموذج بنجاح!")
        except Exception as e:
            self.show_error_dialog(f"خطأ في تحميل النموذج: {str(e)}")

    def toggle_camera(self):
        try:
            if not self.is_camera_open:
                self.capture = cv2.VideoCapture(0)
                if not self.capture.isOpened():
                    raise Exception("تعذر تشغيل الكاميرا")
                self.is_camera_open = True
                self.root.ids.close_cam_btn.opacity = 1
                Clock.schedule_interval(self.update_camera, 1.0/30.0)
                self.show_snackbar("تم تشغيل الكاميرا")
            else:
                self.capture_image()
        except Exception as e:
            self.show_error_dialog(f"خطأ أثناء تشغيل الكاميرا: {str(e)}")

    def update_camera(self, dt):
        try:
            ret, frame = self.capture.read()
            if ret:
                buf = cv2.flip(frame, 0).tobytes()
                texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
                texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
                self.root.ids.img.texture = texture
        except Exception as e:
            self.show_error_dialog(f"خطأ أثناء تحديث الكاميرا: {str(e)}")

    def capture_image(self):
        try:
            ret, frame = self.capture.read()
            if ret:
                cv2.imwrite("captured.jpg", frame)
                self.root.ids.img.source = "captured.jpg"
                result = self.predict_fruit("captured.jpg")
                self.root.ids.result_label.text = self.reshape_text(f"النتيجة: {result}")
                self.close_camera()
        except Exception as e:
            self.show_error_dialog(f"خطأ أثناء التقاط الصورة: {str(e)}")

    def close_camera(self):
        try:
            if self.capture:
                self.capture.release()
                self.is_camera_open = False
                Clock.unschedule(self.update_camera)
                self.root.ids.close_cam_btn.opacity = 0
                self.show_snackbar("تم إيقاف الكاميرا")
        except Exception as e:
            self.show_error_dialog(f"خطأ أثناء إغلاق الكاميرا: {str(e)}")

    def predict_fruit(self, img_path):
        try:
            img = cv2.imread(img_path)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = cv2.resize(img, (100, 100))
            img_array = img.astype(np.float32) / 255.0
            img_array = np.expand_dims(img_array, axis=0)

            input_details = self.interpreter.get_input_details()
            output_details = self.interpreter.get_output_details()

            self.interpreter.set_tensor(input_details[0]['index'], img_array)
            self.interpreter.invoke()

            predictions = self.interpreter.get_tensor(output_details[0]['index'])
            predicted_class = list(self.class_labels.keys())[np.argmax(predictions)]
            return self.class_labels[predicted_class]
        except Exception as e:
            return f"خطأ: {str(e)}"

    def show_fruit_info(self, fruit_name):
        try:
            info = self.fruit_info.get(fruit_name, {})
            content = f"""
            [font=ArbFont][color=#00695C][size=24][b]{self.reshape_text(fruit_name)}[/b][/size][/color]

            [color=#4CAF50][b]الوصف:[/b][/color]
            {self.reshape_text(info.get('description', ''))}

            [color=#4CAF50][b]التاريخ:[/b][/color]
            {self.reshape_text(info.get('history', ''))}

            [color=#4CAF50][b]الفوائد:[/b][/color]
            {self.reshape_text(info.get('benefits', ''))}

            [color=#4CAF50][b]الزراعة:[/b][/color]
            {self.reshape_text(info.get('cultivation', ''))}[/font]
            """
            
            self.dialog = MDDialog(
                title=f"[b]{self.reshape_text(fruit_name)} اليمنية[/b]",
                text=content,
                buttons=[
                    MDFlatButton(
                        text="إغلاق",
                        theme_text_color="Custom",
                        text_color=self.theme_cls.primary_color,
                        on_release=lambda x: self.dialog.dismiss()
                    ),
                ],
                radius=[20, 7, 20, 7],
                md_bg_color=(1, 1, 1, 1),
            )
            self.dialog.open()
        except Exception as e:
            self.show_error_dialog(f"خطأ أثناء عرض المعلومات: {str(e)}")

    def file_manager_open(self):
        try:
            if not self.file_manager:
                self.file_manager = MDFileManager(
                    exit_manager=self.exit_manager,
                    select_path=self.select_path,
                    preview=True,
                )
            self.file_manager.show(os.path.expanduser("~"))
        except Exception as e:
            self.show_error_dialog(f"خطأ في مدير الملفات: {str(e)}")

    def select_path(self, path):
        try:
            self.exit_manager()
            if os.path.isfile(path):
                self.root.ids.img.source = path
                result = self.predict_fruit(path)
                self.root.ids.result_label.text = self.reshape_text(f"النتيجة: {result}")
        except Exception as e:
            self.show_error_dialog(f"خطأ في اختيار الملف: {str(e)}")

    def exit_manager(self, *args):
        try:
            self.file_manager.close()
        except Exception as e:
            self.show_error_dialog(f"خطأ في الخروج: {str(e)}")

    def show_developer_info(self):
        try:
            dialog = MDDialog(
                title="معلومات المطور",
                text=self.reshape_text("تم التطوير بواسطة كمال تقي\nالإصدار 4.0"),
                buttons=[
                    MDFlatButton(
                        text="إغلاق",
                        theme_text_color="Custom",
                        text_color=self.theme_cls.primary_color,
                        on_release=lambda x: dialog.dismiss()
                    ),
                ],
                radius=[20, 7, 20, 7],
            )
            dialog.open()
        except Exception as e:
            self.show_error_dialog(f"خطأ في عرض المعلومات: {str(e)}")

    def show_error_dialog(self, message):
        try:
            dialog = MDDialog(
                title="خطأ",
                text=self.reshape_text(message
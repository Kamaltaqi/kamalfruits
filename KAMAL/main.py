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
from kivy.utils import platform
#from android.permissions import request_permissions, Permission
from kivymd.uix.list import OneLineListItem
from kivymd.uix.snackbar import Snackbar
from kivy.uix.camera import Camera
#
# from plyer import permissions
import cv2
import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing import image

# إضافة المكتبات الجديدة
import arabic_reshaper
from bidi.algorithm import get_display

# إعدادات اللغة والاتجاه
Config.set('kivy', 'keyboard_mode', 'system')
Config.set('kivy', 'log_level', 'debug')
Window.size = (400, 600)

# تسجيل الخط العربي
LabelBase.register(
    name='ArbFont',
    fn_regular='Amiri-Regular.ttf',  # تأكد من أن هذا المسار صحيح
    fn_bold='Amiri-Bold.ttf'
)

# تسجيل الخط الإنجليزي الافتراضي (Roboto)
LabelBase.register(
    name='Roboto',
    fn_regular='Roboto-Regular.ttf',  # هذا الخط يأتي مع KivyMD
    fn_bold='Roboto-Bold.ttf'         # تأكد من وجوده في نفس الدليل أو قم بتوفير المسار الصحيح
)

KV = '''
<FruitInfoScreen@MDScreen>:
    name: 'fruit_info'
    MDBoxLayout:
        orientation: 'vertical'
        padding: dp(10)
        spacing: dp(10)

        MDTopAppBar:
            title: app.reshape_text("معلومات الفاكهة")
            elevation: 4
            md_bg_color: app.theme_cls.primary_color
            font_name: 'ArbFont'
            left_action_items: [["arrow-left", lambda x: app.go_back()]]

        ScrollView:
            MDLabel:
                text: ''
                size_hint_y: None
                height: self.texture_size[1]
                halign: 'right'
                valign: 'top'
                font_name: 'ArbFont'
                font_size: '18sp'
                markup: True

MDNavigationLayout:
    md_bg_color: 1, 1, 1, 1  # خلفية بيضاء
    ScreenManager:
        id: screen_manager
        MDScreen:
            MDBoxLayout:
                orientation: 'vertical'
                spacing: '10dp'
                padding: '10dp'

                # Top App Bar (ثابت في الأعلى)
                MDTopAppBar:
                    title: app.reshape_text("تعرّف على الفواكه")
                    elevation: 4
                    right_action_items: [["menu", lambda x: nav_drawer.set_state("open")]]
                    left_action_items: [["information", lambda x: app.show_developer_info()]]
                    md_bg_color: app.theme_cls.primary_color
                    font_name: 'ArbFont'
                    anchor_title: 'center'  # جعل العنوان في المنتصف
                    size_hint_y: None
                    height: dp(56)

                    pos_hint: {'top': 1, 'left': 0, 'right': 1}  # ضبط الـ AppBar ليغطي عرض الشاشة بالكامل

                # Main Content (الصورة والنتائج)
                ScrollView:
                    MDBoxLayout:
                        orientation: 'vertical'
                        spacing: '20dp'
                        padding: '10dp'
                        size_hint_y: None
                        height: self.minimum_height
                        md_bg_color: 1, 1, 1, 1  # خلفية بيضاء

                        # Image Card (الصورة تتناسب مع الحاوية)
                        MDCard:
                            id: image_card
                            orientation: 'vertical'
                            size_hint: 1, None
                            height: "260dp"
                            elevation: 4
                            radius: [25,]
                            md_bg_color: 1, 1, 1, 1  # خلفية بيضاء
                            FitImage:
                                id: img
                                source: ''
                                size_hint: 1, 1  # جعل الصورة تملأ الحاوية
                                radius: [20,]
                            MDFloatingActionButton:
                                id: close_cam_btn
                                icon: 'close'
                                pos_hint: {'top': 1, 'left': 1}
                                elevation: 8
                                on_release: app.close_camera()
                                opacity: 0

                        # Result Card (عرض النتائج)
                        MDCard:
                            id: result_card
                            orientation: 'vertical'
                            size_hint: 1, None
                            height: "120dp"
                            elevation: 4
                            radius: [25,]
                            md_bg_color: 1, 1, 1, 1  # خلفية بيضاء
                            MDLabel:
                                id: result_label
                                text: app.reshape_text("اختر صورة للبدء")
                                halign: 'right'  # تصحيح اتجاه النص العربي
                                valign: 'center'
                                font_name: 'ArbFont'
                                font_size: '20sp'
                                size_hint_y: None
                                height: self.texture_size[1]

                        # Buttons Grid (الأزرار)
                        MDGridLayout:
                            cols: 2
                            size_hint: None, None
                            width: "160dp"
                            height: "60dp"
                            pos_hint: {'center_x': 0.5, 'center_y': 0.5}  # وضع الأزرار في منتصف الشاشة
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

    # Navigation Drawer
    MDNavigationDrawer:
        id: nav_drawer
        radius: (25, 0, 0, 25)
        anchor: 'right'
        md_bg_color: 1, 1, 1, 1  # خلفية بيضاء
        MDBoxLayout:
            orientation: 'vertical'
            spacing: '10dp'
            padding: '10dp'

            # صورة العنوان
            FitImage:
                source: 'assets/yemen_fruits.jpg'
                size_hint_y: None
                height: dp(150)
                radius: [15, 15, 0, 0]

            # عنوان الصفحة
            MDLabel:
                text: app.reshape_text("الفواكه اليمنية")
                halign: 'right'  # تصحيح اتجاه النص العربي
                font_name: 'ArbFont'
                font_style: "H5"
                size_hint_y: None
                height: self.texture_size[1]
                padding: [0, 10, 0, 20]

            # قائمة الفواكه مع التمرير
            ScrollView:
                MDList:
                    id: fruit_list

                    # المانجو
                    OneLineListItem:
                        text: app.reshape_text("المانجو")
                        title: app.reshape_text("المانجو")  # إضافة title بنفس الاسم
                        font_name: 'ArbFont'
                        font_size: '18sp'
                        halign: 'right'
                        on_release:
                            app.show_fruit_info("المانجو")

                    # الموز
                    OneLineListItem:
                        text: app.reshape_text("الموز")
                        title: app.reshape_text("الموز")  # إضافة title بنفس الاسم
                        font_name: 'ArbFont'
                        font_size: '18sp'
                        halign: 'right'
                        on_release:
                            app.show_fruit_info("الموز")

                    # الجوافة
                    OneLineListItem:
                        text: app.reshape_text("الجوافة")
                        title: app.reshape_text("الجوافة")  # إضافة title بنفس الاسم
                        font_name: 'ArbFont'
                        font_size: '18sp'
                        halign: 'right'
                        on_release:
                            app.show_fruit_info("الجوافة")

                    # الرمان
                    OneLineListItem:
                        text: app.reshape_text("الرمان")
                        title: app.reshape_text("الرمان")  # إضافة title بنفس الاسم
                        font_name: 'ArbFont'
                        font_size: '18sp'
                        halign: 'right'
                        on_release:
                            app.show_fruit_info("الرمان")
'''

class MainApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.capture = None
        self.is_camera_open = False
        self.model = None
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
                "description": self.reshape_text("المانجو اليمنية تُعتبر واحدة من أجود أنواع المانجو في العالم، حيث تتميز بحلاوة طعمها الفريدة ورائحتها الزكية التي تأسر الحواس. ثمار المانجو اليمنية غالبًا ما تكون كبيرة الحجم وممتلئة بالعصارة، مما يجعلها خيارًا مثاليًا للاستهلاك الطازج أو تحضير العصائر والحلويات."),
                "history": self.reshape_text("تُزرع المانجو في اليمن منذ أكثر من ألف عام، وهي جزء لا يتجزأ من التراث الزراعي للبلاد. تُعتبر مناطق تهامة والحديدة من أبرز المناطق التي تشتهر بإنتاج المانجو بسبب المناخ الدافئ والتربة الخصبة. تاريخيًا، كانت المانجو تُزرع في البساتين التقليدية باستخدام أساليب زراعية بسيطة تعتمد على الري التقليدي عبر القنوات المائية المعروفة باسم 'السبيل'."),
                "benefits": self.reshape_text("تعزيز المناعة: تحتوي المانجو على مستويات عالية من فيتامين C وفيتامين A، مما يساعد في تعزيز جهاز المناعة وحماية الجسم من الأمراض.\nتحسين صحة العيون: غنية بفيتامين A، وهي ضرورية لصحة العيون ومنع مشاكل الرؤية مثل العمى الليلي.\nدعم صحة الجلد: تحتوي المانجو على مضادات الأكسدة التي تحمي البشرة من الشيخوخة المبكرة وتمنحها مظهرًا صحيًا.\nتحسين الهضم: تحتوي على الألياف الغذائية التي تساعد في تنظيم حركة الأمعاء ومنع الإمساك.\nدعم صحة القلب: غنية بالبوتاسيوم الذي يساعد في تنظيم ضغط الدم وتحسين صحة القلب."),
                "cultivation": self.reshape_text("تُزرع المانجو في المناطق الساحلية ذات المناخ الدافئ، حيث تحتاج إلى درجات حرارة تتراوح بين 24-30 درجة مئوية. يتم الري بشكل منتظم باستخدام المياه النظيفة، مع توفير تربة جيدة الصرف. يتم قطف الثمار عندما تصل إلى مرحلة النضج الكامل، ويتم تخزينها بطريقة تضمن الحفاظ على جودتها.")
            },
            "الموز": {
                "description": self.reshape_text("الموز اليمني يتميز بكثافة لبه وحلاوة مذاقه، مما يجعله من الخيارات المفضلة لدى المستهلكين. يعتبر الموز مصدرًا غنيًا بالطاقة والمواد الغذائية الأساسية، وهو جزء لا يتجزأ من النظام الغذائي اليومي للكثير من اليمنيين."),
                "history": self.reshape_text("يُعد الموز من أقدم الفواكه المزروعة في اليمن، حيث تم ذكره في النقوش السبئية القديمة. تُزرع أشجار الموز في المناطق الاستوائية وشبه الاستوائية، خاصة في محافظة الحديدة. تعتمد زراعة الموز على نظام الري التقليدي، مما يجعله محصولًا رئيسيًا في المناطق الزراعية."),
                "benefits": self.reshape_text("مصدر طبيعي للطاقة: يحتوي الموز على نسبة عالية من الكربوهيدرات والسكريات الطبيعية، مما يجعله مصدرًا سريعًا للطاقة.\nغني بالبوتاسيوم: يساعد البوتاسيوم في تنظيم ضغط الدم وتحسين صحة القلب.\nتحسين الهضم: يحتوي على الألياف الغذائية التي تدعم صحة الجهاز الهضمي.\nتعزيز صحة الدماغ: يحتوي على فيتامين B6 الذي يعزز وظائف الدماغ ويحسن المزاج.\nدعم صحة العظام: يحتوي على المعادن مثل المغنيسيوم التي تدعم صحة العظام."),
                "cultivation": self.reshape_text("تُزرع أشجار الموز في المناطق ذات المناخ الدافئ والرطب، حيث تحتاج إلى توفر المياه بشكل مستمر. يتم استخدام تقنيات الري الحديثة لضمان نمو الأشجار بشكل صحي. يتم قطف الموز عندما يصل إلى مرحلة النضج المناسبة، ويتم تخزينه في أماكن باردة لتجنب التلف.")
            },
            "الجوافة": {
                "description": self.reshape_text("الجوافة اليمنية تتميز بلونها الوردي من الداخل وطعمها المميز الغني بالفيتامينات. تعتبر الجوافة من الفواكه الغنية بالقيمة الغذائية، مما يجعلها خيارًا صحيًا للجميع."),
                "history": self.reshape_text("دخلت الجوافة اليمن في القرن الثامن عشر عبر الموانئ التجارية في عدن. تُزرع الجوافة في المناطق المعتدلة ذات التربة الجيدة الصرف، حيث تحتاج إلى مناخ معتدل لتنمو بشكل صحي."),
                "benefits": self.reshape_text("غنية بفيتامين C: تحتوي الجوافة على كمية أكبر من فيتامين C مقارنة بالبرتقال، مما يعزز المناعة.\nتحسين صحة القلب: تحتوي على الألياف التي تخفض مستوى الكوليسترول الضار.\nدعم صحة البشرة: تحتوي على مضادات الأكسدة التي تحمي البشرة من الشيخوخة.\nتنظيم ضغط الدم: تحتوي على البوتاسيوم الذي يساعد في تنظيم ضغط الدم."),
                "cultivation": self.reshape_text("تُزرع الجوافة في المناطق ذات المناخ المعتدل، حيث تحتاج إلى تربة جيدة الصرف. يتم الري بشكل منتظم لضمان نمو الشجرة بشكل صحي. يتم قطف الثمار عندما تصل إلى مرحلة النضج الكامل.")
            },
            "الرمان": {
                "description": self.reshape_text("الرمان اليمني يتميز بحباته القرمزية اللامعة وطعمه الحلو الحامضي المتوازن. يعتبر الرمان من الفواكه الغنية بالقيمة الغذائية، مما يجعله خيارًا صحيًا للجميع."),
                "history": self.reshape_text("ذكر الرمان في الموروث اليمني القديم كرمز للخصوبة والحكمة. ينمو الرمان في المرتفعات الجبلية مثل إب وذمار، حيث يحتاج إلى مناخ بارد ومعتدل."),
                "benefits": self.reshape_text("غني بمضادات الأكسدة: يحارب الجذور الحرة ويمنع السرطان.\nتحسين صحة القلب: يخفض مستوى الكوليسترول الضار.\nدعم صحة الجهاز الهضمي: يحتوي على الألياف التي تحسن الهضم."),
                "cultivation": self.reshape_text("تُزرع شجرة الرمان في المناطق الجبلية ذات المناخ المعتدل. يتم الري بشكل منتظم، ويتم قطف الثمار عند النضج.")
            }
        }

        # إعدادات التنسيق
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.accent_palette = "Orange"
        self.theme_cls.font_styles.update({
            'H1': ['ArbFont', 96, False, 0.15],
            'H2': ['ArbFont', 60, False, 0.15],
            'H5': ['ArbFont', 24, False, 0.15],
            'H6': ['ArbFont', 20, False, 0.15],
            'Body1': ['ArbFont', 16, False, 0.15],
        })

    def build(self):
        try:
            if platform == "android":
                request_permissions()
                  #request_permissions([Permission.CAMERA, Permission.WRITE_EXTERNAL_STORAGE])
            self.load_model()
            return Builder.load_string(KV)
        except Exception as e:
            self.show_error_dialog(f"خطأ أثناء بناء التطبيق: {str(e)}")
    def request_permissions():
        permissions.request_permission('android.permission.CAMERA')
        permissions.request_permission('android.permission.READ_EXTERNAL_STORAGE')
        permissions.request_permission('android.permission.WRITE_EXTERNAL_STORAGE')
    def load_model(self):
        try:
            self.interpreter = tf.lite.Interpreter(model_path='frutits_kamaltaqi1.tflite')
            self.interpreter.allocate_tensors()
            self.show_snackbar("تم تحميل النموذج بنجاح!")
        except Exception as e:
            self.show_error_dialog(f"خطأ في تحميل النموذج: {str(e)}")

    def show_fruit_info(self, fruit_name):
        try:
            fruit_data = self.fruit_info.get(fruit_name, {})
            if fruit_data:
                description = fruit_data.get("description", "")
                history = fruit_data.get("history", "")
                benefits = fruit_data.get("benefits", "")
                cultivation = fruit_data.get("cultivation", "")

                # عرض المعلومات في صفحة جديدة
                info_text = f"""
                [b]الوصف:[/b]\n{description}\n\n
                [b]التاريخ:[/b]\n{history}\n\n
                [b]الفوائد الصحية:[/b]\n{benefits}\n\n
                [b]طرق الزراعة:[/b]\n{cultivation}
                """
                self.root.ids.screen_manager.current = 'fruit_info'
                fruit_info_screen = self.root.ids.screen_manager.get_screen('fruit_info')
                fruit_info_screen.ids.label.text = info_text
        except Exception as e:
            self.show_error_dialog(f"خطأ أثناء عرض معلومات الفاكهة: {str(e)}")

    def go_back(self):
        self.root.ids.screen_manager.current = 'main'

    def file_manager_open(self):
        try:
            if not self.file_manager:
                self.file_manager = MDFileManager(
                    exit_manager=self.exit_manager,
                    select_path=self.select_path,
                    preview=True,
                )
            self.file_manager.show(os.path.expanduser("~").encode('utf-8').decode('utf-8'))
        except Exception as e:
            self.show_error_dialog(f"خطأ أثناء فتح مدير الملفات: {str(e)}")

    def select_path(self, path):
        try:
            self.exit_manager()
            if os.path.isfile(path):
                self.root.ids.img.source = path
                result = self.predict_fruit(path)
                self.root.ids.result_label.text = self.reshape_text(f"النتيجة: {result}")
        except Exception as e:
            self.show_error_dialog(f"خطأ أثناء اختيار الملف: {str(e)}")

    def exit_manager(self, *args):
        try:
            self.file_manager.close()
        except Exception as e:
            self.show_error_dialog(f"خطأ أثناء إغلاق مدير الملفات: {str(e)}")

    def toggle_camera(self):
        try:
            if not self.is_camera_open:
                self.capture = cv2.VideoCapture(0)
                if not self.capture.isOpened():
                    raise Exception("تعذر تشغيل الكاميرا")
                self.is_camera_open = True
                self.root.ids.close_cam_btn.opacity = 1
                Clock.schedule_interval(self.update_camera, 1.0 / 30.0)
                self.show_snackbar("تم تشغيل الكاميرا")
            else:
                self.capture_image()
        except Exception as e:
            self.show_error_dialog(f"خطأ أثناء تشغيل الكاميرا: {str(e)}")

    def update_camera(self, dt):
        try:
            ret, frame = self.capture.read()
            if not ret:
                raise Exception("تعذر قراءة الإطار من الكاميرا")
            buf = cv2.flip(frame, 0).tobytes()
            texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
            texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            self.root.ids.img.texture = texture
        except Exception as e:
            self.show_error_dialog(f"خطأ أثناء تحديث الكاميرا: {str(e)}")

    def capture_image(self):
        try:
            ret, frame = self.capture.read()
            if not ret:
                raise Exception("تعذر التقاط الصورة")
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
            self.show_error_dialog(f"خطأ أثناء عرض معلومات المطور: {str(e)}")

    def show_error_dialog(self, message):
        try:
            dialog = MDDialog(
                title="خطأ",
                text=self.reshape_text(message),
                buttons=[
                    MDFlatButton(
                        text="موافق",
                        theme_text_color="Custom",
                        text_color=self.theme_cls.primary_color,
                        on_release=lambda x: dialog.dismiss()
                    ),
                ],
                radius=[20, 7, 20, 7],
            )
            dialog.open()
        except Exception as e:
            print(f"خطأ غير متوقع أثناء عرض رسالة الخطأ: {str(e)}")

    def predict_fruit(self, img_path):
        try:
            if self.interpreter is None:
                raise Exception("النموذج غير متوفر")
            img = image.load_img(img_path, target_size=(100, 100))
            img_array = image.img_to_array(img) / 255.0
            img_array = np.expand_dims(img_array, axis=0)

            input_details = self.interpreter.get_input_details()
            output_details = self.interpreter.get_output_details()

            self.interpreter.set_tensor(input_details[0]['index'], img_array.astype(np.float32))
            self.interpreter.invoke()

            predictions = self.interpreter.get_tensor(output_details[0]['index'])
            predicted_class = list(self.class_labels.keys())[np.argmax(predictions)]
            return self.class_labels[predicted_class]
        except Exception as e:
            return f"خطأ: {str(e)}"

    def show_snackbar(self, message):
        try:
            Snackbar(text=self.reshape_text(message), duration=2).open()
        except Exception as e:
            self.show_error_dialog(f"خطأ أثناء عرض الرسالة: {str(e)}")
   

    def on_stop(self):
        try:
            self.close_camera()
        except Exception as e:
            self.show_error_dialog(f"خطأ أثناء إغلاق الكاميرا عند إيقاف التطبيق: {str(e)}")

    # دالة لتشكيل النصوص وإظهارها من اليمين إلى اليسار
    def reshape_text(self, text):
        try:
            reshaped_text = arabic_reshaper.reshape(text)
            bidi_text = get_display(reshaped_text)
            return bidi_text
        except Exception as e:
            return f"خطأ: {str(e)}"

if __name__ == '__main__':
    try:
        MainApp().run()
    except Exception as e:
        print(f"خطأ غير متوقع أثناء تشغيل التطبيق: {str(e)}")

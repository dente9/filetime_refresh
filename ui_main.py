from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QDateTimeEdit, QHBoxLayout,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget, QLayout)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(409, 484)
        
        # 添加主垂直布局
        self.verticalLayout_2 = QVBoxLayout(Form)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(10, 10, 10, 10)
        
        # 拖放按钮区域
        self.pushButton_path = QPushButton(Form)
        self.pushButton_path.setObjectName(u"pushButton_path")
        self.pushButton_path.setMinimumSize(QSize(0, 250))  # 设置最小高度
        self.pushButton_path.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.verticalLayout_2.addWidget(self.pushButton_path)
        
        # 复选框区域
        self.horizontalLayoutWidget = QWidget(Form)
        self.horizontalLayoutWidget.setObjectName(u"horizontalLayoutWidget")
        self.horizontalLayout = QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        
        self.checkBox_modelchange = QCheckBox(self.horizontalLayoutWidget)
        self.checkBox_modelchange.setObjectName(u"checkBox_modelchange")
        self.horizontalLayout.addWidget(self.checkBox_modelchange)
        
        self.checkBox_file_select_change = QCheckBox(self.horizontalLayoutWidget)
        self.checkBox_file_select_change.setObjectName(u"checkBox_file_select_change")
        self.horizontalLayout.addWidget(self.checkBox_file_select_change)
        
        self.verticalLayout_2.addWidget(self.horizontalLayoutWidget)
        
        # 时间和执行按钮区域
        self.verticalLayoutWidget = QWidget(Form)
        self.verticalLayoutWidget.setObjectName(u"verticalLayoutWidget")
        self.verticalLayout = QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        
        self.dateTimeEdit_timeinput = QDateTimeEdit(self.verticalLayoutWidget)
        self.dateTimeEdit_timeinput.setObjectName(u"dateTimeEdit_timeinput")
        self.dateTimeEdit_timeinput.setMaximumSize(QSize(16777215, 50))
        self.verticalLayout.addWidget(self.dateTimeEdit_timeinput)
        
        self.pushButton_enter = QPushButton(self.verticalLayoutWidget)
        self.pushButton_enter.setObjectName(u"pushButton_enter")
        self.pushButton_enter.setMaximumSize(QSize(16777215, 50))
        self.verticalLayout.addWidget(self.pushButton_enter)
        
        self.verticalLayout_2.addWidget(self.verticalLayoutWidget)
        
        # 添加伸缩因子，使内容均匀分布
        self.verticalLayout_2.setStretch(0, 3)  # 拖放按钮区域占3份
        self.verticalLayout_2.setStretch(1, 1)  # 复选框区域占1份
        self.verticalLayout_2.setStretch(2, 1)  # 底部区域占1份

        self.retranslateUi(Form)
        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.pushButton_path.setText(QCoreApplication.translate("Form", u"\u70b9\u51fb\u6765\u9009\u62e9\u8def\u5f84\u6216\u5c06\u6587\u4ef6\u62d6\u5165\u6b64\u5904", None))
        self.checkBox_modelchange.setText(QCoreApplication.translate("Form", u"\u65f6\u95f4\u5dee-\u6574\u4f53", None))
        self.checkBox_file_select_change.setText(QCoreApplication.translate("Form", u"\u6587\u4ef6\u5939-\u6587\u4ef6\u6a21\u5f0f", None))
        self.pushButton_enter.setText(QCoreApplication.translate("Form", u"\u6267\u884c\u65f6\u95f4\u504f\u79fb", None))
    # retranslateUi
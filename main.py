import sys
import cv2
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QMessageBox
from PyQt5.QtGui import QImage, QPainter, QPainterPath
from PyQt5.QtCore import Qt, QRectF, QTimer

if getattr(sys, 'frozen', False):
    # 这是打包后的环境，导入 pyi_splash
    import pyi_splash

class CircularCameraWindow(QLabel):
    def __init__(self):
        super().__init__()
        
        # 检测摄像头
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            if getattr(sys, 'frozen', False):
                pyi_splash.close()
            self.show_camera_error()  # 显示错误提示
            return  # 退出初始化
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)  # 无边框
        self.setAttribute(Qt.WA_TranslucentBackground)  # 透明背景
        self.setFixedSize(250, 250)  # 固定窗口大小，确保圆形不会改变

        # 使用定时器不断刷新摄像头帧
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # 每30毫秒刷新一次

        # 添加关闭按钮，默认隐藏
        self.close_button = QPushButton('x', self)
        self.close_button.setFixedSize(30, 30)
        self.close_button.move(self.width() - 40, 10)  # 设置关闭按钮在右上角位置
        self.close_button.setStyleSheet(
            "background-color: red; color: white; border-radius: 15px; font-size: 16px;")
        self.close_button.clicked.connect(self.close)
        self.close_button.hide()  # 初始时隐藏

        # 定时器用于控制按钮隐藏
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide_close_button)

        self.m_drag = False  # 用于拖动窗口

    def show_camera_error(self):
        msg_box = QMessageBox()
        msg_box.setWindowTitle("摄像头错误")
        msg_box.setText("没有可用的摄像头设备。")
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()  # 显示消息框
        QApplication.quit()  # 退出程序

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            # 将 OpenCV 图像转换为 QImage，不做缩放处理
            height, width, channel = frame.shape
            bytesPerLine = 3 * width
            qImg = QImage(frame.data, width, height, bytesPerLine, QImage.Format_RGB888).rgbSwapped()

            # 保存图像供 paintEvent 使用
            self.current_frame = qImg
            self.update()  # 刷新界面

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if hasattr(self, 'current_frame'):
            # 创建圆形裁剪区域，确保居中
            path = QPainterPath()
            radius = self.width() // 2
            circle_rect = QRectF(0, 0, 2 * radius, 2 * radius)
            path.addEllipse(circle_rect)
            painter.setClipPath(path)

            # 将摄像头画面按比例缩放，居中显示
            scaled_img = self.current_frame.scaled(self.width(), self.height(), Qt.KeepAspectRatioByExpanding)
            img_x = (self.width() - scaled_img.width()) // 2
            img_y = (self.height() - scaled_img.height()) // 2
            painter.drawImage(img_x, img_y, scaled_img)

    def closeEvent(self, event):
        self.cap.release()

    # 实现窗口拖动
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.m_drag = True
            self.m_DragPosition = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if Qt.LeftButton and self.m_drag:
            self.move(event.globalPos() - self.m_DragPosition)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.m_drag = False

    # 鼠标进入窗口时显示关闭按钮
    def enterEvent(self, event):
        self.close_button.show()  # 显示关闭按钮
        if self.hide_timer.isActive():
            self.hide_timer.stop()  # 停止隐藏定时器

    # 鼠标离开窗口时启动定时器，延时隐藏按钮
    def leaveEvent(self, event):
        self.hide_timer.start(1000)  # 启动2秒的定时器

    # 隐藏关闭按钮
    def hide_close_button(self):
        self.close_button.hide()

# 主函数
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CircularCameraWindow()
    if not window.cap.isOpened():
        sys.exit()  # 如果未打开摄像头，则退出程序
    # 在打包环境中关闭 splash screen
    if getattr(sys, 'frozen', False):
        pyi_splash.close()
    window.show()
    sys.exit(app.exec_())

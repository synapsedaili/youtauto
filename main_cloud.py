# main.py
import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton,
    QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsTextItem, QMessageBox
)
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QFont, QPen, QBrush, QColor, QPainter

# Modüller
import idea
import script
import video
import upload

class InfoNode(QGraphicsItem):
    def __init__(self, title="", width=240, height=130):
        super().__init__()
        self.width, self.height = width, height
        self.title_item = QGraphicsTextItem(f"<b>{title}</b>", self)
        self.title_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.title_item.setDefaultTextColor(QColor("#cbd5e0"))
        self.title_item.setPos(10, 5)

        self.text_item = QGraphicsTextItem("", self)
        self.text_item.setFont(QFont("Segoe UI", 8))
        self.text_item.setDefaultTextColor(QColor("#f1f5f9"))
        self.text_item.setTextWidth(width - 20)
        self.text_item.setPos(10, 22)

    def set_text(self, text):
        self.text_item.setPlainText(text[:400])
        self.update()

    def boundingRect(self):
        return QRectF(0, 0, self.width, self.height)

    def paint(self, painter, option, widget):
        painter.setBrush(QBrush(QColor("#2d3748")))
        painter.setPen(QPen(QColor("#4a5568"), 1))
        painter.drawRoundedRect(0, 0, self.width, self.height, 8, 8)

class WorkflowWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎥 YouTube Otomasyonu — Modüler Workflow")
        self.resize(900, 320)

        self.setStyleSheet("""
            QMainWindow { background-color: #0f172a; }
            QPushButton {
                background-color: #63b3ed; color: #0f172a; border: none;
                border-radius: 8px; padding: 12px 24px; font-weight: bold;
            }
            QPushButton:hover { background-color: #4299e1; }
        """)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setAlignment(Qt.AlignTop)

        title = QLabel("YouTube Otomasyonu — Adım 1 → 2 → 3 → 4")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #bee3f8; margin-bottom: 15px;")
        layout.addWidget(title)

        self.scene = QGraphicsScene()
        self.scene.setSceneRect(-450, -80, 900, 160)
        self.view = QGraphicsView(self.scene)
        self.view.setBackgroundBrush(QBrush(QColor("#1e293b")))
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setDragMode(QGraphicsView.NoDrag)
        self.view.setInteractive(False)
        layout.addWidget(self.view)

        self.nodes = {}
        for i, (name, title) in enumerate([
            ("idea", "💡 Fikir"),
            ("script", "🎙️ Senaryo"),
            ("video", "🎥 Video"),
            ("upload", "📤 YouTube")
        ]):
            node = InfoNode(title)
            node.setPos(-390 + i * 260, -70)
            self.scene.addItem(node)
            self.nodes[name] = node

        self.run_btn = QPushButton("▶️ Tam Workflow’u Çalıştır")
        self.run_btn.clicked.connect(self.run_full_pipeline)
        layout.addWidget(self.run_btn, alignment=Qt.AlignCenter)

        self.setCentralWidget(central)

    def run_full_pipeline(self):
        try:
            # === Adım 1: Fikir ===
            idea_text, next_idx = idea.get_next_idea()
            self.nodes["idea"].set_text(f"{idea_text}\n\n(Sıra: {next_idx})")

            # === Adım 2: Senaryo ===
            script_text = script.generate_script(idea_text)
            self.nodes["script"].set_text(script_text)

            # === Adım 3: Video ===
            video_path = video.create_video_from_script(script_text, idea_text)
            self.nodes["video"].set_text(f"Video yolu:\n{os.path.basename(video_path)}")

            # === Adım 4: Upload ===
            upload_result = upload.upload_to_youtube(video_path, idea_text)
            self.nodes["upload"].set_text(upload_result)

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Workflow hatası:\n{str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 9))
    window = WorkflowWindow()
    window.show()
    sys.exit(app.exec())
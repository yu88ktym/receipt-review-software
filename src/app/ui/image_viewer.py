from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGraphicsView, QGraphicsScene
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QPainter


class _ZoomPanView(QGraphicsView):
    """拡大縮小・ドラッグ移動に対応した QGraphicsView。"""

    def __init__(self, scene: QGraphicsScene, parent=None) -> None:
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self._last_mouse_pos = None

    def wheelEvent(self, event) -> None:
        """マウスホイールで拡大/縮小する。"""
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)

    def mousePressEvent(self, event) -> None:
        """左ボタン押下でドラッグ開始。"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._last_mouse_pos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        """ドラッグ中は画像を移動させる（パン）。"""
        if self._last_mouse_pos is not None:
            delta = event.pos() - self._last_mouse_pos
            self._last_mouse_pos = event.pos()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        """左ボタン離してドラッグ終了。"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._last_mouse_pos = None
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseReleaseEvent(event)


class ImageViewer(QWidget):
    """原本画像を表示するためのビューアウィンドウ（非モーダル）。

    - ウィンドウタイトルは画像ID
    - 上部に画像ID（コピー可能）を表示
    - マウスホイールで拡大/縮小
    - マウスドラッグで画像の移動（パン）
    """

    viewer_closed = Signal(object)  # self

    def __init__(self, image_id: str, parent=None) -> None:
        super().__init__(parent, Qt.WindowType.Window)
        self.setWindowTitle(image_id)
        self.setMinimumSize(800, 600)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 0)
        layout.setSpacing(4)

        # 画像IDを上部にコピー可能なテキストとして表示
        id_row = QHBoxLayout()
        id_label = QLabel("画像ID：")
        id_label.setFixedWidth(60)
        id_value = QLabel(image_id)
        id_value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        id_value.setWordWrap(True)
        id_row.addWidget(id_label)
        id_row.addWidget(id_value, stretch=1)
        layout.addLayout(id_row)

        self._scene = QGraphicsScene(self)
        self._view = _ZoomPanView(self._scene, self)
        layout.addWidget(self._view)
        self._fit_pending = False

    def closeEvent(self, event) -> None:
        self.viewer_closed.emit(self)
        super().closeEvent(event)

    def showEvent(self, event) -> None:
        """ウィンドウが表示されたタイミングで fitInView を実行する。"""
        super().showEvent(event)
        if self._fit_pending and self._scene.items():
            self._view.resetTransform()
            self._view.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
            self._fit_pending = False

    def load_image(self, image_bytes: bytes) -> None:
        """画像バイナリを読み込んで表示する。"""
        pixmap = QPixmap()
        pixmap.loadFromData(image_bytes)
        if pixmap.isNull():
            return

        self._scene.clear()
        self._scene.addPixmap(pixmap)
        self._scene.setSceneRect(pixmap.rect().toRectF())
        self._fit_pending = True
        # ウィンドウがすでに表示済みなら即座にフィット、未表示なら showEvent で実行される
        if self.isVisible():
            self._view.resetTransform()
            self._view.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
            self._fit_pending = False

        # ゴミ箱操作
        trash_heading = QLabel("ゴミ箱操作")
        layout.addWidget(trash_heading)

        trash_row = QHBoxLayout()

        # ステータスに応じて一方のみ表示する（load() で切り替え）
        self.trash_btn = QPushButton("🗑️ ゴミ箱へ移動")
        self.trash_btn.setProperty("danger", "true")
        self.trash_btn.clicked.connect(
            lambda: self.trash_requested.emit(self._current_image_id)
        )
        self.restore_btn = QPushButton("復元")
        self.restore_btn.setProperty("flat", "true")
        self.restore_btn.clicked.connect(
            lambda: self.restore_requested.emit(self._current_image_id)
        )
        trash_row.addWidget(self.trash_btn)
        trash_row.addWidget(self.restore_btn)
        layout.addLayout(trash_row)
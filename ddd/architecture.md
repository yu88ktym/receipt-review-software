# アーキテクチャ設計ドキュメント

## 1. パッケージ構成・クラス図（ハイブリッド）

### 1-1. 全体パッケージ図

```mermaid
graph TD
    classDef entry fill:#4CAF50,color:#fff,stroke:#388E3C
    classDef config fill:#2196F3,color:#fff,stroke:#1565C0
    classDef ui fill:#FF9800,color:#fff,stroke:#E65100
    classDef tab fill:#FF9800,color:#fff,stroke:#E65100,stroke-dasharray:5 5
    classDef service fill:#9C27B0,color:#fff,stroke:#6A1B9A
    classDef model fill:#F44336,color:#fff,stroke:#B71C1C
    classDef external fill:#607D8B,color:#fff,stroke:#37474F

    subgraph src/app
        MAIN["main.py\n(エントリーポイント)"]:::entry

        subgraph config["config/"]
            THEME["theme.py\n(デザイン定数)"]:::config
            STATUS_COLORS["status_colors.py\n(ステータス色定義)"]:::config
        end

        subgraph ui["ui/"]
            MW["main_window.py\n(MainWindow)"]:::ui
            SB["sidebar.py\n(Sidebar)"]:::ui
            DP["detail_panel.py\n(DetailPanel)"]:::ui

            subgraph tabs["ui/tabs/"]
                TL["tab_list.py\n(TabList)"]:::tab
                TFE["tab_final_edit.py\n(TabFinalEdit)"]:::tab
                TQ["tab_quality.py\n(TabQuality)"]:::tab
                TD["tab_dups.py\n(TabDups)"]:::tab
                TAC["tab_autocomplete.py\n(TabAutocomplete)"]:::tab
                TEC["tab_export_csv.py\n(TabExportCsv)"]:::tab
                TU["tab_upload.py\n(TabUpload)"]:::tab
                TS["tab_settings.py\n(TabSettings)"]:::tab
            end
        end

        subgraph services["services/"]
            SVC["各種サービス\n(将来実装)"]:::service
        end

        subgraph models["models/"]
            MDL["データモデル\n(将来実装)"]:::model
        end
    end

    PYSIDE6["PySide6\n(外部ライブラリ)"]:::external
    REQUESTS["requests\n(外部ライブラリ)"]:::external

    MAIN --> MW
    MAIN --> THEME
    MW --> SB
    MW --> DP
    MW --> TL
    MW --> TFE
    MW --> TQ
    MW --> TD
    MW --> TAC
    MW --> TEC
    MW --> TU
    MW --> TS

    TL --> STATUS_COLORS
    TFE --> STATUS_COLORS
    TQ --> STATUS_COLORS
    TS --> STATUS_COLORS

    TL --> THEME
    TFE --> THEME
    TQ --> THEME
    TD --> THEME
    TS --> THEME
    SB --> THEME
    MW --> THEME

    ui --> PYSIDE6
    services --> REQUESTS
```

### 1-2. UIクラス詳細図

```mermaid
classDiagram
    direction TB

    class MainWindow {
        +QTabWidget tabs
        +Sidebar sidebar
        +DetailPanel detail_panel
        -TabList _tab_list
        -TabFinalEdit _tab_final_edit
        -TabQuality _tab_quality
        -TabDups _tab_dups
        -TabAutocomplete _tab_autocomplete
        -TabExportCsv _tab_export_csv
        -TabUpload _tab_upload
        -TabSettings _tab_settings
        -_build_ui() None
        -_show_detail(data: dict) None
        -_on_detail_closed() None
    }

    class Sidebar {
        +QPushButton refresh_btn
        +QLineEdit keyword_edit
        +QComboBox status_combo
        +QComboBox quality_combo
        +QCheckBox exclude_dups_chk
        +QDateEdit since_date
        +QDateEdit until_date
        +QSpinBox page_size_spin
        -_build_ui() None
    }

    class DetailPanel {
        +Signal closed
        +dict~str,QLabel~ fields
        +QLabel image_label
        +QPushButton trash_btn
        +QPushButton restore_btn
        +load(data: dict) None
        -_build_ui() None
    }

    class TabList {
        +Signal detail_requested
        +QTableWidget table
        -int _page
        -int _total_pages
        -_build_ui() None
        -_populate() None
        -_apply_row_colors() None
        -_on_detail(row_data: tuple) None
        -_prev_page() None
        -_next_page() None
        -_update_pager() None
    }

    class TabFinalEdit {
        +QTableWidget table
        +QDateEdit edit_purchase_date
        +QLineEdit edit_total
        +QLineEdit edit_store
        +QLineEdit edit_payment
        -_build_ui() None
        -_populate() None
        -_apply_row_colors() None
        -_on_selection_changed() None
    }

    class TabQuality {
        +Signal detail_requested
        +QTableWidget table
        +QGroupBox qa_group
        -int|None _expanded_row
        -_build_ui() None
        -_populate() None
        -_apply_row_colors() None
        -_on_detail(row_data: tuple) None
        -_toggle_qa(row: int) None
    }

    class TabDups {
        +QTableWidget table
        -_build_ui() None
        -_populate() None
    }

    class TabSettings {
        +QSlider sidebar_width_slider
        +dict~str,QPushButton~ _status_color_btns
        -QColor _accent_color
        -dict~str,QColor~ _status_colors
        -_build_ui() None
        -_build_ui_settings() QGroupBox
        -_build_network_settings() QGroupBox
        -_build_border_settings() QGroupBox
        -_build_column_width_settings() QGroupBox
        -_build_status_color_settings() QGroupBox
        -_pick_accent_color() None
        -_pick_status_color(status: str) None
        -_update_status_color_btn(status: str) None
    }

    MainWindow --> Sidebar
    MainWindow --> DetailPanel
    MainWindow --> TabList
    MainWindow --> TabFinalEdit
    MainWindow --> TabQuality
    MainWindow --> TabDups
    MainWindow --> TabSettings
    TabList ..> DetailPanel : detail_requested signal
    TabQuality ..> DetailPanel : detail_requested signal
```

---

## 2. 各パッケージ・クラスの責務解説

### `main.py` — エントリーポイント

| 項目 | 内容 |
|------|------|
| 責務 | アプリケーションの起動。`QApplication` の初期化、グローバルスタイルシート・フォントの適用、`MainWindow` の生成と表示を行う。 |
| 外部依存 | `PySide6.QtWidgets.QApplication` |

---

### `config/theme.py` — デザイン定数

| 項目 | 内容 |
|------|------|
| 責務 | フォント名・サイズ、カラーコード、マージン・パディング、サイドバー幅などすべてのデザイントークンを一元管理する。各ウィジェットはこのモジュールの定数を参照することで、デザインの一貫性を保つ。 |
| 主な定数 | `FONT_FAMILY`, `COLOR_PRIMARY`, `MARGIN`, `PADDING`, `SIDEBAR_WIDTH`, `DETAIL_PANEL_WIDTH_PERCENT`, `STYLESHEET` |

---

### `config/status_colors.py` — 画像ステータス色定義

| 項目 | 内容 |
|------|------|
| 責務 | 画像ステータス（`INGESTED`, `OCR_DONE`, `FINAL_UPDATED`, `DROPPED`, `NOT_RECEIPT_SUSPECT` など）とテーブル行背景色の対応を定義する。テーブルウィジェット・設定タブが参照する唯一の色定義ソース。 |
| 主なAPI | `STATUS_COLORS: dict[str, str]`、`get_row_color(status: str) -> QColor` |

---

### `ui/main_window.py` — メインウィンドウ

| 項目 | 内容 |
|------|------|
| 責務 | アプリケーションのルートウィンドウ。左サイドバー・中央タブ・右詳細パネルを `QSplitter` で配置する。タブ間のシグナル転送（`detail_requested` → `DetailPanel.load`）を担う。 |
| 外部依存 | `PySide6.QtWidgets.QMainWindow`, `QSplitter`, `QTabWidget` |

---

### `ui/sidebar.py` — 左サイドバー

| 項目 | 内容 |
|------|------|
| 責務 | 検索・フィルタ条件（キーワード、ステータス、品質レベル、日付範囲、ページサイズ）の入力UIを提供する。「更新」ボタンを持ち、将来的にフィルタ変更シグナルを発する基点となる。 |
| 外部依存 | `PySide6.QtWidgets` 各種ウィジェット |

---

### `ui/detail_panel.py` — 右詳細パネル

| 項目 | 内容 |
|------|------|
| 責務 | 選択された画像の詳細情報（ID、日付、金額、店名、ステータス、整合性ステータスなど）を表示する。`load(data: dict)` メソッドで任意のタブからデータを受け取る。閉じるボタンで `closed` シグナルを発し、`MainWindow` がパネルを非表示にする。 |
| 外部依存 | `PySide6.QtWidgets.QScrollArea`, `QLabel`, `QPushButton`, `PySide6.QtGui.QPixmap` |

---

### `ui/tabs/tab_list.py` — 一覧タブ

| 項目 | 内容 |
|------|------|
| 責務 | 登録済み画像の一覧テーブルを表示する。ページネーション、ステータスによる行色付け、ヘッダークリックによるソート機能を持つ。行の「詳細」ボタンで `detail_requested` シグナルを発する。 |
| ステータス列 | インデックス 6（`ステータス/重要`） |

---

### `ui/tabs/tab_final_edit.py` — 確定値編集タブ

| 項目 | 内容 |
|------|------|
| 責務 | 画像の確定値（購入日、金額、店名、支払方法）を編集するUIを提供する。テーブル行選択でフォームに値を転記し、「確定」ボタンで保存する。ステータスによる行色付けとヘッダーソートを持つ。 |

---

### `ui/tabs/tab_quality.py` — 品質確認タブ

| 項目 | 内容 |
|------|------|
| 責務 | 画像の品質レベル（HIGH/MEDIUM/LOW）を確認・更新するUIを提供する。品質レベルフィルター、ステータス行色付け、ヘッダーソートを持つ。「品質確認」ボタンで展開式チェックパネルを表示する。 |

---

### `ui/tabs/tab_dups.py` — 重複管理タブ

| 項目 | 内容 |
|------|------|
| 責務 | 重複候補の一覧表示、重複設定（対象ID・親ID入力）、親子逆転操作のUIを提供する。テーブルヘッダーによるソート機能を持つ。列構成：レシートID、重複元レシートID、詳細ボタン、重複解除ボタン。 |

---

### `ui/tabs/tab_autocomplete.py` — 自動補完設定タブ

| 項目 | 内容 |
|------|------|
| 責務 | 店名・支払方法の表記ゆれ→正規化マッピングを管理するUIを提供する。行追加・削除機能を持つ。 |

---

### `ui/tabs/tab_export_csv.py` — CSVエクスポートタブ

| 項目 | 内容 |
|------|------|
| 責務 | CSV出力対象の列選択・日付範囲指定・エクスポートボタンのUIを提供する。 |

---

### `ui/tabs/tab_upload.py` — 画像アップロードタブ

| 項目 | 内容 |
|------|------|
| 責務 | 画像ファイルの選択（ファイルダイアログ）とアップロード操作のUIを提供する。 |

---

### `ui/tabs/tab_settings.py` — 設定タブ

| 項目 | 内容 |
|------|------|
| 責務 | アプリケーション設定（UI設定、通信設定、罫線設定、カラム幅、**画像ステータス色**）の編集UIを提供する。QColorDialogを使用してアクセントカラーおよび各ステータス色を対話的に変更できる。設定タブ全体はQScrollAreaで囲まれており、設定項目が増えてもスクロールで対応できる。 |

---

### 外部ライブラリ

| ライブラリ | バージョン | 用途 |
|------------|-----------|------|
| **PySide6** | ≥6.11 | Qt for Pythonの公式バインディング。全GUIウィジェット・シグナル・スロット・レイアウト管理を担う。LGPLライセンス。 |
| **requests** | ≥2.33 | HTTPクライアント。将来的にAPIサーバとの通信で使用する。 |
| **python-dotenv** | ≥1.2 | `.env` ファイルから環境変数（APIエンドポイントURL等）を読み込む。 |
| **PyInstaller** | ≥6.19 | Pythonアプリケーションを単一実行ファイル（.exe）にパッケージングする。開発依存。 |

---

## 3. GUIウィジェット間連携シーケンス図

### 3-1. 詳細パネル表示フロー（一覧タブから）

```mermaid
sequenceDiagram
    actor User as ユーザー
    participant TL as TabList
    participant MW as MainWindow
    participant DP as DetailPanel

    User->>TL: 「詳細」ボタンをクリック
    TL->>TL: _on_detail(row_data)
    TL-->>MW: detail_requested シグナル送出(data: dict)
    MW->>DP: load(data)
    DP->>DP: fields[key].setText(value) × n
    MW->>DP: setVisible(True)
    DP-->>User: 詳細パネルが表示される

    User->>DP: 「× 閉じる」をクリック
    DP-->>MW: closed シグナル送出
    MW->>DP: setVisible(False)
    DP-->>User: 詳細パネルが非表示になる
```

### 3-2. テーブルヘッダーソートフロー

```mermaid
sequenceDiagram
    actor User as ユーザー
    participant Header as QHeaderView
    participant Table as QTableWidget
    participant Items as QTableWidgetItem群

    User->>Header: 列ヘッダーをクリック
    Header->>Table: sectionClicked シグナル（Qt内部）
    Table->>Table: sortItems(column, order)
    Table->>Items: 列の QTableWidgetItem 値を比較・並べ替え
    Table-->>Header: ソートインジケータ（▲/▼）を更新
    Table-->>User: テーブル行が並び替えられて表示される

    note over Table,Items: setCellWidget() で配置したボタンは\nQTableWidgetItemを持たないため\nソート時に行移動しない（仕様）
```

### 3-3. ステータス色設定フロー（設定タブ）

```mermaid
sequenceDiagram
    actor User as ユーザー
    participant TS as TabSettings
    participant Dialog as QColorDialog
    participant SC as status_colors.py

    User->>TS: ステータス色ボタンをクリック
    TS->>TS: _pick_status_color(status)
    TS->>Dialog: QColorDialog.getColor(current_color)
    Dialog-->>User: カラーピッカーが表示される
    User->>Dialog: 色を選択してOKをクリック
    Dialog-->>TS: QColor（選択色）を返す
    TS->>TS: _status_colors[status] = new_color
    TS->>TS: _update_status_color_btn(status)
    TS-->>User: ボタン背景色が更新される

    note over TS,SC: 現在は設定保存はUI上のみ。\n将来的に settings.json 保存機能と\n各テーブルへの色反映シグナルを追加予定。
```

### 3-4. 確定値編集フロー（確定値編集タブ）

```mermaid
sequenceDiagram
    actor User as ユーザー
    participant TFE as TabFinalEdit
    participant Table as QTableWidget
    participant Form as 編集フォーム

    User->>Table: テーブル行をクリック / 「選択」ボタンをクリック
    Table-->>TFE: itemSelectionChanged シグナル
    TFE->>TFE: _on_selection_changed()
    TFE->>Form: edit_purchase_date.setDate(...)
    TFE->>Form: edit_total.setText(...)
    TFE->>Form: edit_store.setText(...)
    TFE->>Form: edit_payment.setText(...)
    Form-->>User: フォームに選択行の値が転記される

    User->>Form: 値を編集して「確定」ボタンをクリック
    note over TFE: 将来的にAPIクライアントを呼び出し\nサーバへ確定値を送信する
```

### 3-5. 品質確認展開フロー（品質確認タブ）

```mermaid
sequenceDiagram
    actor User as ユーザー
    participant TQ as TabQuality
    participant Table as QTableWidget
    participant QAGroup as qa_group (QGroupBox)

    User->>Table: 「品質確認」ボタンをクリック
    Table-->>TQ: clicked シグナル (row index)
    TQ->>TQ: _toggle_qa(row)

    alt 同じ行を再クリック
        TQ->>QAGroup: setVisible(False)
        TQ->>TQ: _expanded_row = None
        QAGroup-->>User: 品質確認パネルが折りたたまれる
    else 別の行または初回
        TQ->>QAGroup: setVisible(True)
        TQ->>TQ: _expanded_row = row
        QAGroup-->>User: 品質確認パネルが展開される
    end
```

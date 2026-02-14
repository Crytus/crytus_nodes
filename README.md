# Crytus Nodes — ComfyUI Custom Nodes

ComfyUI用のカスタムノードパッケージです。文字列操作やDICOM医用画像の読み込み機能を提供します。

---

## 📦 インストール

### 1. ファイルの配置

このフォルダ（`crytus_nodes`）を ComfyUI の `custom_nodes` ディレクトリに配置します。

```
ComfyUI/
└── custom_nodes/
    └── crytus_nodes/
        ├── __init__.py
        ├── concatenator.py
        ├── dicom_nodes.py
        ├── requirements.txt
        ├── js/
        │   └── crytus_dicom.js
        └── README.md
```

### 2. 依存ライブラリのインストール

ComfyUI の Python 環境で以下を実行してください：

```bash
pip install -r custom_nodes/crytus_nodes/requirements.txt
```

必要なライブラリ：
| ライブラリ | 用途 |
|---|---|
| `pydicom` | DICOM ファイルの読み込み |
| `numpy` | 画像データの数値処理 |
| `Pillow` | プレビュー画像の生成 |

> **Note:** `numpy`、`Pillow`、`torch` は ComfyUI に通常含まれています。追加で必要なのは `pydicom` のみの場合が多いです。

### 3. ComfyUI を再起動

インストール後、ComfyUI を再起動してください。

---

## 🧩 ノード一覧

### Simple String Concatenator

| 項目 | 内容 |
|---|---|
| **カテゴリ** | `Crytus/Text` |
| **内部名** | `MyStringConcatenator` |

2つの文字列を連結して出力するシンプルなノードです。

#### 入力

| 名前 | 型 | 必須 | 説明 |
|---|---|---|---|
| `string1` | STRING | ✅ | 1つ目の文字列 |
| `string2` | STRING | ✅ | 2つ目の文字列 |
| `delimiter` | STRING | ❌ | 区切り文字（デフォルト: 空文字） |

#### 出力

| 名前 | 型 | 説明 |
|---|---|---|
| `result` | STRING | 連結された文字列 |

#### 使用例

```
string1 = "Hello"
string2 = "World"
delimiter = ", "
→ result = "Hello, World"
```

---

### Load DICOM

| 項目 | 内容 |
|---|---|
| **カテゴリ** | `Crytus/Input` |
| **内部名** | `LoadDICOM` |

DICOM 形式の医用画像ファイルを読み込み、ComfyUI の IMAGE / MASK 形式に変換して出力します。

#### 入力

| 名前 | 型 | 必須 | 説明 |
|---|---|---|---|
| `path` | STRING | ✅ | DICOM ファイルのパス |

#### 出力

| 名前 | 型 | 説明 |
|---|---|---|
| `IMAGE` | IMAGE | 読み込まれた画像（RGB、0〜1正規化） |
| `MASK` | MASK | マスク（全ゼロ） |

#### 機能

- **ファイル選択ダイアログ**: ノード上の「Select File」ボタンをクリックすると、OS のファイル選択ダイアログが開きます。
- **画像プレビュー**: ファイルを選択すると、ノード上にDICOM画像のプレビューが表示されます。
- **ドラッグ＆ドロップ**: DICOM ファイルをノードに直接ドロップすることでも読み込めます。
- **VOI LUT / ウィンドウ処理**: DICOM ファイルに VOI LUT やウィンドウ設定が含まれている場合、自動的に適用されます。
- **マルチフレーム対応**: 複数フレームの DICOM ファイルではフレームごとにバッチとして出力されます。

#### 使用手順

1. ノード追加メニューから `Crytus/Input` → `Load DICOM` を追加
2. 以下のいずれかの方法でファイルを指定：
   - 「**Select File**」ボタンをクリックしてダイアログから選択
   - `path` 入力欄にファイルパスを直接入力
   - DICOM ファイルをノードに**ドラッグ＆ドロップ**
3. `Preview Image` ロードした結果を確認

---

## ⚠️ 注意事項

- ファイル選択ダイアログは **ComfyUI サーバーが動作しているマシン** 上で開きます（リモート接続時はサーバー側で表示されます）。
- ドラッグ＆ドロップでアップロードされたファイルは `crytus_nodes/uploads/` ディレクトリに保存されます。
- 対応OS: Windows（PowerShell によるダイアログ）、Linux（zenity によるダイアログ）

---

## 📄 ライセンス

MIT License

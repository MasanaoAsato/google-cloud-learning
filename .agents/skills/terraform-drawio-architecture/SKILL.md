---
name: terraform-drawio-architecture
description: Terraformコードを一次情報としてAWS、Microsoft Azure、Google Cloudの編集可能なdraw.ioアーキテクチャ図を最終成果物として新規作成または更新する。`.tf`、`.tf.json`、Terraformモジュール、plan JSON、state、既存の`.drawio`やSVGからクラウド構成図を生成する依頼、既存図をTerraformへ同期する依頼、複数クラウドの図のレイアウト・配色・アイコン・線・日本語ラベルを統一する依頼で使用する。SVGはスキル内蔵のレンダラで書き出す（Draw.io CLI不要）。
license: Apache-2.0 (see LICENSE; bundled icons: THIRD-PARTY-NOTICES.md)
---

# Terraform Draw.io アーキテクチャ

Terraformを構成の根拠、既存図と参考画像を視覚表現の根拠として扱う。`.drawio`を唯一の編集可能な正本かつ必須の最終成果物にする。SVGは`export_svg.py`で生成して添える追加成果物であり、出力失敗は図の完成を妨げない。

利用者のローカルVS CodeにDraw.io拡張（`hediet.vscode-drawio`）が導入済みで、`.drawio`を編集・閲覧できることを前提にする。実行環境で拡張の導入やGUI操作を自動化する必要はない。Draw.io CLIやデスクトップアプリは前提にしない。

Python 3.10以降が必要である。Pythonのコマンド名は環境により`python3`または`python`なので、`.py`は直接起動せず、常に`sh <skill-dir>/scripts/run_python.sh <script.py> ...`を使う。このランナーが利用可能なコマンドを選ぶ。

## 守る原則

- Terraformに無いリソース、接続、認証、冗長化、データフローを事実として描かない。
- 参考画像から構成内容を移さない。抽出するのは色、余白、配置、境界、線、ラベル、情報密度だけにする。
- SVGを直接編集して完成扱いにしない。SVGしか無い場合は視覚参照としてdraw.ioを再構成する。
- 既存draw.ioの意味と利用者が加えた説明を保つ。Terraformと矛盾する要素は黙って消さず、変更記録へ残す。
- 図を詳細なリソース台帳にしない。主要な境界、実行経路、依存関係、セキュリティ上の要点に絞る。
- 図中のタイトル、凡例、説明、経路名は原則日本語にする。Terraformアドレスは根拠メタデータへ保持し、ユーザーが図中表示を明示した場合だけ表示する。
- アイコンはAWS、Azure、GCP共通の優先順位で選ぶ。(1) Draw.io標準ライブラリのステンシル、(2) Draw.ioサイドバー埋め込みの画像アイコン、(3) どちらも無ければ破線の四角＋サービス名。利用者やインターネットのような一般的な主体にもアイコンを使い、四角のフォールバックに頼った要素は`architecture-notes.md`へ記録する。
- **完成前にプレビュー画像でレイアウトの破綻だけは必ず確認する。** 検査スクリプトは重なりと根拠の欠落を見つけるが、枠線に乗った文字や不自然な折り返しは画像を見るまで分からない。
- Draw.ioと画像出力の背景は白にする。`build_drawio.py`が最背面へ置く白いキャンバス全面セルは、画像書き出し時にも意図した外周余白を残すためのメタ要素なので削除しない。
- SVGは`export_svg.py`で書き出す。事前レンダリングが無いアイコンがあると、黙って劣化させずに明確なエラーで失敗する。その場合の対処は手順4に従い、ツールの導入やGUIの自動操作での回避はしない。
- ユーザーが日本語ではない言語利用者である場合、ラベルや図中の説明の言語もユーザーの言語にする。

## 手順

### 1. Terraformの根拠を集める

```bash
bash <skill-dir>/scripts/collect_terraform_context.sh <terraform-root>
```

`references/terraform-evidence-and-spec.md`を読み、provider、resource、data、module、variable、output、参照式、ネットワーク境界を追跡する。収集スクリプトの出力は行番号付きの索引（BLOCK HEADERS / REFERENCE CANDIDATES）であり、ソース全文は含まない。`confirmed`にする要素は該当する`.tf`ファイルを読んで根拠の行を確認する。コード行またはplan/stateのJSONパスへ戻れない要素を`confirmed`にしない。

Terraform CLIは既定では使わない。静的解析で確定できず、CLIを使えば`confirmed`へ格上げできる要素が残った場合だけ、`terraform_exec.sh`経由で`init`、`validate`、plan JSON、stateの順に必要な範囲を使う。ユーザーが禁止した場合は使わない。失敗したら静的解析へ戻る。`apply`は実行しない。CLIが`.terraform.lock.hcl`などを書き換えたら元に戻す。

既存図を更新する場合は`references/updating-existing-diagrams.md`を読む。

### 2. 中間仕様を書く

`references/terraform-evidence-and-spec.md`の「中間仕様」の形式で`architecture-diagram.json`を作る。寸法と配置の判断は`references/layout-and-style.md`を読む。

- ノードと線へ`evidence`を付け、`confirmed`、`derived`、`unresolved`を区別する。
- 省略した主要候補を`omissions`へ残す。推測を描く必要がある場合だけ`unresolved`にし、オレンジの破線と「要確認」を使う。
- 座標は書かない。各要素へ`grid: {"row": 行, "col": 列}`で親の中の位置だけを宣言すれば、カード寸法、境界寸法、キャンバス、凡例位置は`build_drawio.py`が余白の契約を満たす形で計算する。
- 流れは既定で左から右。入口（利用者・外部システム）を最左の列に置き、処理の段階を列で進め、並列要素は行で分ける。主要経路が流れに逆行すると検査が警告する。上から下が明らかに適する場合だけルートへ`"flow": "vertical"`を宣言し、理由を`architecture-notes.md`へ残す。
- 自動配置を動かしたい要素にだけ`geometry`を明示する。`geometry`を書いた要素は計算されず、そのまま尊重される。
- `service`にはアイコンを引くための正式サービス名または主体名、`label`には図に出す表示名を書く。両者は別物でよい（`service`は`cloud load balancing`、`label`は`ターゲット HTTPS プロキシ`）。`shape_style`はカタログを上書きするときだけ使う。
- ラベルに手で改行を入れない。折り返しは語の境界で自動的に決まる。
- `terraform_address`は既定で表示しない。

### 3. 生成して画像を見る

1コマンドで、仕様検査、`.drawio`生成、生成物検査、プレビュー画像までを行う。

```bash
sh <skill-dir>/scripts/run_python.sh <skill-dir>/scripts/build_drawio.py \
  architecture-diagram.json \
  --output architecture.drawio \
  --preview /tmp/architecture-preview.png
```

検査が落ちたらメッセージのとおりに中間仕様を直す。通ったらプレビュー画像を開き、**レイアウトの破綻**を見る。ここだけは省略しない。

- 境界名が枠線に乗っていないか
- 日本語が語の途中で折れていないか（「プロキ / シ」「束 / ねる」）
- カード内の文字やアイコンが枠に接していないか
- 線のラベルが隣のカードや境界名に重なっていないか
- 枠内に、要素の描き忘れに見えるほど大きな空白が無いか

プレビューは事前レンダリングのあるアイコンを実描画し、無いものだけ薄い四角のプレースホルダで描く。最終的な線の経路はVS Codeで`.drawio`を開くか、手順4で書き出すSVGで確認する。

問題があれば中間仕様かstyle tokenを直して同じコマンドを再実行する。draw.ioやSVGを手で修正して辻褄を合わせない。多くの問題は`grid`の行・列やラベルの長さの変更で直る。特定の要素だけ位置を微調整したい場合は、`--resolved-spec <path>`で計算済み座標を書き出し、その要素の`geometry`として中間仕様へ貼り付けて動かす。

生成された`.drawio`には、白いページ背景と、キャンバス全面を覆う白塗り・枠線なし・ロック済みの背景セルが含まれる。背景セルがエクスポート範囲をキャンバス寸法へ広げるため、仕様で確保した外周余白が画像にも残る。

### 4. draw.ioを検証し、SVGを書き出す

まず必須成果物の`.drawio`を検証する。SVGの有無にかかわらず、この検査が通れば図そのものは完成できる。

```bash
sh <skill-dir>/scripts/run_python.sh <skill-dir>/scripts/validate_artifacts.py \
  --spec architecture-diagram.json --drawio architecture.drawio
```

次にSVGを書き出す。Draw.io CLIは不要で、スキル内蔵のレンダラが全アイコンを実描画し（アプリ専用Stencilは`assets/icon-styles.json`の事前レンダリングで代替）、編集可能なXMLを`content`属性へ埋め込む。Draw.ioへ再インポートできるSVGになる。

```bash
sh <skill-dir>/scripts/run_python.sh <skill-dir>/scripts/export_svg.py architecture.drawio architecture.svg
```

`no pre-rendered SVG for ...`で失敗した場合、そのアイコンの事前レンダリングがまだ無い。ネットワークが使えるならエラーメッセージの指示どおり`maintenance/render_stencils.py`で一度だけ取り込み、再実行する。使えなければSVGを省略し、理由を`architecture-notes.md`へ記録して`.drawio`を最終成果物とする。品質を落としたSVGは作らない。

書き出せたら、埋め込みXMLが`.drawio`と一致することを検査する。検査に失敗したSVGは成果物に含めない。

```bash
sh <skill-dir>/scripts/run_python.sh <skill-dir>/scripts/validate_artifacts.py \
  --spec architecture-diagram.json --drawio architecture.drawio --svg architecture.svg
```

利用者がVS CodeのDraw.io拡張で手動エクスポート（ファイル > Export）したSVGは、アプリ純正の描画を持つ同等以上の成果物として扱う。

### 5. 説明を残す

`assets/architecture-notes-template.md`を使って`architecture-notes.md`を書く。Terraformから読み取った構成、依存関係と通信経路、既存図からの変更点、省略した要素と理由、確認できなかった事項、要確認事項、Terraform CLIをどこまで使ったか、プレビューで直した点を残す。SVGを生成できなかった場合はその理由を記録する。

## 出力先

指定が無ければTerraformルートまたはテーマディレクトリへ次を置く。既存ファイルは必ず読んでから更新し、利用者の加筆を残す。

- `architecture.drawio`（正本かつ最終成果物）
- `architecture-diagram.json`（根拠と描画指定の中間仕様）
- `architecture-notes.md`

次は書き出しと検査に成功した場合だけ成果物に含める。

- `architecture.svg`（追加成果物。編集可能なXMLを`content`属性に埋め込む）

AWS、Azure、Google Cloudが混在する場合は、クラウドごとの上位境界を分け、共通の凡例と線規則を使う。

## 完了条件

`build_drawio.py`の検査は、XMLの妥当性、白背景セル、根拠の付与、アイコンの実在とクラウド整合、境界様式、余白の契約、日本語の折り返し、Terraformアドレスの非表示を機械的に保証する。検査が通っていることに加えて、機械検査できない次の点を確認する。

- 重要なTerraform要素が反映され、未反映には理由がある。
- 境界がコードと一致し、グローバルとリージョナルのスコープを誤っていない。
- プレビュー画像を見てレイアウトの破綻が無く、直した点を`architecture-notes.md`へ記録している。
- SVGを生成できなかった場合は、失敗理由（不足していた事前レンダリングなど）を`architecture-notes.md`へ記録し、`.drawio`を最終成果物として明示している。生成できた場合は`validate_artifacts.py --svg`で埋め込みXMLの一致を検査している。

## 参照ファイル

- `references/terraform-evidence-and-spec.md`: Terraform解析、動的補助解析、根拠の格付け、中間仕様の形式
- `references/layout-and-style.md`: 余白の契約、境界、文字、アイコン、線、プロバイダ固有規則
- `references/updating-existing-diagrams.md`: 既存図の構造抽出と差分整理

## スクリプト

- `collect_terraform_context.sh` / `terraform_exec.sh`: Terraformの静的収集とCLI実行
- `build_drawio.py`: 仕様検査、座標計算、`.drawio`生成、生成物検査、プレビュー画像を1コマンドで実行
- `layout.py`: `grid`宣言から寸法と座標を計算するエンジン。`geometry`明示の要素は触らない
- `preview.py`: `.drawio`からプレビュー画像だけを作り直す
- `validate_diagram_spec.py` / `validate_artifacts.py`: 個別に検査したいときに使う。`--svg`は書き出し後の確認用
- `icon_catalog.py`: アイコン名の検索（`--provider`）と手動でのカタログ拡張（`--harvest`）
- `run_python.sh`: Python 3.10以降の`python3`または`python`を選んでスクリプトを実行する
- `text_layout.py`: 日本語の折り返し確認（`sh scripts/run_python.sh scripts/text_layout.py "ラベル" 176 13`）
- `inspect_drawio.py`: 既存`.drawio`やSVGから構造を抽出
- `export_svg.py`: Draw.io CLI無しでSVGを書き出す。実アイコンで描き、編集可能なXMLを埋め込む
- `self_test.py`: スキルを変更したときの回帰テスト
- `drawio_styles.py`: 色・角・文字サイズなどstyle文字列の生成。見た目を変えるときはここを見る

ネットワークを使うメンテナンス専用ツールは`maintenance/`にある（`render_stencils.py`: アプリ専用Stencilの事前レンダリングをカタログへ追加。`sync_sidebar_icons.py`: ステンシルが無いサービスのサイドバー埋め込みアイコンをDraw.io上流から取り込み・更新。`sync_upstream.py`: Draw.io公式パレットと`style-tokens.json`の突き合わせ。CI化の雛形は`ci-sync-drawio-upstream.yml`）。

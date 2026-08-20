# Terraformの根拠と中間仕様

## 目次

1. 情報源の優先順位
2. 静的解析
3. Terraform CLIによる補助解析
4. 根拠の状態
5. 図へ含める判断
6. 中間仕様

## 情報源の優先順位

構成の事実は次の順で判断する。

1. Terraformコードとローカルモジュール
2. 成功したplanのJSON
3. 許可を得て取得したstate
4. 既存draw.ioにある説明
5. SVGや参考画像

既存図と画像はTerraformの不足を埋める根拠にしない。矛盾した場合はTerraformを優先し、変更記録へ残す。

## 静的解析

次を読む。

- `terraform`と`required_providers`
- `provider`のalias、region、project、subscriptionなど
- `resource`と`data`
- `module`のsource、入力、出力参照
- `variable`の型、既定値、validation
- `locals`
- `output`
- `depends_on`
- resource、data、module、local、variable間の参照式
- `count`、`for_each`、dynamic block、条件式
- `moved`、`import`、`removed`

リソース種別だけで通信を決めない。明示参照はTerraformの評価依存を示すが、必ずしも通信経路を示さない。通信線は、ポート、URL、backend、target、origin、network、subnet、IAM principalなど、関係を裏付ける設定がある場合に描く。

ローカルモジュールは展開してアドレスを追跡する。取得されていないリモートモジュールは、moduleブロックの入出力だけを確定情報とし、内部リソースを推測しない。

## Terraform CLIによる補助解析

静的解析を先に終わらせる。CLIを使うのは、`count`・`for_each`・module展開・条件式のせいで静的解析では確定できず、かつCLIなら`confirmed`へ格上げできる要素が残った場合だけにする。静的解析だけで全要素の根拠が付くならCLIは実行しない（`init`のprovider取得だけで数分かかることがある）。ユーザーが禁止した場合も実行しない。

実行する場合は、コマンド実行前にネットワーク、認証、バックエンド、機密情報、リポジトリ変更の影響を確認する。

Terraformの起動には`<skill-dir>/scripts/terraform_exec.sh`を使う。このラッパーは`TERRAFORM_BIN`、対象ディレクトリのmise設定、PATHの順に解決する。miseで版を固定しているプロジェクトでは、作業シェルをactivateしていなくても設定されたTerraformを使える。

```bash
bash <skill-dir>/scripts/terraform_exec.sh \
  --cwd <terraform-root> -- version
```

### 初期化と検証

- `TF_DATA_DIR`を一時ディレクトリへ向け、可能な限り作業ツリーへ`.terraform`を作らない。
- ロックファイルがある場合は`-lockfile=readonly`を優先する。
- バックエンドが不要なら`terraform init -backend=false -input=false`を使う。
- リモートmoduleやproviderの取得に失敗しても静的解析を続ける。
- `terraform validate -json`の診断は構成解釈の補助に使う。

`init`や`validate`もラッパーの`--`以降へ渡す。例:

```bash
terraform_diagram_data_dir="$(mktemp -d)"
TF_DATA_DIR="$terraform_diagram_data_dir" \
  bash <skill-dir>/scripts/terraform_exec.sh \
  --cwd <terraform-root> -- init -backend=false -input=false -lockfile=readonly
```

### plan JSON

planはユーザーの認証、変数、バックエンドが利用でき、実行が許可されている場合だけ使う。

- `-input=false -lock=false`を使う。
- 既存リソースの更新を目的としない解析では`-refresh=false`を検討する。
- planファイルと`terraform show -json`の出力は一時ディレクトリへ置く。
- plan内の`sensitive_values`を尊重し、値を図やレポートへ転記しない。
- planが失敗した場合は部分的な診断だけを使い、構成を推測しない。

### state

stateには秘密値や内部識別子が含まれ得る。必要性と許可を確認し、`terraform state pull`の結果を一時領域だけに保存する。stateは実体数、解決済みID、module展開の確認に使い、図へ秘密値、実プロジェクトID、アカウントID、IP、メールアドレスを載せない。

`terraform apply`、`import`、state変更コマンドは実行しない。

## 根拠の状態

各ノード、コンテナ、エッジを次のいずれかにする。

- `confirmed`: resource/data/moduleブロック、明示設定、plan/stateで直接確認できる。
- `derived`: module入出力や複数の参照を追跡して導出できる。導出元をすべて記録する。
- `unresolved`: 候補はあるがコードから確定できない。通常は図へ含めず、必要なら「要確認」と描く。

`evidence`は次の形にする。

```json
{
  "source": "architectures/01/modules/load_balancer/main.tf",
  "line": 42,
  "expression": "backend_service = google_compute_backend_service.main.id",
  "note": "バックエンド関連付け"
}
```

plan/stateの場合は`source`へ一時ファイル名ではなく`terraform plan JSON`または`terraform state`と書き、`json_path`を付ける。機密値は含めない。

## 図へ含める判断

含めるもの:

- 利用者または外部システムの入口
- リージョン、ゾーン、network、subnet、clusterなど主要境界
- compute、load balancing、database、storage、messagingなど主要サービス
- セキュリティ判断を理解するために必要なIAM、firewall、gateway
- 可用性やデータ経路を理解するために必要な複製関係

省略候補:

- ラベル、タグ、細かなIAM bindingの全件
- ログ設定、通知先など、主題でない補助リソース
- 反復リソースの全インスタンス。代表ノードと台数表示で代替する
- providerやrandomなど、実行時の構成要素ではないもの

省略した重要候補は`omissions`へ理由を残す。

## 中間仕様

`architecture-diagram.json`の形式の正は`scripts/validate_diagram_spec.py`である。検査エラーのメッセージが修正方法を指示するので、迷ったら実行する。

ルートに必須: `schema_version`（1固定）、`title`、`provider`（`aws`/`azure`/`gcp`/`multi`）、`source_roots`、`containers`、`nodes`、`edges`、`omissions`、`unresolved`。任意: `subtitle`、`flow`（主要経路の向き。`horizontal`＝左から右が既定。上から下が明らかに適する図だけ`vertical`）、`canvas`（`width`/`height`、整数px。省略すれば内容から計算される）、`legend`（`show`/`x`/`y`/`width`。省略すれば左下へ自動配置）、`show_terraform_addresses`。

| 要素 | 必須フィールド | 任意フィールド |
| --- | --- | --- |
| container | `id`、`kind`、`label`、`provider`、`status`、`evidence` | `grid`、`geometry`、`parent`（省略時はトップレベル）、`variant`（例: subnetの`public`） |
| node | `id`、`provider`、`service`、`role`、`label`、`status`、`evidence` | `grid`、`geometry`、`container`、`terraform_address`、`show_terraform_address`、`shape_style` |
| edge | `id`、`from`、`to`、`kind`、`label`、`status`、`evidence` | `bidirectional`、`waypoints`（自動配置では使わない） |

配置は`grid: {"row": 行, "col": 列}`で親の中の位置を宣言するのが基本形で、寸法と座標は生成時に計算される。`grid`も`geometry`も無い要素は宣言順に流れの方向（既定は左から右）へ並ぶ。`geometry`（`x`/`y`/`width`/`height`、親からの相対座標）を書いた要素は計算されず、そのまま使われる。

- `kind`（container）: `cloud`、`organization`、`account`、`subscription`、`resource-group`、`folder`、`project`、`region`、`zone`、`network`、`subnet`、`cluster`、`namespace`、`group`、`external`
- `kind`（edge）: `traffic`（同期）、`async`（非同期）、`peer`（双方向・対等）、`control`（制御・管理）、`dependency`（構成上の依存）、`special`（VPN・専用線などの特殊経路）
- `status`: `confirmed`/`derived`/`unresolved`。`provider`（要素単位）: `aws`/`azure`/`gcp`/`neutral`
- 文字数の上限: nodeの`label`30字、`role`32字、edgeの`label`24字。超える説明は`architecture-notes.md`へ
- `omissions`と`unresolved`の各項目は`item`と`reason`が必須

該当アイコンが無いサービスは近いアイコンへ置換せず、上位サービスへ集約するか`omissions`へ移す。`terraform_address`は既定で可視化しない。

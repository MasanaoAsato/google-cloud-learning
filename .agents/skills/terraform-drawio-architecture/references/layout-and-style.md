# レイアウトと視覚スタイル

寸法の正本は`assets/style-tokens.json`、アイコンの正本は`assets/icon-styles.json`である。ここはその意図と、コードでは表せない判断を書く。

上流由来の値（`providers.aws.groups`、`edges_gcp`）は手で編集しない。draw.io公式パレットの世代交代には`maintenance/sync_upstream.py --write`で追従する（出典と検証日は`style-tokens.json`の`upstream`にある。CI化する場合は`maintenance/ci-sync-drawio-upstream.yml`を参照）。可読性のための意図的な逸脱は`providers.aws.group_overrides`に置く。生成時に上流を参照することはしない。図の見た目が生成のたびに変わると再現性が失われる。

## 余白の契約

自動配置はこの契約を構築時に満たす。手動`geometry`を含む仕様は`validate_diagram_spec.py`が検査し、詰まりすぎはエラー、空きすぎは警告になる。両方を見るのは、窮屈な枠が意味の階層を潰す一方で、広すぎる枠は空白を「描き忘れた要素」として読ませてしまうからだ。

| 項目 | 既定 | 意図 |
| --- | --- | --- |
| `outer_padding` | 40px | キャンバス外周 |
| `container_header` | 50px | 境界の上辺に空ける帯。境界名がここに入る |
| `container_padding` | 30px | 境界の左右下の内側余白 |
| `node_gap` | 30px | 同じ親を持つ要素の間隔 |
| `card_width` / `card_height` | 280 / 100px | カードの基準寸法。最小は260×96px |
| `icon_size` | 48px | カード内のアイコン |
| `card_padding_x` / `card_padding_y` | 20 / 14px | カード内の余白 |
| `card_icon_gap` | 16px | アイコンとラベルの間 |

キャンバス上辺はタイトル帯を避けて90px以上空ける。線のラベルを置く隙間も余白として設計し、ラベル幅より30px以上広く取る。`text_layout.measure()`で幅を見積もれる。

Draw.ioは画像書き出し時に実セルの外接矩形まで余白を詰めるため、`build_drawio.py`は白いキャンバス全面セルを`layer-background`へ追加する。このセルが書き出し範囲をキャンバス寸法へ固定し、上記の`outer_padding`を画像にも残す。セルは白塗り・枠線なし・ロック済みとし、Draw.ioのページ背景も`#FFFFFF`にする。アーキテクチャ要素ではないのでTerraform根拠は付けない。

## レイアウト

配置は`grid`（親の中の行・列）で宣言し、寸法と座標は`scripts/layout.py`が計算する。エンジンは余白の契約を構築時に満たし、同じ列の要素の幅と中心をそろえるので、縦に繋ぐ線は曲げずにまっすぐ通る。カードの高さはラベルと役割の折り返し結果から決まる。

**流れの向きは既定で左から右にする。** 利用者や外部システムなどの入口を最左の列に置き、処理の段階が進むごとに右の列へ割り当てる。並列な要素は同じ列の別の行に置く。上から下が明らかに読みやすい場合（段階が少なく縦の分岐が主、縦長の文書に貼るなど）だけルートへ`"flow": "vertical"`を宣言して切り替え、その判断理由を`architecture-notes.md`へ残す。

この規則の本質は、**主要経路（traffic / async / special）をひとつの方向へ一方向に流し、線が縦横無尽に走る図を防ぐ**ことにある。流れに逆行する主要経路は検査が警告する。意図したループ（リトライ、コールバック）だけを残し、それ以外は列（縦なら行）の割り当てを流れに沿って並べ直す。管理・監視系（control / dependency）の線は逆行してよい。

- 外部利用者や外部システムはクラウド境界の外（トップレベルの別コンテナ）へ置く。外向き通信の出口は流れの終端側へ置く。
- 横に長くなりすぎるとREADMEへ貼ったとき文字が読めなくなるので、縦横比は2:1程度までに収める。行と列の割り当てで調整する。
- 境界は内容に合わせた大きさに自動で決まる。1枚のカードのために深い入れ子を作らない。
- 線の始点と終点の並びを`grid`で先に決めてから細部を詰めると、後から線を曲げずに済む。

### 自動配置の微調整

`build_drawio.py --resolved-spec <path>`で計算済み座標を書き出し、動かしたい要素にだけ`geometry`を貼り付けて調整する。`geometry`を書いた要素はエンジンが触らない。手動で書く場合は10pxグリッドに乗せ、親コンテナからの相対座標にする。

- 縦に繋ぐ2つのカードは中心x座標をそろえる（自動配置の同じ列なら保証される）。
- 境界名は左上にあるため、境界を跨ぐ線はラベルが境界名と重ならない位置を通す。
- カードへ真上から入る線が境界名の帯を通らざるを得ない場合は、線の終点を境界コンテナ自体にする。矢印が枠の上辺で止まり、ラベルは枠の外の隙間に入る。

## 境界

**大前提: 境界を意味する専用シェイプがあるクラウドでは、必ずそれを使う。** Draw.ioの公式ライブラリを調査した結果は次のとおりで、`drawio_styles.py`がこの規則を実装している。

| クラウド | 専用シェイプ | 扱い |
| --- | --- | --- |
| AWS | 「AWS / Groups」（`shape=mxgraph.aws4.group` + `grIcon`） | 必ず使う |
| Google Cloud | 「GCP / Zones」（囲い線なし・角丸2pxの塗り領域） | 必ず使う |
| Azure | 存在しない（draw.ioにもMS公式アイコン集にも境界シェイプは無い） | 汎用規則で描く |

共通の規則:

- 上位から下位へ、cloud、account/subscription/project、region、zone、network、subnet、cluster/namespaceの順に入れ子にする。
- **外側の領域ほど枠線を太くする。** `BOUNDARY_BORDER_PROFILES`が cloud 3px → account/project 2.5px → region 2px → zone/network 1.5px の順で単調に細くする。subnetは枠線を持たない。
- **subnetは囲い線なしの塗りだけで示す。** AWS公式Groups（`grStroke=0`）とGCP公式Zonesがこの表現であり、汎用規則もそれに合わせる。public subnetは薄い緑、private subnetは薄い水色。
- **親子関係にあるnetworkとsubnetは同系色でまとめる。** 役割の違い（public/private）は塗り色で分ける。
- **境界は直角にする。** 角丸の入れ子は装飾に見える。例外はGCP公式Zoneのカードと同じ2pxの微小な角丸だけ。
- 境界名は`container_header`帯の内側に置く。境界セル自身のラベルにすると枠線の上に描かれる。`build_drawio.py`は必ず専用のラベルセルを作り、`grIcon`付きの境界では角のアイコンの右へ逃がす。
- グローバル、regional、zonalのスコープをコードと公式仕様から確認し、見た目だけでregion内へ入れない。
- 隣接して入れ子になる境界は、枠線あり同士なら線色・線幅・破線パターンのうち最低2つを、塗りのみ同士なら塗り色を変える。色覚や縮小表示に左右されず階層を追えることが目的である。

## 文字

- タイトル20px、上位境界16px、下位境界14px、サービス名13px、注釈11pxを基準にする。
- サービス名を先、短い役割を次に置く。2行を超える説明は`architecture-notes.md`へ移す。
- Terraformアドレスは既定で表示せず、セルのメタデータへ保持する。

### 日本語の折り返し

折り返しは`text_layout.py`が決め、`build_drawio.py`が再折り返し不可の形でDraw.ioへ渡す。ブラウザに任せるとCJKは任意の文字間で折れ、「ターゲット HTTPS プロキ / シ」のような読めない分断が起きる。

- ラベルに手で改行を入れない。行数と改行位置は寸法から決まる。
- 分割してよいのは、空白、文字種の変わり目（ラテン↔カタカナ↔漢字かな）、`・`や`/`などの区切りの後だけである。カタカナ語の内部と、漢字＋送り仮名（`束ねる`）は割らない。
- 行数は最小に、そのうえで各行の幅を均す。末尾に1語だけ残る形は避ける。
- 収まらない場合は検査がエラーにする。カードを広げるか、`role`を短くして詳細をメモへ移す。

## アイコン

- AWS、Azure、GCP共通の優先順位で`icon_catalog.py`が名前から解決する。(1) Draw.io標準ライブラリのステンシル、(2) Draw.ioサイドバー埋め込みの画像アイコン（ステンシル化されていない新しめのサービス）、(3) どちらも無ければ`build_drawio.py`が破線の四角＋サービス名で描き、警告を出す。

```bash
sh <skill-dir>/scripts/run_python.sh <skill-dir>/scripts/icon_catalog.py --provider=gcp "Cloud Run" "利用者"
```

- 利用者、インターネット、ブラウザ、オンプレミスのような一般的な主体もアイコンで描く。一部だけ絵が無い図は未完成に見える。
- カタログは対象クラウドのライブラリを優先する。GCPの図にAWSの人型アイコンが混ざると、どのクラウドの話か一瞬迷わせる。
- カタログに無いものは、ネットワークが使えるなら`maintenance/sync_sidebar_icons.py`でDraw.io上流から取り込む。Draw.ioで実際に置いた`.drawio`からの`icon_catalog.py --harvest`は手動の最終手段。style文字列を推測して書くとDraw.ioでは空の四角になる。
- 該当アイコンが無い要素を、近い別サービスのアイコンで代用しない。取り込めない場合は四角のフォールバックのまま完成させてよいが、その旨を`architecture-notes.md`へ残す。上位サービスへ集約して省略する場合は理由を`omissions`へ残す。

## 線

線は次の6種別で描き分ける。色と太さの正本は`style-tokens.json`の`edges`である。

| kind | 種類 | 線種 | 色 | 矢頭 | 表すものの例 |
| --- | --- | --- | --- | --- | --- |
| `traffic` | 同期通信 | 実線 | グレー | 片方向 | HTTP、gRPC、SQLの呼び出し |
| `async` | 非同期通信 | 破線 | グレー | 片方向 | キュー、Pub/Sub、通知 |
| `peer` | 双方向・対等 | 実線 | グレー | 両端 | レプリケーション、ピアリング、WebSocket |
| `control` | 制御・管理 | 細い実線 | アンバー | 片方向 | ログ、メトリクス、デプロイ、IAM操作 |
| `dependency` | 構成上の依存 | 点線 | 薄グレー | 片方向 | DNS参照、設定参照、IaC上の依存 |
| `special` | 特殊経路 | 太い実線 | 青 | 片方向／両端 | VPN、専用線、PrivateLink |

- `unresolved`ステータスの線はオレンジの破線と「要確認」で描く。
- 双方向を確認できない限り両矢印にしない。`peer`以外で両端矢印が要る場合は`bidirectional: true`を使う（主に`special`のVPNやピアリング）。
- **GCPの図では、専用の矢印スタイル「GCP / Paths」があるので必ず使う。** `edges_gcp`トークンが該当する種別だけ公式の線へ置き換える（traffic/peer/asyncは公式ブルー`#4284F3`、dependencyは公式グレー`#9E9E9E`の点線、矢頭は`blockThin`）。controlとspecialとunresolvedは共通規則のまま。AWSとAzureには矢印の専用スタイルが無いため共通規則で描く。
- 物理・論理接続の意味が無いTerraform評価依存（`depends_on`）は描かない。
- 実通信と誤認されないラベルを付ける。

## 凡例

- 左下、または図の流れを妨げない位置へ置き、外枠と全項目をキャンバス内へ収める。
- 図で実際に使った線種と状態だけを載せる。`要確認`が1件でもあれば意味を説明する。
- タイトル直下に対象環境やTerraformルートを短く書く。実アカウントIDなどは載せない。

## プロバイダ固有

### AWS

境界はDraw.io公式「AWS / Groups」パレット（現行世代）で描く。`kind`と`variant`から`drawio_styles.py`が公式のstyle文字列を組み立てるので、`shape_style`で上書きしない。`grIcon`の綴りが違うと角のアイコンは黙って消える。

| kind | 公式Group | 枠線 | 塗り |
| --- | --- | --- | --- |
| cloud | AWS Cloud（`group_aws_cloud_alt`） | 濃紺 `#232F3E` 実線 | なし |
| account | AWS Account（`group_account`） | `#CD2264` 実線 | なし |
| region | Region（`group_region`） | `#00A4A6` 破線 | なし |
| zone | Availability Zone（公式でもアイコン無し） | `#147EBA` 破線 | なし |
| network | VPC（`group_vpc2`） | 紫 `#8C4FFF` 実線 | なし |
| subnet `variant: public` | Public subnet（`grStroke=0`） | なし | 薄緑 `#F2F6E8` |
| subnet | Private subnet（`grStroke=0`） | なし | 薄青緑 `#E6F6F7` |
| external | Corporate data center（`group_corporate_data_center`） | `#7D8998` 実線 | なし |

- 現行公式パレットのVPCは紫である（緑のVPCと`group_vpc`は旧2019世代）。参考画像が旧配色でも現行公式に従う。
- Route 53、CloudFrontなどグローバルサービスをRegion内へ誤配置しない。
- Availability Zoneを横並びにし、冗長構成は対応する位置へ配置する。

### Google Cloud

境界はDraw.io公式「GCP / Zones」の表現（囲い線なし・角丸2px・塗りのみ）で描く。塗りはすべて公式Zoneパレットの色で、階層への割り当ては`style-tokens.json`の`providers.gcp`が正本である（cloud `#F6F6F6`、project 白、region `#F1F8E9`、network `#E1F5FE`、subnet `#E0F2F1`、cluster `#F3E5F5`、namespace `#FFEBEE`、オンプレミス `#EFEBE9`）。

- 矢印は公式「GCP / Paths」を使う（線の節を参照）。
- `google_compute_global_address`、転送ルール、Cloud DNS、Cloud Armorはリージョン指定を持たない。region境界の中へ入れない。
- 同じサービスの構成要素を複数描く場合（転送ルール、プロキシ、バックエンドサービスなど）は、同じアイコンを繰り返し、`label`で構成要素名、境界名でサービス名を示す。
- 経路の分岐に関わらない設定リソース（URLマップ、SSL Policy、IAMポリシーなど）はカードを増やさず、`role`とメモへ移す。
- GKEはproject、region、cluster、namespaceまでを必要な粒度で使い、個々のKubernetes objectを描かない。

### Microsoft Azure

draw.ioにもMicrosoft公式アイコン集にも境界専用シェイプが存在しない（Subscriptions等は小さなサービスアイコンのみ）。そのため汎用規則をAzure配色で適用する。外側ほど太く、VNetとsubnetは同系の青でまとめる。

| 境界 | 線色 | 線幅 | 破線パターン | 塗り |
| --- | --- | ---: | --- | --- |
| Cloud | Azure Blue `#0078D4` | 3px | 実線 | 白 |
| Subscription / Resource Group | 濃灰 `#5F6368` | 2.5px | 長い破線 `12 6` | 白 |
| Region | 灰 `#9AA0A6` | 2px | 中間の破線 `8 6` | 白 |
| Virtual Network | Azure Blue `#0078D4` | 1.5px | 実線 | なし |
| Subnet | なし | — | — | 薄青 `#E6F2FA` |

- Network Security Groupなど境界に効くリソースは、関連付けをコードで確認したうえで対応するsubnetの縁近くへ置く。
- ExpressRoute、VPN Gateway、BastionはVirtual Network境界との関係を明示する（VPN・専用線は`special`の線）。
- subscription、resource group、regionのうち、コードと図の理解に必要な境界だけを描く。

## 参考画像を渡されたとき

構成の事実と視覚スタイルを混ぜない。抽出するのは色、余白、配置、境界、線種、情報密度だけで、画像にあるリソースや経路を中間仕様へ写さない。余白の契約、境界の直角、境界名の位置、日本語の折り返し規則は上書きしない。これらは読みやすさの下限であって好みの問題ではない。出典や再利用権が不明な画像を成果物やSkillへ複製しない。

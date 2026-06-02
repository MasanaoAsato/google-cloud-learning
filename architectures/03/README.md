# Architecture 03 — GCP: Cloud Run + Cloud NAT によるセキュアな Web アプリケーション公開

このディレクトリ（architectures/03）は、Cloud Run 上のコンテナアプリケーションを HTTPS ロードバランサー経由で公開しつつ、Cloud Run からのアウトバウンド通信を Cloud NAT 経由で固定 IP 化する構成です。Cloud Armor による地理ベースのアクセス制御や、Certificate Manager によるマネージド証明書の管理も含む、本番に近いアーキテクチャパターンを学べます。

## 学習の目的

- **Cloud Run の Direct VPC egress**：Cloud Run のアウトバウンド通信を VPC 経由にルーティングする方法。`egress = "ALL_TRAFFIC"` によりすべての外向き通信を VPC 経由に強制。
- **Cloud NAT による外部 IP の固定化**：Cloud Run からのアウトバウンド通信を Cloud NAT 経由にすることで、外部サービスへの通信元 IP を固定する設計パターン。
- **Global External Application Load Balancer**：Cloud Run をバックエンドとしたグローバル HTTPS ロードバランサーの構成。Serverless NEG を使用。
- **Certificate Manager**：DNS 認証によるマネージド SSL 証明書の発行と Certificate Map によるマッピング。
- **Cloud Armor**：地理ベースのアクセス制御（日本国内の IP のみ許可、それ以外は 403）。
- **Cloud DNS**：カスタムドメインの A レコードと証明書検証用 CNAME レコードの管理。
- **Cloud Run の Ingress 制御**：`INGRESS_TRAFFIC_INTERNAL_ONLY` により、ロードバランサー経由のアクセスのみを許可。
- **Terraform モジュール化**：再利用可能なモジュール（network / cloud_run / load_balancer / cloud_armor / cloud_dns / cloud_nat / artifact_registry）による構成管理。

## 想定するアーキテクチャ要素

- **VPC Network**（`test-vpc-network`）：カスタムモードの VPC。`auto_create_subnetworks = false`。
  - Subnet（`test-test-nat-subnetwork` / 10.0.0.0/16）：Cloud Run の Direct VPC egress および Cloud NAT が使用するサブネット。
- **Cloud Run**（`test-cloud-run-service`）：
  - コンテナイメージ：`us-docker.pkg.dev/cloudrun/container/hello`（サンプル）
  - Ingress：`INGRESS_TRAFFIC_INTERNAL_ONLY`（LB 経由のみ）
  - VPC Access：Direct VPC egress（`ALL_TRAFFIC`）で Subnet に接続
  - スケーリング：0〜3 インスタンス、CPU: 1、メモリ: 512Mi
  - IAM：`allUsers` に `roles/run.invoker` を付与（パブリック公開）
- **Global External Application Load Balancer**：
  - 外部 IP（`test-lb-ip`）：グローバル IPv4 アドレス
  - Serverless NEG：Cloud Run サービスをバックエンドとして接続
  - Backend Service：HTTPS プロトコル、Cloud Armor ポリシー適用、ロギング有効（サンプルレート 1.0）
  - HTTP → HTTPS リダイレクト（301）
  - SSL Policy：MODERN プロファイル、TLS 1.2 以上
- **Certificate Manager**：
  - DNS 認証（`PER_PROJECT_RECORD`）によるマネージド証明書
  - 対象ドメイン：`mystudy.com`、`*.mystudy.com`
  - Certificate Map Entry：`dev.mystudy.com` にマッピング
- **Cloud Armor**（`test-cloud-armor-security-policy`）：
  - デフォルトルール：すべて deny(403)
  - 優先度 100：`origin.region_code == 'JP'` のみ allow
- **Cloud DNS**（`example-zone` / `mystudy.com.`）：
  - A レコード：`dev.mystudy.com` → LB の外部 IP
  - CNAME レコード：証明書の DNS 検証用
- **Cloud NAT**（`cnat-test`）：
  - Cloud Router（`crouter-test`）：BGP ASN 64515
  - 外部 IP：手動割り当て（`nat-manual-ip-test`、PREMIUM ティア）
  - ポート割り当て：動的（min: 2048、max: 8192）
  - TCP タイムアウト：established 300秒、transitory 30秒
  - ロギング：ERRORS_ONLY
- **Cloud Run Job**（`test-nat-verification-job`）：
  - コンテナイメージ：`curlimages/curl`（公開イメージ、Artifact Registry 不要）
  - コマンド：`curl -s https://ifconfig.me`（外部 IP を確認）
  - VPC Access：Direct VPC egress（`ALL_TRAFFIC`）で Service と同じ Subnet を使用
  - 用途：Cloud NAT 経由のアウトバウンド通信を検証するワンショットジョブ
- **Artifact Registry**（`ar-test`）：Docker イメージリポジトリ（immutable tags 有効）。Terraform でリポジトリの作成のみ行う。イメージのビルド・プッシュは CI/CD（Cloud Build 等）で別途実施が必要。

## 接続フロー

### インバウンド（ユーザー → Cloud Run）

```
ユーザー → DNS 名前解決（dev.mystudy.com → LB IP）
        → HTTPS（443） → Global External Application Load Balancer
        → Cloud Armor（JP の IP のみ許可、それ以外 403）
        → Serverless NEG → Cloud Run（INTERNAL_ONLY）
```

### アウトバウンド（Cloud Run → 外部）

```
Cloud Run → Direct VPC egress（ALL_TRAFFIC）
         → Subnet（10.0.0.0/16）
         → Cloud NAT（固定外部 IP: nat-manual-ip-test）
         → インターネット
```

## ディレクトリ構成

```
architectures/03/
├── architecture.svg           # アーキテクチャ図
├── README.md                  # このファイル
├── README_TERRAFORM_DOCS.md   # terraform-docs 自動生成ドキュメント
├── main/                      # メインの Terraform 構成
│   ├── main.tf                # モジュールの呼び出し
│   ├── local.tf               # ローカル変数（プレフィックス、リージョン、Cloud Run スペック等）
│   └── provider.tf            # Google プロバイダ設定（hashicorp/google >= 7.33.0）
└── modules/                   # 再利用可能なモジュール
    ├── network/               # VPC、Subnet
    ├── cloud_run/             # Cloud Run サービス、IAM ポリシー、NAT 検証用 Job
    ├── load_balancer/         # LB、NEG、Backend Service、SSL Policy、Certificate Manager、Forwarding Rule
    ├── cloud_armor/           # Security Policy、ルール（JP 許可 / デフォルト拒否）
    ├── cloud_dns/             # DNS Managed Zone、A レコード、CNAME レコード
    ├── cloud_nat/             # Cloud Router、Cloud NAT、外部 IP
    └── artifact_registry/     # Docker リポジトリ
```

## 前提

- mise で必要なツール（Terraform >= 1.14.0）がインストールされていること
- Google Cloud CLI（`gcloud auth application-default login` 認証済み）がセットされていること
- `provider.tf` の `project` に使用する GCP プロジェクト ID を設定すること
- カスタムドメイン（`mystudy.com`）のネームサーバーが Cloud DNS を参照していること（証明書の DNS 検証に必要）

## 使用方法（簡易）

1. `main` ディレクトリへ移動:

```bash
cd architectures/03/main
```

2. Terraform 初期化:

```bash
terraform init
```

3. 計画確認:

```bash
terraform plan
```

4. 適用:

```bash
terraform apply
```

5. インバウンドの動作確認:

```bash
# Cloud Run の URL 確認
gcloud run services describe test-cloud-run-service --region asia-northeast1 --format 'value(status.url)'

# カスタムドメイン経由でアクセス
curl -v https://dev.mystudy.com
```

6. アウトバウンド（Cloud NAT）の動作確認:

```bash
# Cloud Run Job を実行（curl ifconfig.me で外部 IP を取得）
gcloud run jobs execute test-nat-verification-job --region asia-northeast1 --wait

# ログで Job が返した外部 IP を確認
gcloud logging read \
  'resource.type="cloud_run_job" AND resource.labels.job_name="test-nat-verification-job"' \
  --limit 10 \
  --format "value(textPayload)"

# Cloud NAT の固定 IP を確認（上のログの IP と一致すれば NAT 経由）
gcloud compute addresses describe nat-manual-ip-test \
  --region asia-northeast1 \
  --format 'value(address)'
```

## カスタマイズ

- `local.tf` の変数を変更してリソース名プレフィックス（`prefix`）、Cloud Run のスペック（`crun_cpu`、`crun_memory`）、スケーリング設定（`crun_min_instance_count`、`crun_max_instance_count`）、リクエストタイムアウト（`crun_timeout_seconds`）を調整できます。
- Cloud Armor のルール（`cloud_armor/main.tf`）を編集して、許可する国コードや IP レンジを追加・変更できます。
- Cloud NAT のポート割り当て（`min_ports_per_vm`、`max_ports_per_vm`）や TCP タイムアウトは `local.tf` で調整できます。
- `load_balancer/main.tf` の `enable_cdn` を `true` に変更すると Cloud CDN が有効になります。

## 運用上の注意

- Global External Application Load Balancer は時間課金が発生するため、学習目的の場合はテスト後に速やかに `terraform destroy` でリソースを削除してください。
- Cloud NAT の外部 IP（PREMIUM ティア）も課金対象です。
- Certificate Manager の証明書発行には DNS 検証が完了する必要があり、ネームサーバーの設定によっては時間がかかる場合があります。
- Cloud Run のコンテナイメージはサンプル（`hello`）を使用しています。独自のイメージを使用する場合は Artifact Registry にプッシュし、Cloud Run のイメージ URL を変更してください。

## 発展課題

- **Cloud Run のカスタムコンテナ**：Artifact Registry（`ar-test`）にカスタムイメージをビルド・プッシュし、Cloud Run Service のイメージを切り替える。Cloud Build や GitHub Actions で CI/CD パイプラインを構築することで、コードプッシュからデプロイまでを自動化できる。
- **Cloud Armor の高度なルール**：レートリミット、WAF ルール（OWASP Top 10）、Adaptive Protection の導入。
- **Cloud Run の VPC Service Controls**：サービス境界を設定し、データ漏洩を防止するセキュリティ強化。
- **マルチリージョン構成**：複数リージョンの Cloud Run サービスをグローバル LB で負荷分散する高可用性構成。

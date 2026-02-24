# Architecture 02 — GCP: Cloud Run + Cloud SQL

このディレクトリ（architectures/02）は、Google Cloud Platform 上でのサーバーレスコンテナ実行環境（Cloud Run）とマネージドRDB（Cloud SQL）を組み合わせた基本的なアーキテクチャを学習するための Terraform 構成を含んでいます。セキュアな接続、認証・権限設計、秘密情報管理、ネットワーク分離などの実践的パターンを学べます。

## 学習の目的

- サーバーレスアプリケーションのデプロイ：`Cloud Run` によるコンテナ化アプリのデプロイとスケーリング挙動を理解する。
- マネージドDB接続：`Cloud SQL`（Postgres/MySQL等）を Cloud Run から安全に接続する方法（Private IP / Cloud SQL Proxy / Service Account）。
- ネットワーク設計：VPC、サブネット、Serverless VPC Connector を用いたプライベート接続の構成。
- シークレットの安全管理：`Secret Manager` を用いた DB 認証情報の管理と Cloud Run での参照方法。
- サービスアカウントと最小権限：Cloud Run に割り当てるサービスアカウントと Cloud SQL への権限設計。
- Terraform モジュール化：再利用可能なモジュール（network / cloud_run / cloud_sql / secret_manager / service_account）の使い方。

## 想定するアーキテクチャ要素

- VPC とサブネット（プライベートなネットワーク境界）
- Serverless VPC Connector：Cloud Run から VPC 内 Cloud SQL へ Private IP でアクセスするためのコネクタ
- Cloud Run：コンテナ実行環境（外部公開 or internal）
- Cloud SQL：マネージドデータベース（Private IP 構成を推奨）
- Secret Manager：DB パスワード等の秘密情報を格納
- Service Account：Cloud Run に付与するアイデンティティ（最小権限）

## 接続フロー（例）

1. クライアント（外部） → HTTPS → `Cloud Run`（Ingress: external または internal）
2. `Cloud Run`（割り当てられた Service Account） → Serverless VPC Connector 経由 → `Cloud SQL`（Private IP）
3. DB 認証情報は `Secret Manager` から取得（Cloud Run の実行環境で参照）

## ディレクトリ構成（想定）

```
architectures/02/
├── main/               # メインの Terraform 構成
│   ├── main.tf         # モジュールの呼び出し
│   ├── local.tf        # ローカル変数/プレフィックス等
│   └── provider.tf     # GCP プロバイダ設定
└── modules/            # 再利用可能なモジュール
    ├── network/        # VPC, subnets, Serverless VPC Connector
    ├── cloud_run/      # Cloud Run サービス、IAM、Ingress/Autoscale 設定
    ├── cloud_sql/      # Cloud SQL インスタンス（Private IP 設定）
    ├── secret_manager/ # Secret Manager の定義
    └── service_account/# サービスアカウントと IAM ロール
```

## 前提

- Terraform >= 1.0
- gcloud CLI（認証済み）または環境変数で GCP 認証がセットされていること
- 使用する GCP プロジェクトが作成済みで次の API が有効：Cloud Run、Cloud SQL Admin、Secret Manager、Compute Engine など

## 使用方法（簡易）

1. `main` ディレクトリへ移動:

```bash
cd architectures/02/main
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

## カスタマイズ

- `local.tf` の変数を変更してリソース名プレフィックス、Region、Cloud Run の最小/最大インスタンス数、同時接続数（concurrency）などを調整できます。
- Cloud SQL の接続方式は Private IP もしくは Cloud SQL Auth Proxy（sidecar/connector）に切り替え可能です。モジュール設計に従って選択してください。

## 運用上の注意

- Cloud SQL を Public IP で公開しないこと。可能であれば Private IP を利用して VPC 内から接続する構成を推奨します。
- `Secret Manager` を使い、DB の資格情報は平文でソース管理しないでください。
- サービスアカウントは最小権限で付与し、Cloud Run に必要なロールのみを与えること（例：Cloud SQL Client ロール）。
- Cloud Run（Direct VPC Egress）+Cloud SQL(VPC Peering) + VPCの構成 terraform destroyが依存の問題で正常に動作しない
- 内部静的IPアドレスの開放はCloud Run削除時に行われるはずだがラグがありこれに依存するVPCやサブネットが削除できなくなるので待つか、手動で削除する（数分～数時間）
- Cloud SQL削除後も、VPCネットワークピアリングが残るバグがあるので手動で消す。
- テスト後は不要な課金を避けるために `terraform destroy` でリソースを削除してください。

---

必要であれば、README の内容を調整したり、具体的な `main`/`modules` のサンプルを追加します。ご希望を教えてください。

# Architecture 04: GKE Autopilot + Workload Identity

## 概要

GKE Autopilot クラスタを構築し、Workload Identity を使って Pod が Google サービスアカウント (GSA) の権限を借用できる構成です。

- GKE Autopilot（プライベートノード）
- VPC ネットワーク + セカンダリ IP レンジ（Pod・Service 用）
- Workload Identity Federation（KSA ↔ GSA のバインディング）

## アーキテクチャ

```
┌─────────────────────────────────────────────┐
│  VPC Network (test-vpc-network)              │
│                                             │
│  ┌──────────────────────────────────────┐   │
│  │  Subnetwork: test-gke-subnetwork     │   │
│  │  Primary CIDR:   10.0.0.0/24         │   │
│  │  Pod CIDR:       10.1.0.0/16         │   │
│  │  Service CIDR:   10.2.0.0/20         │   │
│  │                                      │   │
│  │  ┌────────────────────────────────┐  │   │
│  │  │ GKE Autopilot Cluster          │  │   │
│  │  │  Private Nodes: enabled        │  │   │
│  │  │  Private Endpoint: disabled    │  │   │
│  │  │  Master CIDR: 172.16.0.0/28    │  │   │
│  │  │                                │  │   │
│  │  │  Pod (KSA: app-ksa)            │  │   │
│  │  │    │ Workload Identity          │  │   │
│  │  │    ▼                           │  │   │
│  │  │  GSA: test-gke-sa              │  │   │
│  │  └────────────────────────────────┘  │   │
│  └──────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

## ポイント

### Workload Identity の仕組み

Pod が GCP リソースにアクセスする際、サービスアカウントキー（JSON）を使わずに IAM 権限を借用できる仕組みです。

```
Pod (app-ksa)
  │ iam.gke.io/gcp-service-account アノテーション
  ▼
Kubernetes Service Account (app-ksa)
  │ Workload Identity バインディング
  ▼
Google Service Account (test-gke-sa)
  │ roles/iam.workloadIdentityUser
  ▼
GCP リソースへのアクセス
```

### GKE Autopilot

- ノードの管理が不要（Google がノードプールを自動管理）
- `enable_autopilot = true` のみで有効化
- セカンダリ IP レンジが必須（Pod/Service 用に明示的に指定）

### プライベートクラスタ設定

| 設定 | 値 | 理由 |
|------|-----|------|
| `enable_private_nodes` | `true` | ノードにパブリック IP を付与しない |
| `enable_private_endpoint` | `false` | ローカルから `kubectl` でアクセス可能にする |
| `master_ipv4_cidr_block` | `172.16.0.0/28` | マスターの内部 IP レンジ |

## ディレクトリ構成

```
architectures/04/
├── main/
│   ├── main.tf        # モジュール呼び出し
│   ├── local.tf       # プロジェクト・リージョン設定
│   └── provider.tf    # Google プロバイダー設定
├── modules/
│   ├── network/       # VPC・サブネット
│   ├── gke/           # GKE Autopilot クラスタ
│   └── service_account/ # GSA + Workload Identity バインディング
└── scripts/
    ├── setup_workload_identity.sh   # Phase 2: KSA 作成・アノテーション付与
    └── verify_workload_identity.sh  # 動作確認用
```

## デプロイ手順

### Phase 1: Terraform でインフラ構築

```bash
cd architectures/04/main

terraform init
terraform plan
terraform apply
```

作成されるリソース:
- VPC ネットワーク
- サブネット（セカンダリレンジ付き）
- GKE Autopilot クラスタ
- Google Service Account
- Workload Identity バインディング（GSA 側）

### Phase 2: Kubernetes Service Account のセットアップ

`scripts/setup_workload_identity.sh` の設定値を環境に合わせて編集してから実行します。

```bash
# スクリプト内の設定値を変更
PROJECT_ID="<YOUR_PROJECT_ID>"
CLUSTER_NAME="<YOUR_PREFIX>-autopilot-cluster"

# 実行
bash scripts/setup_workload_identity.sh
```

このスクリプトは以下を実行します:
1. クラスタの認証情報を取得 (`gcloud container clusters get-credentials`)
2. Kubernetes Service Account (`app-ksa`) を作成
3. KSA に GSA のアノテーションを付与

### 動作確認

```bash
bash scripts/verify_workload_identity.sh
```

テスト Pod を起動して `gcloud auth list` を実行し、GSA のメールアドレスが表示されれば Workload Identity が正しく機能しています。

## ネットワーク構成

| リソース | 値 |
|---------|-----|
| VPC | `test-vpc-network` |
| サブネット | `test-gke-subnetwork` |
| Primary CIDR | `10.0.0.0/24` |
| Pod CIDR | `10.1.0.0/16` |
| Service CIDR | `10.2.0.0/20` |
| Master CIDR | `172.16.0.0/28` |
| リージョン | `asia-northeast1` |

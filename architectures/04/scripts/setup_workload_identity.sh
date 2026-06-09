#!/bin/bash
set -euo pipefail

#===========================================
# Phase 2: Workload Identity セットアップ
# Phase 1 (terraform apply) 完了後に実行
#===========================================

# --- 設定値（環境に合わせて変更） ---
PROJECT_ID="<YOUR_PROJECT_ID>"
CLUSTER_NAME="<YOUR_PREFIX>-autopilot-cluster"
LOCATION="asia-northeast1"
GSA_EMAIL="<YOUR_PREFIX>-gke-sa@${PROJECT_ID}.iam.gserviceaccount.com"
KSA_NAME="app-ksa"
NAMESPACE="default"

# --- Step 1: クラスタの認証情報を取得 ---
echo "=== Step 1: クラスタ認証情報を取得 ==="
gcloud container clusters get-credentials "${CLUSTER_NAME}" \
  --location "${LOCATION}" \
  --project "${PROJECT_ID}"

# --- Step 2: KSA を作成 ---
echo "=== Step 2: Kubernetes Service Account を作成 ==="
kubectl create serviceaccount "${KSA_NAME}" -n "${NAMESPACE}" \
  --dry-run=client -o yaml | kubectl apply -f -

# --- Step 3: KSA に GSA のアノテーションを付与 ---
echo "=== Step 3: Workload Identity アノテーションを付与 ==="
kubectl annotate serviceaccount "${KSA_NAME}" \
  iam.gke.io/gcp-service-account="${GSA_EMAIL}" \
  -n "${NAMESPACE}" \
  --overwrite

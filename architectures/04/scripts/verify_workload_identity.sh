#!/bin/bash
set -euo pipefail

#===========================================
# Phase 2: Workload Identity 動作確認
# setup_workload_identity.sh 実行後に使用
#===========================================

# --- 設定値（環境に合わせて変更） ---
KSA_NAME="app-ksa"
NAMESPACE="default"

# --- テスト用Podを起動して gcloud auth list を実行 ---
echo "=== Workload Identity 動作確認 ==="
echo "GSA のメールアドレスが表示されれば成功です"
echo ""

kubectl run test-pod \
  --image=google/cloud-sdk:slim \
  --overrides="{\"spec\":{\"serviceAccountName\":\"${KSA_NAME}\"}}" \
  -n "${NAMESPACE}" \
  -it --rm \
  -- gcloud auth list

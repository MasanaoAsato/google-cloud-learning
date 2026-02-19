# google-cloud-learning
googlecloudの学習
# リポジトリ構成

architectures/<アーキテクチャ番号>の下に、テーマごとのアーキテクチャ図とTerraformコードを配置する。

テーマは、それぞれのフォルダ内のREADME.mdに記載する。
svgファイルはアーキテクチャの構成図である。



# Terraform関連
## Terraformのフォーマット修正
`terraform fmt -recursive`

## tflint
`tflint --recursive --config=$(pwd)/.tflint.hcl`

## terraform docsの作成
`terraform-docs ./architectures/<番号>`

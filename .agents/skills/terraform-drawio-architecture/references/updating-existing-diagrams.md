# 既存図を更新する

## 意味を先に復元する

```bash
sh <skill-dir>/scripts/run_python.sh <skill-dir>/scripts/inspect_drawio.py <existing.drawio-or-svg> --output /tmp/existing.json
```

次を一覧にする。

- コンテナと親子関係
- ノードの表示名、Terraformアドレス、サービス種別
- 線の始点、終点、方向、ラベル、線種
- 凡例、図中の注釈、利用者独自の説明

Draw.ioから出力されたSVGで`content`属性にmxfileを含む場合は、埋め込みXMLを正本候補として復元する。埋め込みが無いSVGは視覚参照に限定する。

## Terraformと比較する

差分を次に分類する。

- `add`: Terraformにあり、図に無い重要要素
- `update`: 同じ要素だが名称、境界、接続、属性が異なる
- `remove-candidate`: 図にあるがTerraformで確認できない
- `unresolved`: module内部や外部接続など、判断できない
- `style-only`: 意味を変えない配置、色、線、ラベルの修正

`remove-candidate`を即座に削除しない。Terraform管理外の外部システムかもしれないため、図中で外部要素として根拠があるか確認し、判断を変更記録へ残す。

## 作り直しの判断

利用者の加筆がある図は、その意味を中間仕様へ移してから作り直す。`base.drawio`から組み直すと注釈が落ちる。スタイルだけの修正で足りる場合は、中間仕様の`geometry`とstyle tokenを直して再生成する方が、手作業でセルを触るより再現性がある。

## 引き継ぐスタイルの優先順位

1. 更新対象の既存draw.ioにある一貫したスタイル
2. 今回ユーザーが渡した参考画像の視覚表現
3. `references/layout-and-style.md`のプロバイダ別規則
4. `assets/style-tokens.json`の共通トークン

上位を採用しても、余白の契約、境界の直角、境界名の位置、日本語の折り返しはそろえる。

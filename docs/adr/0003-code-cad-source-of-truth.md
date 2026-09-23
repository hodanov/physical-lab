# ADR-0003: コード CAD を正本にし、FreeCAD を図面・解析に使う

- 状態: 承認
- 日付: 2026-09-23

## 背景

[ADR-0002](0002-cad-source-and-manufacturing-exports.md) では FreeCAD の `.FCStd` を
設計正本とした。しかし `.FCStd` はバイナリ（zip）で差分レビューができず、形状の妥当性を
CI で自動検証しにくい。FreeCAD の Python は同梱版で、uv による依存管理の外にあり、
CI で動かすには AppImage などの重いセットアップが要る。

一方で、将来は機械設計へ広げる予定があり、寸法入り図面、アセンブリ確認、FEM などの
後工程は必要になる。

## 決定

形状の正本を Python のコード CAD にし、FreeCAD は図面・解析の後工程に使う。

- モデリングには build123d（OpenCASCADE ベース）を使う。プロダクトのパラメータと
  モデリングスクリプトを `cad/source/` に置き、これを設計正本とする。
- Python の依存はルートの `pyproject.toml` と `uv.lock` で uv により管理する。
  Python は 3.14 に固定する。
- ビルドスクリプトで STEP（中立形式の製造マスター）、STL（3Dプリント用）、確認用
  SVG、検査レポートを `cad/export/` に生成する。生成物はコミットせず、CI の
  artifact として取得する。
- 発注時は、発注に使う生成物を `manufacturing/<service>/<rev>/` にコピーしてコミットし、
  製造した形状を固定する。
- FreeCAD は STEP を取り込み、TechDraw による寸法入り図面、アセンブリ確認、FEM に
  使う。図面の元データ（`.FCStd`）は `drawings/` に置き、発注や図面確認の節目で更新する。
- CI では format、lint、型チェック、テスト、形状ビルドを実行する。
- 単位はミリメートルのままとする。

## 検討した選択肢

- FreeCAD 一本（スクリプトで `.FCStd` を生成）: 図面、アセンブリ、FEM まで 1 つの
  ツールで完結する。ただし API が冗長で型が効かず、uv の外で動くため CI も重い。
- CadQuery + FreeCAD: 役割分担は本決定と同じ。実績は多いが、メソッドチェーン中心の
  API は型チェックとの相性が build123d より弱い。
- コード CAD 一本（FreeCAD なし）: 構成は最も単純。ただし寸法入り図面、アセンブリ、
  FEM がなく、将来の機械設計に向かない。
- build123d + FreeCAD: 正本をコードにして差分レビューと CI 検証を得つつ、FreeCAD の
  後工程を残せる。両者とも OpenCASCADE ベースなので STEP で劣化なく受け渡せる。

## 影響

- ADR-0002 の「`.FCStd` を正本とする」を置き換える。STEP と STL を `cad/export/` に
  生成し、手で編集しない点は引き継ぐ。
- FreeCAD に取り込んだ STEP はパラメトリックではない。形状を変えると TechDraw の寸法の
  参照が外れることがあるため、図面は節目で更新し、毎回の CI には含めない。
- 開発中の形状確認には ocp_cad_viewer（VS Code）や FreeCAD で STEP を開く方法を使う。
- ルートとプロダクトの `AGENTS.md`、README を本決定に合わせて更新する。

## 関連資料

- [ADR-0002: CAD 正本と製造用エクスポート](0002-cad-source-and-manufacturing-exports.md)
- [リポジトリルール](../../AGENTS.md)
- [TSUGU Split 65 の設計制約](../../products/keyboard/tsugu-65/AGENTS.md)
- [build123d](https://github.com/gumyr/build123d)

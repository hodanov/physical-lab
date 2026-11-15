# 図面

TSUGU Split 65 の寸法入り図面は、FreeCAD の TechDraw でスクリプトから生成する
（[ADR-0004](../../../../docs/adr/0004-scripted-techdraw-drawings.md)）。
形状を変えたら再生成するだけで、寸法が付き直る。

- `make_drawings.py`: FreeCAD 内で動く描画スクリプト。直接は実行せず、
  `tsugu65-drawings` から起動する
- `tsugu65-<half>.pdf`: レビューや発注の節目で書き出した図面（節目にだけ置く）

生成した `.FCStd` は `cad/export/` に出力され、コミットしない。

## 前提

- FreeCAD 1.1 以上
- `freecadcmd` は次の順で探す。見つからないときは環境変数 `FREECADCMD` に
  パスを設定する
  1. 環境変数 `FREECADCMD`
  2. `PATH` 上の `freecadcmd`
  3. macOS の `/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd`

## 生成

リポジトリのルートで実行する。

```sh
uv run tsugu65-build      # STEP と図面仕様（tsugu65-<half>-drawing.json）を出力
uv run tsugu65-drawings   # cad/export/tsugu65-<half>-drawing.FCStd を生成
```

`tsugu65-drawings` は、寸法ごとに測定値と期待値を表示する。どれか1つでも
期待値から 0.001 mm を超えてずれたり、寸法を付ける頂点が図面上に見つからなかったり
すると、エラーで終了し、その図面は保存しない。

## 図面の内容

左右それぞれ A3 横 1 枚、縮尺 1:1、第三角法。

| ビュー                 | 寸法                                                           |
| ---------------------- | -------------------------------------------------------------- |
| 上面図                 | 全幅、全奥行き、キーピッチ（ホーム行の隣り合う 1u キーの開口） |
| 正面図                 | なし                                                           |
| 外側面図               | 全高、前端の高さ                                               |
| 外側面図（左半分のみ） | USB-C 開口の幅、高さ、後端からの位置、底面からの位置           |

寸法の端点と期待値は `cad/source/tsugu65/drawing.py` の図面仕様で決まる。
図面に寸法を足したり変えたりするときは、`drawing.py` と
`cad/source/tests/test_drawing.py` を変更する。`make_drawings.py` は描画と照合だけを
担当するので、通常は変更しない。

## 節目の PDF

レビューや発注の節目では、PDF を書き出してコミットする。

1. `uv run tsugu65-build && uv run tsugu65-drawings` で図面を最新にする
2. FreeCAD で `cad/export/tsugu65-left-drawing.FCStd` を開く
   （例: `open -a FreeCAD products/keyboard/tsugu-65/cad/export/tsugu65-left-drawing.FCStd`）
3. ツリーの `Page` を開き、TechDraw の「Export Page as PDF」で
   `drawings/tsugu65-left.pdf` に書き出す
4. 右半分も同様に `drawings/tsugu65-right.pdf` に書き出す
5. 発注に使う場合は、PDF を他の生成物と一緒に `manufacturing/<service>/<rev>/` にも
   コピーする

GUI で寸法の位置などを手直ししても、再生成すると元に戻る。手直しを残したいときは、
その内容を `make_drawings.py` の配置ロジックに反映する。

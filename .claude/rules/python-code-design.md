---
paths:
  - "**/*.py"
---

# 変更容易性・可読性の設計原則（Python）

コードを書く・直すときは、変更容易性と可読性を予防的に確保する。

## 核となる原則

関連する状態と規則は所有者に凝集させ、宣言は最も狭いスコープに置き、事実は一度だけ書く。
ただし、現在の要件にない抽象は足さない。

既存の言語仕様、リポジトリ固有ルール、外部との契約を優先する。
原則を満たすためだけに、変更対象外のコードまでリファクタリングしない。

## 凝集

- データの不変条件や検証は、そのデータを所有する型へ寄せる。値オブジェクトは
  `@dataclass(frozen=True, slots=True)` にし、検証は `__post_init__` に置く。
- 派生値は、所有する型のメソッドやプロパティにする（例: `Params.keycap_size`）。
- 手続きを1つの関数へ並べず、状態と規則を同じ場所へ置く。
- 状態に依存しない処理は、無理にメソッド化せずモジュール関数のままにする。
- 具象型へのメソッド追加と、差し替えのための `Protocol` や ABC の追加は別々に判断する。

## スコープ最小化

- 一箇所でしか使わない宣言は、言語仕様と所有する振る舞いが許す範囲で利用箇所のローカルに置く。
- 宣言位置から、その値や規則が影響する範囲を読み取れるようにする。
- 再利用が発生してから、必要な最小範囲へ引き上げる。
- 1つの関数でしか使わない定数は、その関数のローカルに置く。
- 複数の関数、デフォルト引数、クラス定義から参照する値は、`_` 始まりのモジュール非公開名にする。
- 他モジュールやテストから import される名前だけを公開名にする。
- 名前付き関数とクラスは、クロージャが必要な場合を除き、ネストせずモジュールスコープに置く。

避ける:

```python
BASE_DELAY_S = 0.1


def retry_delay_s(attempt: int) -> float:
    return attempt * BASE_DELAY_S
```

推奨:

```python
def retry_delay_s(attempt: int) -> float:
    base_delay_s = 0.1
    return attempt * base_delay_s
```

## コード内の単一の情報源

- 同時に変更される同一の事実を複数箇所へ直接書かない。
- 許容値、表示文言、派生値が同じ事実を表すなら、1つの定義から導出する。
- 定義を追加・変更したとき、別の記述だけが取り残される構造を避ける。
- 偶然同じ値になっているだけで変更理由が異なるものは、無理に共有しない。

避ける:

```python
def validate_format(fmt: str) -> None:
    allowed_formats = ("json", "text")
    if fmt not in allowed_formats:
        raise ValueError("format must be one of json, text")
```

推奨:

```python
def validate_format(fmt: str) -> None:
    allowed_formats = ("json", "text")
    if fmt not in allowed_formats:
        raise ValueError(f"format must be one of {', '.join(allowed_formats)}")
```

## YAGNI

- 現在の要件にない差し替え可能性のために `Protocol`、ABC、間接化を追加しない。
- テストだけを理由に本番コードへ抽象、依存注入の引数、公開アクセサを追加しない。
  pytest の `monkeypatch` や `tmp_path` で足りるならそれを使う。
- 具象型や小さな関数で十分なら、その形を維持する。
- 将来必要になった時点で、実際の変更軸に沿って抽象化する。
- 複数実装、既存のアーキテクチャ境界、明示された変更軸がある場合は、その要件に必要な最小範囲で抽象化する。

避ける:

```python
class LabelFormatter(Protocol):
    def format(self, value: str) -> str: ...


class StripLabelFormatter:
    def format(self, value: str) -> str:
        return value.strip()
```

推奨:

```python
def format_label(value: str) -> str:
    return value.strip()
```

## 命名

- 関数・メソッド名は、対象の何を調べるか、または何を変えるかが分かる名前にする。
- `process`、`handle`、`validate` のような広い動詞を使う場合も、対象や保証を名前から特定できるようにする。
- 名前を具体化できない場合は、複数の責務を抱えていないか見直す。
- 名前は呼び出し側が依存できる契約を表し、変更可能な実装手段を漏らさない。
- 単位が既定のミリメートル以外なら、`tilt_deg` のように名前へ単位を含める。

避ける:

```python
def process(lines: Sequence[str]) -> str:
    return "\n".join(lines)
```

推奨:

```python
def render_summary(lines: Sequence[str]) -> str:
    return "\n".join(lines)
```

## 引数列の凝集

- 複数の引数が常に一緒に渡され、呼び出し側ですでに1つの概念として扱われるなら、
  frozen dataclass にまとめる。
- その値に固有の規則は、その dataclass のメソッドや `__post_init__` へ寄せる。
- 呼び出しが一度しかない偶然の引数集合や、単一のプリミティブを意味の薄い型で包むだけの変更は避ける。

避ける:

```python
def validate_bounds(start: float, end: float) -> None:
    if start > end:
        raise ValueError("start must not exceed end")
```

推奨:

```python
@dataclass(frozen=True, slots=True)
class Range:
    start: float
    end: float

    def __post_init__(self) -> None:
        if self.start > self.end:
            raise ValueError("start must not exceed end")
```

## クエリとコマンド

- 値を返すクエリは、返すものや保証する事後条件が伝わる名前にする。
- 状態を変えるコマンドは、命令形の動詞と対象を名前に含める。
- `fetch` や `refresh` は、毎回取得・更新すること自体が呼び出し側の依存する契約である場合だけ使う。
- `functools.cache`、`cached_property`、遅延初期化、リトライなどが実装詳細なら、名前へ露出させない。
- 有効な値を保証し、必要な場合だけ処理する操作には、実装手段ではなく事後条件を表す名前を使う。

次の名前は、異なる契約を表す。例示の `Protocol` は抽象化の追加を求めるものではない。

```python
class SnapshotStore(Protocol):
    def ensure_snapshot(self) -> Snapshot: ...

    def invalidate_snapshot(self) -> None: ...


class SnapshotGateway(Protocol):
    def fetch_snapshot(self) -> Snapshot: ...
```

`ensure_snapshot` は取得方法を規定せず有効な値を返す。`fetch_snapshot` は呼び出しごとの外部取得を契約に含む。

## 判断チェック

1. 状態と規則を同じ所有者（dataclass とその `__post_init__`・メソッド）へ置けないか。
2. 言語仕様と所有する振る舞いを保ったまま、宣言をさらに狭いスコープ（関数ローカル、
   モジュール非公開）へ閉じられないか。
3. 同時に変更される同じ事実を、別の定義から導出できないか。
4. `Protocol` や ABC を必要とする現在の要件または既存のアーキテクチャ境界があるか。
5. 名前だけで対象と操作する性質が分かるか。
6. 引数列は常に一緒に扱われ、固有の規則を持つ1つの値か。
7. 名前は呼び出し側が依存する契約か、変更可能な実装手段か。
8. 適用する原則が、既存の言語・リポジトリルールや外部契約と衝突しないか。

# HCim 自動化: 「工場」に `K` を入れてから検索する変更

以下の変更で、検索実行前に「工場」欄へ `K` を入力します。  
このファイルはそのままコピーして使える **Markdown (.md)** です。

---

## 追加関数

```python
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException

def set_factory_code(driver, wait, code: str = "K"):
    """
    ラベル『工場』に紐づく左側(コード)のテキストボックスへ code を入力して確定させる。

    ・tableレイアウト(<th>/<td>)、ラベル(<label>)、div行構造の3パターンに対応
    ・入力後に input/change/blur を発火 & TAB で確定
    """
    xpath = (
        "//th[normalize-space()='工場']/following-sibling::td[1]//input[not(@type='hidden')][1]"
        " | //td[normalize-space()='工場']/following-sibling::td[1]//input[not(@type='hidden')][1]"
        " | //label[normalize-space()='工場']/following::input[1]"
        " | //div[contains(@class,'imui-form-row')][.//span[normalize-space()='工場']]//input[not(@type='hidden')][1]"
    )

    try:
        el = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
    except TimeoutException:
        raise TimeoutException("『工場』の入力欄が見つかりませんでした。セレクタを見直してください。")

    # クリックしてから値を入れる（onfocus系のフック対策）
    try:
        el.click()
    except Exception:
        driver.execute_script("arguments[0].click();", el)

    # 値をセット
    try:
        el.clear()
    except Exception:
        pass

    el.send_keys(code)
    # 画面側のイベントを確実に起こす
    driver.execute_script("""
        arguments[0].dispatchEvent(new Event('input', {bubbles:true}));
        arguments[0].dispatchEvent(new Event('change', {bubbles:true}));
        arguments[0].dispatchEvent(new Event('blur', {bubbles:true}));
    """, el)
    # オートコンプリート等の確定用
    el.send_keys(Keys.TAB)
```

## 呼び出し位置（`main()` 内）

`set_date_range(...)` と `click_search(...)` の間に **1行** 追加してください。

```python
# 起票日
set_date_range(driver, wait, START, END)

# ★ 工場コードを「K」にする
set_factory_code(driver, wait, "K")  # ← これを追加

# 検索
click_search(wait)
```

---

## 既存の不要関数の整理（任意）

もし `K_in()` が残っていれば、`click_csv()` と重複しているため削除して構いません。

---

## トラブルシュート

- 入力欄が2つ（左:コード／右:名称）の場合は **左側** が対象です。  
  上記XPATHは左側の最初の`input`を優先して取ります。
- もし見つからない場合は、該当画面のHTMLを保存し、`th/td` の構造か、`label`／`div`の構造かを確認して、
  `xpath` の候補を1つ追加してください（例：`//span[text()='工場']...` など）。
- 値が反映されない時は、`send_keys(Keys.TAB)` を `Keys.ENTER` に換えると確定するケースがあります。

---

## 完成イメージ（抜粋）

```python
def main():
    driver = build_driver()
    wait = WebDriverWait(driver, TIMEOUT)
    try:
        driver.get(URL)
        go_to_parts_search_list(driver, wait)
        in_frame = switch_into_content_frame(driver, wait)

        click_clear(wait)
        select_doc_type(driver, wait, label="返品管理票", value="5")

        check_all_status(driver, wait)

        # 日付範囲
        set_date_range(driver, wait, START, END)

        # 工場 = K を入力
        set_factory_code(driver, wait, "K")  # ★ 追加

        # 検索
        click_search(wait)

        # 以降 CSV 出力...
        click_csv(wait)
        confirm_csv_ok(driver, wait)
        csv_path = wait_for_download(DOWNLOAD_DIR, expected_ext=".csv", rename_to=csv_name)
        print(f"[+] CSV保存: {csv_path}")
    finally:
        pass
```

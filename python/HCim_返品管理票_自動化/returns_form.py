"""
returns_form.py
=================

This module contains a collection of functions used to automate the export of
*返品管理票* CSV reports from the HCim portal. It uses Selenium to drive a
browser through a series of UI interactions:

1. Navigate through the portal’s menu to reach the 部品品記検索一覧 page.
2. Select the 文書種別 as 返品管理票.
3. Turn on all status checkboxes.
4. Set the 起票日 date range.
5. Click the 検索 button to fetch the results.
6. Click the CSV button and confirm the export.
7. Wait for the CSV file to download to a specified directory and optionally
   rename it.

The script can be run as a standalone program by invoking the ``main``
function, which performs the entire flow with configurable start and end dates
and an optional headless browser mode.

Dependencies
------------

* ``selenium`` 4.6+ with Chrome support (Selenium Manager will download
  an appropriate ChromeDriver).
* ``pandas`` (only used for DataFrame conversion if you decide to call
  ``scrape_table``, but not strictly required for export).

Usage
-----

You can run the script directly from the command line to export a CSV for a
given date range. Adjust ``START`` and ``END`` constants or modify the
``main`` call.

```
python returns_form.py
```

This will open Chrome, perform the steps described above, and save a CSV file
in the ``DOWNLOAD_DIR`` directory. If headless mode is desired, change the
``HEADLESS`` constant to ``True``. Note that when running headless Chrome,
the download directory must be explicitly set via the Chrome DevTools
protocol. This is handled automatically in ``build_driver``.

"""

import time
from pathlib import Path
from datetime import date

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# ----------------------- Configuration -----------------------
# URL of the HCim portal start page. You must be logged in before running
# this script, as it assumes an authenticated session.
URL = "https://fftpim-s.fujifilm.co.jp/imart/samlsso/home"

# Date range for 起票日 (start and end). Adjust these as needed. Format: YYYY/MM/DD
START = "2025/10/01"  # 起票日の開始日
END = "2025/10/06"    # 起票日の終了日

# Whether to run the browser in headless mode. Set to True to hide the
# browser window. Note: file downloads are still supported via DevTools.
HEADLESS = False

# Timeouts and window size for WebDriver waits.
TIMEOUT = 20
WINDOW_SIZE = "1400,1000"

# Directory where CSV files will be downloaded. The directory is created
# relative to this script if it does not already exist.
DOWNLOAD_DIR = Path(__file__).resolve().parent / "output"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ----------------------- Selenium Utility Functions -----------------------

def build_driver(*, headless: bool) -> webdriver.Chrome:
    """
    Create and configure a Chrome WebDriver instance. The download directory
    is set via Chrome preferences, and when running headless the DevTools
    protocol is used to explicitly set the download path.

    :param headless: Whether to run Chrome in headless mode.
    :return: Configured WebDriver instance.
    """
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument(f"--window-size={WINDOW_SIZE}")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-popup-blocking")

    prefs = {
        "download.default_directory": str(DOWNLOAD_DIR.resolve()),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        # Ensures that PDFs, if any, are downloaded rather than opened in the browser.
        "plugins.always_open_pdf_externally": True,
    }
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=options)
    # When headless, the download path must be explicitly set via CDP.
    if headless:
        try:
            driver.execute_cdp_cmd("Page.setDownloadBehavior", {
                "behavior": "allow",
                "downloadPath": str(DOWNLOAD_DIR.resolve())
            })
        except Exception:
            # Fallback for older versions of Chrome.
            driver.execute_cdp_cmd("Browser.setDownloadBehavior", {
                "behavior": "allow",
                "downloadPath": str(DOWNLOAD_DIR.resolve())
            })
    return driver


def go_to_parts_search_list(driver: webdriver.Chrome, wait: WebDriverWait) -> None:
    """
    Navigate through the HCim portal menu to the 部品品記検索一覧 page. This
    involves hovering over several menu items and clicking the final entry.
    """
    driver.switch_to.default_content()
    actions = ActionChains(driver)

    # Hover over the top-level "ワークフロー" menu.
    wf = wait.until(EC.visibility_of_element_located(
        (By.XPATH, "//*[self::a or self::span][normalize-space(.)='ワークフロー']")
    ))
    actions.move_to_element(wf).pause(0.25).perform()

    # Hover over "不具合情報システム" submenu.
    ng = wait.until(EC.visibility_of_element_located(
        (By.XPATH, "//*[self::a or self::span][normalize-space(.)='不具合情報システム']")
    ))
    actions.move_to_element(ng).pause(0.25).perform()

    # Hover over "部品品記" submenu.
    parts = wait.until(EC.visibility_of_element_located(
        (By.XPATH, "//*[self::a or self::span][normalize-space(.)='部品品記']")
    ))
    actions.move_to_element(parts).pause(0.25).perform()

    # Click "部品品記検索一覧".
    target = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//*[self::a or self::span][normalize-space(.)='部品品記検索一覧']")
    ))
    try:
        actions.move_to_element(target).pause(0.1).click().perform()
    except Exception:
        driver.execute_script("arguments[0].click();", target)

    # If a new window opens (e.g., new tab), switch to it.
    time.sleep(0.3)
    if len(driver.window_handles) > 1:
        driver.switch_to.window(driver.window_handles[-1])


def switch_into_content_frame(driver: webdriver.Chrome, wait: WebDriverWait) -> bool:
    """
    Iterate through all iframes to find one containing the keywords "起票日" or
    "返品管理表". Switch into it if found. Returns True if a frame was found and
    switched into, otherwise returns False.
    """
    driver.switch_to.default_content()
    frames = driver.find_elements(By.TAG_NAME, "iframe")
    for f in frames:
        driver.switch_to.default_content()
        driver.switch_to.frame(f)
        try:
            wait.until(EC.presence_of_element_located(
                (By.XPATH, "//*[contains(normalize-space(.),'起票日') or contains(normalize-space(.),'返品管理表')]")
            ))
            return True
        except TimeoutException:
            continue
    driver.switch_to.default_content()
    return False


def click_clear(wait: WebDriverWait) -> None:
    """Click the 'クリア' button to reset the form."""
    btn = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//input[@type='button' and @value='クリア'] | //button[normalize-space()='クリア']")
    ))
    btn.click()


def select_doc_type(driver: webdriver.Chrome, wait: WebDriverWait, label: str = "返品管理票", value: str = "5") -> None:
    """
    Select the document type for the search form. The HCim portal uses a custom
    select component where the visible text input and underlying hidden
    elements must be updated. This function sets the value of the hidden
    select (`doc_type`), the display text, and the hidden `escape_doc_type`.

    :param driver: The WebDriver instance.
    :param wait: WebDriverWait for waiting on elements.
    :param label: The visible label to display (e.g., "返品管理票").
    :param value: The value attribute corresponding to the label ("5" for 返品管理票).
    """
    container = wait.until(EC.presence_of_element_located((By.ID, "doc_type")))
    sel = container.find_element(By.NAME, "doc_type")      # hidden <select>
    txt = container.find_element(By.CSS_SELECTOR, "input.imfr_select_text")  # visible textbox
    esc = driver.find_element(By.NAME, "escape_doc_type")  # hidden input used on submit

    # Update the hidden select and dispatch change event.
    driver.execute_script(
        "arguments[0].value=arguments[1]; arguments[0].dispatchEvent(new Event('change',{bubbles:true}));",
        sel, value
    )
    # Update the visible text box and dispatch input/change.
    driver.execute_script(
        "arguments[0].value=arguments[1];"
        "arguments[0].dispatchEvent(new Event('input',{bubbles:true}));"
        "arguments[0].dispatchEvent(new Event('change',{bubbles:true}));",
        txt, label
    )
    # Update the hidden escape field.
    driver.execute_script("arguments[0].value=arguments[1];", esc, value)
    # Wait until the underlying select reflects the new value.
    wait.until(lambda d: sel.get_attribute("value") == value)


def check_all_status(driver: webdriver.Chrome, wait: WebDriverWait) -> None:
    """Check all status checkboxes: 承認中 (2), 差戻 (6), 引戻 (7), 取止 (8), 完了 (9)."""
    for v in ("2", "6", "7", "8", "9"):
        cb = wait.until(EC.presence_of_element_located(
            (By.XPATH, f"//input[@type='checkbox' and @name='item_status' and @value='{v}']")
        ))
        if not cb.is_selected():
            driver.execute_script("arguments[0].click();", cb)


def set_date_range(driver: webdriver.Chrome, wait: WebDriverWait, start_text: str, end_text: str) -> None:
    """
    Set the 起票日 range by writing values into the two date fields and
    dispatching input and change events. These fields are not normal HTML
    `<input type="date">` elements but custom text inputs with attached
    calendar pickers.
    """
    start_input = wait.until(EC.presence_of_element_located((By.ID, "apply_dt_from_display")))
    end_input = wait.until(EC.presence_of_element_located((By.ID, "apply_dt_to_display")))
    for el, value in ((start_input, start_text), (end_input, end_text)):
        driver.execute_script("arguments[0].value='';", el)
        driver.execute_script(
            "arguments[0].value = arguments[1];"
            "arguments[0].dispatchEvent(new Event('input',{bubbles:true}));"
            "arguments[0].dispatchEvent(new Event('change',{bubbles:true}));",
            el, value
        )
        time.sleep(0.05)


def click_search(wait: WebDriverWait) -> None:
    """Click the '検索' button to perform the search."""
    btn = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//input[@type='button' and @value='検索'] | //button[normalize-space()='検索']")
    ))
    btn.click()


def click_csv(wait: WebDriverWait) -> None:
    """
    Click the 'CSV' export button. HCim exposes this as an input, button or link.
    The typical export is bound to a form submission which triggers a confirmation
    dialog.
    """
    btn = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//input[@type='button' and @value='CSV']"
                   " | //button[normalize-space()='CSV']"
                   " | //a[normalize-space()='CSV']")
    ))
    try:
        btn.click()
    except Exception:
        wait._driver.execute_script("arguments[0].click();", btn)


def confirm_csv_ok(driver: webdriver.Chrome, wait: WebDriverWait) -> None:
    """
    Handle the CSV export confirmation dialog by clicking OK. The dialog may
    appear as a native alert or as a jQuery UI modal overlay. This function
    attempts both.
    """
    # First try native alerts
    try:
        driver.switch_to.alert.accept()
        return
    except Exception:
        pass

    # Then handle page-based modals.
    wait.until(EC.visibility_of_any_elements_located(
        (By.CSS_SELECTOR, ".ui-widget-overlay, .imui-widget-overlay")
    ))
    ok_xpath = (
        "//div[contains(@class,'ui-dialog') and not(contains(@style,'display: none'))]"
        "//button[.//span[normalize-space()='OK'] or normalize-space()='OK']"
        " | //div[contains(@class,'ui-dialog') and not(contains(@style,'display: none'))]"
        "//a[contains(@class,'ui-button') and normalize-space()='OK']"
        " | //div[contains(@class,'imui-dialog') and contains(@style,'display')]"
        "//button[normalize-space()='OK']"
    )
    ok_btn = wait.until(EC.element_to_be_clickable((By.XPATH, ok_xpath)))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", ok_btn)
    driver.execute_script("arguments[0].click();", ok_btn)
    try:
        wait.until(EC.invisibility_of_element(ok_btn))
    except Exception:
        pass


def wait_for_download(dirpath: Path, *, expected_ext: str = ".csv", rename_to: str | None = None, timeout: int = 90) -> Path:
    """
    Wait for a new file to appear in ``dirpath`` and return its Path object. If
    ``rename_to`` is provided, the file will be renamed to that name after
    download completes. The function monitors the directory for new files and
    ensures that any ``.crdownload`` temporary files (Chrome's partial
    downloads) have been finalized before returning.
    """
    start = time.time()
    before = {p.name for p in dirpath.glob("*")}
    target: Optional[Path] = None
    while time.time() - start < timeout:
        now = list(dirpath.glob("*"))
        added = [p for p in now if p.name not in before]
        if added:
            for p in sorted(added, key=lambda x: x.stat().st_mtime, reverse=True):
                cr = Path(str(p) + ".crdownload")
                if cr.exists():  # still downloading
                    break
                if expected_ext is None or p.suffix.lower() == expected_ext:
                    target = p
                    break
        if target:
            break
        time.sleep(0.3)
    if target is None:
        raise TimeoutException("CSVのダウンロードが確認できませんでした")
    if rename_to:
        dest = target.with_name(rename_to)
        try:
            target.rename(dest)
            target = dest
        except Exception:
            pass
    return target


def run_automation(start_date: str, end_date: str, output_name: str, *, headless: bool = False) -> Path:
    """
    Execute the end-to-end export process and return the path to the downloaded
    CSV file. The caller must ensure that an authenticated session exists
    (e.g., by logging in to the portal before running this script).

    :param start_date: 起票日の開始日 in format YYYY/MM/DD.
    :param end_date: 起票日の終了日 in format YYYY/MM/DD.
    :param output_name: Filename to rename the downloaded CSV to.
    :param headless: Run Chrome headlessly.
    :return: Path to the downloaded CSV file.
    """
    driver = build_driver(headless=headless)
    wait = WebDriverWait(driver, TIMEOUT)
    try:
        driver.get(URL)
        go_to_parts_search_list(driver, wait)
        switch_into_content_frame(driver, wait)
        click_clear(wait)
        select_doc_type(driver, wait, label="返品管理票", value="5")
        check_all_status(driver, wait)
        set_date_range(driver, wait, start_date, end_date)
        click_search(wait)
        click_csv(wait)
        confirm_csv_ok(driver, wait)
        csv_path = wait_for_download(DOWNLOAD_DIR, expected_ext=".csv", rename_to=output_name)
        return csv_path
    finally:
        driver.quit()


def main() -> None:
    """
    When executed as a script, run the automation for the configured ``START``
    and ``END`` dates and print the resulting CSV path.
    """
    output_name = f"imart_返品管理表_{START.replace('/', '-')}_{END.replace('/', '-')}.csv"
    csv_file = run_automation(START, END, output_name, headless=HEADLESS)
    print(f"CSV saved to: {csv_file}")


if __name__ == "__main__":
    main()

# WSA

> 人中会犯错，特别是在重复性高、容错度低的网页配置环境下，好消息是机器不会。

[使用手册: Notion](https://www.notion.so/pacdora/Web-Setup-Automation-229c0ce4640c80e69bd2fd3ffc42c3c9?v=1a6c0ce4640c80708250000cde9dce24&source=copy_link) 

[代码Docs: DeepWiki](https://deepwiki.org/xolarvill/web_setup_automation)

WSA is a cross-platform desktop application built with PySide6 designed to streamline the process of generating web setup configurations. It automates the extraction of key information from text and facilitates the creation of JSON output for various web page types, helping users efficiently prepare content for web deployment.

## Features

* **Cross-Platform Compatibility:** Built with PySide6 and keyring to ensure smooth operation on Windows and macOS.
* **Automated Data Extraction:** Parses copied text from sources like Google Docs to automatically populate fields for URL, Title, Meta Description, Keywords, and more.
* **Intuitive User Interface:** A clear and organized interface with input fields, output display, and action buttons.
* **Folder Management:** Easily browse and open local or network folders for managing associated assets (e.g., images).
* **JSON Generation:** Compiles all collected data into a well-formatted JSON output, ready for use in web setup processes.
* **Clipboard Integration:** Seamlessly copies extracted data and generated JSON to the clipboard for quick pasting.
* **Real-time Feedback:** Provides informative messages and status updates in the output console.
* **DrissionPage-based Automation:** This is the real kicker.

Todos:
- [x] splash screen
- [x] better ui scaling for much information
- [x] cross-platform AWS secret management
- [x] support all formats of json file
  - [x] mockup tool
  - [x] landing page
  - [x] resource
  - [x] universal topic
  - [x] tools
  - [ ] ~~dieline SERIES~~ (Well they don't want it. What can i say, man)
- [x] clean and neat distribution
- [x] furthur automated setup

## For Developers

### Set Up
First make sure `uv` is installed, if not:

On windows
```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/0.7.11/install.ps1 | iex"
```

On mac you can use homebrew
```bash
brew install uv
```

Set up the venv by
```bash
cd /web_setup_automation
uv sync
```

You can set up your AWS S3 configure by running the following. Or you can use the other two methods in the instruction manual.
```bash
aws configure
```

Run the app by
```bash
uv run main_launcher.py
```

This will open a splash screen, displaying loading information and possible errors.

Automated packaging can be used by `build_automation.py`. Run this file and input the version number, a usable distribution will be stored in the `/dist` folder.

### Some Notes

#### Resource and Templates

All json templates are stored in `/json_templates`. Other image files and miscellaneous files are stored in `/resources`, including the icon files.

#### Credentials Management

The application uses a hierarchical approach to manage AWS credentials, ensuring both security and flexibility. The order of precedence is as follows:

1.  **Keyring (Recommended):** The primary and most secure method. Credentials are saved via the in-app "AWS Configure" UI and stored in the operating system's native credential manager (e.g., macOS Keychain, Windows Credential Manager) using the `keyring` library. This avoids storing sensitive information in plaintext files.
2.  **AWS CLI (`~/.aws/credentials`):** If no credentials are found in Keyring, the application's underlying libraries (like `boto3`) will automatically look for credentials configured via the standard `aws configure` command. This is a good fallback for developers who already use the AWS CLI.
3.  **`aws_config.json` (Legacy Fallback):** As a final resort, the application will check for a local `aws_config.json` file in the root directory. This method is considered legacy and is less secure. It should only be used if the above methods are not feasible.
4.  When opening the app, a S3Uploader will be instantiated and automatically detect AWS configure information.
#### Threading

A highly recommended way to run task in the app without UI stagger is to use thread task.
```python
def worker():
  pass # write your task code here

# use lazy import to reduce the start time of app
from threading import Thread
  thread = Thread(target=worker, daemon=True)
  thread.start()
```

#### UI Widgets

The `CollapsibleBox` is a reusable widget that can be used to create collapsible sections in the UI.

```python
# Create a collapsible box with a title
collapsible_box = CollapsibleBox("My Collapsible Box")

# Create a layout for the content of the box
content_layout = QVBoxLayout()
content_layout.addWidget(QLabel("This is the content of the box."))
content_layout.addWidget(QPushButton("A button"))

# Set the content layout for the box
collapsible_box.setContentLayout(content_layout)

# Add the collapsible box to your main layout
main_layout.addWidget(collapsible_box)
```

The `HorizontalCollapsibleTab` is a horizontal foldable panel switch base on the design of `CollapsibleBox`.

```python
# ... (in your main window setup)
tabs = HorizontalCollapsibleTabs()

# Tab 1
content1 = QWidget()
layout1 = QVBoxLayout(content1)
layout1.addWidget(QLabel("This is the content for Tab 1"))
tabs.add_tab("Tab 1", content1)

# Tab 2
content2 = QWidget()
layout2 = QVBoxLayout(content2)
layout2.addWidget(QLabel("This is the content for Tab 2"))
tabs.add_tab("Tab 2", content2)

# Add the tabs widget to your main layout
main_layout.addWidget(tabs)
```

The `LabeledLineEditWithCopy` is the main widgets in the app. It is simpel and intuitive. 

#### Browser Automating Task

This program runs browser task by `DrissionPage`, which could be relatively novel to some developers. You can visit the offical docs [here](https://drissionpage.cn/browser_control/intro).

`dp_bot_manager.py` provides a factory of modular bot `ModularBatchBot`, where you can furthur assemble and customize.

### Other Notes

- `dp_bot.py` is a primitive DP-based browser automation file. This is a legacy file.
- `upload_selenium_class.py` uses Selenium to automate login and bulk image uploads. It stores login information using cookies, requiring a manual login only on the first use. This is a legacy file.
- `size.csv` has to be manually updated, which means a developer has to do it once a request. I didn't update this feature simply because of low ROI.

## Acknowledgement

- Shout out to mirtle@pacdora.com for the original idea and some snippets.
- For support, contact me at xolarvill@gmail.com or bayuejiake@163.com.
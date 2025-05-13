
# 📌 Setup Instructions for Pre-commit, Black, and Ruff

This guide will walk you through setting up:
- `pre-commit`: For managing Git hooks
- `black`: Python code formatter
- `ruff`: Fast Python linter and import sorter

---

## ✅ **1️⃣ Create a Virtual Environment**

From the root of your project, create a virtual environment:

```bash
python3.12 -m venv .venv --upgrade-deps --with-pip
```

Activate the environment:

- On **Linux/macOS**:
    ```bash
    source .venv/bin/activate
    ```

- On **Windows**:
    ```cmd
    .venv\Scripts\activate
    ```

You should now see `(.venv)` in your terminal prompt.

---

## ✅ **2️⃣ Install Dependencies**

Inside your virtual environment, install the necessary tools:

```bash
pip install pre-commit black ruff
```

---

## ✅ **3️⃣ Create a `.pre-commit-config.yaml` file**

In the root of your project, create a `.pre-commit-config.yaml` with the following content:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.3.0
    hooks:
      - id: black
        language_version: python3
        args:
          - --line-length=100
          - --target-version=py312
        exclude: ^(examples/|docs/)

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.3.5
    hooks:
      - id: ruff
        args:
          - --line-length=100
          - --target-version=py312
          - --select=E,F,I,B
          - --ignore=E203
          - --fix
          - --unsafe-fixes
        exclude: ^(examples/|docs/)
```

---

## ✅ **4️⃣ Install the Pre-commit Hooks**

Run the following command to initialize the hooks:

```bash
pre-commit install
```

This will automatically run `black` and `ruff` every time you commit.

---

## ✅ **5️⃣ Run Pre-commit Manually (First Time)**

To format and lint your entire project:

```bash
pre-commit run --all-files
```

---

## ✅ **6️⃣ Verify Everything Works**

Test the installation with:

```bash
black --version
ruff --version
pre-commit --version
```

---

## 🎯 **7️⃣ Optional: Auto-update Hooks**

To always use the latest versions of hooks:

```bash
pre-commit autoupdate
```

---

# 🚀 **You're all set!**
From now on:
- Every `git commit` will auto-format your code with `black`
- Every `git commit` will lint your code with `ruff`
- The folders `examples/` and `docs/` are excluded automatically

---

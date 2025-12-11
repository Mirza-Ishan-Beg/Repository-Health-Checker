# Introduction

An automation program that runs with the help of task scheduler to allow checking of python imports libraries of selected paths within the computer. It checks the `venv` folder's paths specifically to see and update onto the Google Task if imports on computer turns older than PYPI documented latest one or documentation is not found on the PYPI anymore.

---

![Instruction-to-install.png](Instruction-to-install.png)

---
# Libraries used underneath
- It mainly uses Google's `google_auth_oauthlib.flow`, `googleapiclient.discovery`, and `google.oauth2.credentials`.
- There is also the use of the `Pyside6` for the GUI based dialog box selection.
- We use `requests` to be able to fetch data from the website of our choice as well, specifically in the `PYPIChecker.py`
- `M_CLI_M` stands for `Modulated CLI Menu` which has its own description separately in the class comment itself.
---

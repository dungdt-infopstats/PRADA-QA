@echo off
setlocal enabledelayedexpansion

:: Danh sách các giá trị
set type_list="base" "base_description" "qa"
set model_list="qwen2.5:14b-instruct" "qwen2.5-coder:14b-instruct-fp16" "mistral:7b-instruct"
set part_list="8" "9"

:: Lặp qua từng bộ giá trị và chạy main.py
for %%t in (%type_list%) do (
    for %%m in (%model_list%) do (
        for %%p in (%part_list%) do (
            echo Running: python main.py %%~m %%t %%p
            python main.py %%~m %%t %%p
        )
    )
)

endlocal

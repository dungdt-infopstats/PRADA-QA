@REM @echo off
@REM setlocal enabledelayedexpansion

@REM :: Danh sách các giá trị
@REM set type_list="base" "base_description" "base_code" "base_description_code"
@REM set model_list= "deepseek-r1:32b-qwen-distill-fp16" "deepseek-r1:32b" "gemma2:27b-instruct-fp16" "qwen2.5-coder:32b"
@REM set part_list= "0" "1" "2"

@REM :: Lặp qua từng bộ giá trị và chạy main.py
@REM for %%t in (%type_list%) do (
@REM     for %%m in (%model_list%) do (
@REM         for %%p in (%part_list%) do (
@REM             echo Running: python main.py %%~m %%t %%p
@REM             python main.py %%~m %%t %%p
@REM         )
@REM     )
@REM )

@REM endlocal

@echo off
setlocal enabledelayedexpansion

:: Định nghĩa danh sách các giá trị
set type_list= "qa" "base_description_code"
set model_list="Qwen/Qwen2.5-14B-Instruct"
set part_list="9"

:: Lấy timestamp hiện tại
for /f "tokens=2 delims==" %%I in ('wmic OS Get localdatetime /value') do set datetime=%%I
set timestamp=%datetime:~0,4%-%datetime:~4,2%-%datetime:~6,2%_%datetime:~8,2%-%datetime:~10,2%-%datetime:~12,2%

:: Lặp qua từng bộ giá trị và chạy main.py
for %%t in (%type_list%) do (
    for %%m in (%model_list%) do (
        for %%p in (%part_list%) do (
            set model_name=%%~m
            set model_name=!model_name::=_!
            set model_name=!model_name:.=_!
            set model_name=!model_name:/=_!
            set log_file=acs_log_!model_name!_%%t_%%p_%timestamp%.txt
            echo log_file: "!log_file!"
            echo Running: python main.py %%~m %%t %%p >> !log_file!
            python main.py %%~m %%t %%p >> "!log_file!" 2>&1
        )
    )
)

endlocal




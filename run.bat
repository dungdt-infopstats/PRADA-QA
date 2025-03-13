@echo off
for /L %%i in (9,1,9) do (
    python main.py %%i
)

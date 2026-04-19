@echo off
echo === Batch Test Script ===
echo All arguments received: %*
echo.
echo Arg 1: [%1]
echo Arg 2: [%2]
echo Arg 3: [%3]
echo Arg 4: [%4]
echo Arg 5: [%5]
echo.
echo Simulating some work...
timeout /t 3
echo Done!

# Windows Batch Files for MASEE

This directory contains Windows batch files (.bat) for easy execution of MASEE commands on Windows systems.

## 🚀 Quick Start Commands

### **1. First Time Setup**
```bat
scripts\setup.bat
```
*Installs dependencies and creates .env template*

### **2. Test Installation** (Recommended first command)
```bat
scripts\run_demo.bat
```
*Runs complete workflow demonstration*

### **3. Single Experiment**
```bat
scripts\run_experiment.bat

REM With custom parameters:
scripts\run_experiment.bat gpt-4o-mini base 50 demo 3
```

### **4. Run Tests**
```bat
scripts\run_tests.bat

REM Specific test types:
scripts\run_tests.bat unit
scripts\run_tests.bat integration
scripts\run_tests.bat coverage
```

### **5. Batch Experiments**
```bat
scripts\run_batch.bat
```
*Runs multiple experiments automatically*

### **6. System Monitoring**
```bat
scripts\monitor.bat status
scripts\monitor.bat logs
scripts\monitor.bat processes
scripts\monitor.bat files
```

## 📁 Batch Files Description

| File | Purpose | Parameters |
|------|---------|------------|
| `setup.bat` | Install dependencies, create .env | None |
| `run_demo.bat` | Quick system test | None |
| `run_experiment.bat` | Single experiment | model type part data steps |
| `run_tests.bat` | Run test suite | unit\|integration\|performance\|coverage |
| `run_batch.bat` | Multiple experiments | None (interactive) |
| `monitor.bat` | System monitoring | status\|logs\|processes\|files\|help |

## 🎯 **Your Test Command:**

```bat
scripts\run_demo.bat
```

## ✨ Features of Windows Batch Files

### **Error Handling**
- ✅ Python installation check
- ✅ Dependency verification
- ✅ Clear error messages
- ✅ Automatic pause for error viewing

### **User-Friendly Interface**
- ✅ Colored console output
- ✅ Progress indicators
- ✅ Success/failure status
- ✅ Interactive prompts where needed

### **Logging & Output**
- ✅ Timestamped log files
- ✅ Structured output format
- ✅ Error log capture
- ✅ Results preservation

### **Path Management**
- ✅ Automatically changes to project root
- ✅ Works from any directory
- ✅ Relative path resolution
- ✅ Cross-directory compatibility

## 🔧 Technical Details

### **Requirements**
- Windows 10+ (or Windows with Command Prompt)
- Python 3.10+ installed and in PATH
- Administrative rights may be needed for package installation

### **How They Work**
1. Each batch file starts by checking Python availability
2. Changes to project root directory using `cd /d "%~dp0.."`
3. Runs the appropriate Python commands
4. Captures output and errors
5. Displays results and pauses for user review

### **Customization**
You can modify the batch files to:
- Change default parameters
- Add more experiment configurations
- Modify logging behavior
- Adjust error handling

## 🚨 Troubleshooting

### **Common Issues**

1. **"Python not found"**
   - Install Python from https://python.org
   - Check "Add Python to PATH" during installation
   - Restart Command Prompt after installation

2. **"Access denied" or permission errors**
   - Run Command Prompt as Administrator
   - Check file permissions in project directory

3. **"pip install failed"**
   - Try: `pip install --user -r requirements.txt`
   - Check internet connection
   - Update pip: `python -m pip install --upgrade pip`

4. **Batch file doesn't run**
   - Right-click → "Run as administrator"
   - Check if file is in scripts/ directory
   - Verify Windows hasn't blocked the file

### **Debug Mode**
Add this line after `@echo off` to see detailed execution:
```bat
@echo on
```

### **Manual Execution**
If batch files don't work, you can run commands manually:
```bat
cd /d "C:\path\to\MASEE"
python run_demo.py
```

## 📞 Support

If you encounter issues:
1. Run `scripts\monitor.bat status` to check system
2. Check Python installation: `python --version`
3. Verify project structure: `scripts\monitor.bat files`
4. Review error logs created by batch files

---

*These batch files provide Windows-native execution of MASEE commands with proper error handling and user-friendly interfaces.*
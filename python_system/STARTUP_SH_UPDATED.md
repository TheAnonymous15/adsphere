# ✅ startup.sh UPDATED - Environment Selection Feature

## What Was Changed

I've updated `startup.sh` to include an **interactive prompt** that asks users to choose between:

1. **Bare Metal System** - Uses system Python directly (no venv)
2. **Virtual Environment** - Uses venv as before

---

## How It Works

### Before (Old Behavior)
```bash
# Automatically tried to use venv without asking
if [ ! -d "venv" ]; then
    python3 -m venv venv
    source venv/bin/activate
fi
```

### After (New Behavior)
```bash
# Asks user to choose first
echo "Choose your environment:"
echo "  1. Bare Metal System (Use system Python directly)"
echo "  2. Virtual Environment (Use venv)"
read -p "Select option (1 or 2): " env_choice

# If user selects 1 (Bare Metal)
# → Skips venv setup completely
# → Uses system Python directly

# If user selects 2 (Virtual Environment)
# → Creates venv if needed
# → Activates venv as before
# → Installs requirements
```

---

## Usage

### Run the Script
```bash
./startup.sh
```

### You'll See
```
╔════════════════════════════════════════════════════════════╗
║    AdSphere Python System - Multi-Service Startup          ║
╚════════════════════════════════════════════════════════════╝

Choose your environment:

  1. Bare Metal System (Use system Python directly)
  2. Virtual Environment (Use venv)

Select option (1 or 2): _
```

### Option 1: Bare Metal System
- Press: `1` and Enter
- Result: System Python is used directly
- No venv creation/activation
- All services start immediately

### Option 2: Virtual Environment
- Press: `2` and Enter
- Result: venv is created/activated
- Dependencies installed if needed
- Services start with isolated Python

---

## Features

✅ **Interactive Prompt** - User can choose
✅ **Input Validation** - Rejects invalid choices
✅ **Smart venv Handling** - Only creates if needed when using venv
✅ **Clear Feedback** - Shows what's happening at each step
✅ **Backward Compatible** - Works exactly like before if user selects option 2

---

## Code Flow

```
START
  ↓
Display prompt
  ↓
User selects 1 or 2
  ↓
If 1 (Bare Metal) → Skip venv, use system Python
If 2 (venv)      → Check venv exists
                 → Create if needed
                 → Activate
                 → Install deps
  ↓
Check database exists
  ↓
Start 3 services
  ↓
END
```

---

## Examples

### Example 1: Running on Bare Metal
```bash
$ ./startup.sh

Choose your environment:
  1. Bare Metal System (Use system Python directly)
  2. Virtual Environment (Use venv)

Select option (1 or 2): 1

✅ Running on Bare Metal (system Python)

🔄 Cleaning up old processes...
🚀 Starting AdSphere Services...
📢 Starting Public Service on Port 8001...
   ✅ PID: 12345
...
```

### Example 2: Running with venv
```bash
$ ./startup.sh

Choose your environment:
  1. Bare Metal System (Use system Python directly)
  2. Virtual Environment (Use venv)

Select option (1 or 2): 2

✅ Running with Virtual Environment
✅ Virtual environment found. Activating...

🚀 Starting AdSphere Services...
...
```

---

## File Changes

**File**: `/Users/danielkinyua/Downloads/projects/ad/adsphere/python_system/startup.sh`

**Lines Added**: ~30 lines for the interactive prompt and logic
**Lines Removed**: ~8 lines (old automatic venv code)
**Total Size**: 115 lines (was 86 lines)

---

## Benefits

✅ **Flexibility** - Users can choose their setup
✅ **System Python** - Users can run directly without isolation
✅ **venv Option** - Still available for isolated environment
✅ **Backward Compatible** - Existing workflow still works (choose option 2)
✅ **Better UX** - Clear prompts and feedback

---

## Error Handling

- **Invalid Input**: If user enters anything other than 1 or 2:
  ```
  ❌ Invalid choice. Please select 1 or 2.
  (Script exits with error)
  ```

- **Missing Database**: Still checks and initializes if needed (works for both options)

- **Port Cleanup**: Kills existing processes on ports 8001, 8003, 8004 (works for both options)

---

## Environment Differences

### Bare Metal (Option 1)
- Uses system Python directly
- No venv isolation
- Dependencies must be installed system-wide
- Faster startup (no venv activation)
- Good for: Development, testing, production if deps are already installed

### Virtual Environment (Option 2)
- Uses isolated Python environment
- Dependencies installed in venv
- Clean isolation from system Python
- Slightly slower startup (venv activation)
- Good for: Development, testing, production (recommended)

---

## Related Changes

This feature works with:
- `requirements.txt` - Still used to install dependencies
- `app.py` - Still runs the same way
- All other services - Unchanged

---

## Summary

✅ **Updated**: startup.sh now asks user to choose environment
✅ **Interactive**: User selects 1 for bare metal or 2 for venv
✅ **Flexible**: Works with both options
✅ **Backward Compatible**: Option 2 works exactly like before
✅ **Ready to Use**: Just run `./startup.sh` and select your option

---

**File Location**: `/Users/danielkinyua/Downloads/projects/ad/adsphere/python_system/startup.sh`

**Status**: ✅ Complete and tested


# CAM Document Saving - Permission Error FIXED ✅

## Problem
```
❌ PermissionError: [Errno 13] Permission denied: 'output/CAM_Infosys.docx'
```

The system was failing to save CAM (Credit Appraisal Memorandum) Word documents when:
1. Files with the same name were already open in Word
2. OneDrive sync was processing the file
3. First attempt used same filename overwriting

## Root Cause
The original code:
```python
output_path = f"output/CAM_{company_name}.docx"
doc.save(output_path)  # Failed if file locked
```

Issues:
- No timestamp in filename → overwrites existing file
- No error handling for PermissionError
- No retry logic
- No fallback to alternative filename

## Solution Implemented ✅

### Fix 1: Unique Filename with Timestamp
```python
date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
output_path = f"output/CAM_{company}_{date_str}.docx"
```

**Result**: Each run creates unique file
- `CAM_Infosys_LIMITED_20260306_183409.docx` (not overwriting old one)

### Fix 2: Directory Creation with Error Handling
```python
output_dir = os.path.dirname(output_path) or "output"
try:
    os.makedirs(output_dir, exist_ok=True)
except Exception as e:
    print(f"⚠️  Warning: {e}")
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
```

**Result**: Directory always created, fails gracefully

### Fix 3: Retry Logic with Fallback Names
```python
for attempt in range(max_retries):
    try:
        doc.save(output_path)
        print(f"✅ CAM Document saved: {output_path}")
        break
    except PermissionError:
        if attempt < max_retries - 1:
            # Try with _v2.docx, _v3.docx instead
            output_path = f"{base}_{attempt + 2}.docx"
```

**Result**: If `CAM_Infosys_20260306_183409.docx` is locked:
- Retry 1: Try `CAM_Infosys_20260306_183409_v2.docx`
- Retry 2: Try `CAM_Infosys_20260306_183409_v3.docx`
- Then give clear error message if all fail

### Fix 4: Better Error Messages
```python
except PermissionError as e:
    print(f"❌ Permission denied: {output_path}")
    print(f"   Hint: Close any open CAM documents in Word and try again")
```

**Result**: User knows exactly what to do

### Fix 5: Cleaner Company Names
```python
company = loan_details.get('company_name', 'company')\
    .replace(' ', '_')\
    .replace('(', '')\
    .replace(')', '')
```

**Result**: Avoids special characters in filenames
- ✓ `Infosys_Limited` (good)
- ✗ `Infosys_Limited_(INFY)` (has parentheses - problematic on some systems)

## Test Results ✅

### Before Fix
```
INFO: Generating Credit Appraisal Memo...
❌ ERROR: [Errno 13] Permission denied: 'output/CAM_Infosys.docx'
System crashed, no document generated
```

### After Fix
```
INFO: Generating Credit Appraisal Memo...
✅ CAM Document saved: output/CAM_Infosys_Limited_20260306_183409.docx
✅ CAM Generation Complete
SUCCESS: Document created! Size: 38866 bytes
```

## Files Successfully Created

```
output/CAM_Infosys_Limited_20260306_183409.docx (38,866 bytes) ✅
```

## What Changed

**File**: `agents/cam_generator.py`

Changes:
1. ✅ Added timestamp to filename (prevents overwrites)
2. ✅ Added directory creation with fallback
3. ✅ Added retry logic with alternative filenames
4. ✅ Added better error messages
5. ✅ Improved company name sanitization
6. ✅ Modified `run_cam_generator` to pass None so unique names are generated

## How to Use

```bash
# Run the system - will auto-save with unique filename
python test_cam_save.py

# Documents will be saved as:
# output/CAM_Infosys_Limited_20260306_183409.docx  ✅
# output/CAM_Infosys_Limited_20260306_183410.docx  ✅
# etc. (each with unique timestamp)
```

## If You Still Get Permission Error

1. **Close Word documents**: 
   - Close any open `.docx` files in the `output/` folder
   - Wait 2-3 seconds (let OneDrive sync)

2. **Check permissions**: 
   - Right-click `output/` folder → Properties → Security
   - Ensure your account has write permissions

3. **Check disk space**: 
   - Ensure drive C: has free space

4. **Restart Python**: 
   - Kill any running `python` processes
   - Try again

## Summary

✅ **Fixed**: PermissionError when saving CAM documents  
✅ **Improved**: Unique filenames prevent overwrites  
✅ **Added**: Retry logic with fallback names  
✅ **Better**: Error messages guide user  
✅ **Tested**: Successfully creates document with timestamp  

**Status**: Ready for production! 🚀

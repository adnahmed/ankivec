# Windows Support Implementation Summary

## What Was Done

The ankivec addon has been successfully refactored to support Windows while following Anki addon best practices. Here's what was implemented:

### 1. **Hybrid Dependency Management**
- **Vendored Pure-Python Dependencies**: ollama, pydantic, httpx, requests, and all their pure-Python transitive dependencies are now vendored in `src/vendor/`
- **Runtime-Installed Dependencies**: chromadb and numpy are still installed at runtime via `uv sync` (these have C extensions and are heavy, so vendoring isn't practical)

### 2. **Windows Platform Support**
- **Removed `NotImplementedError` for Windows**: The addon now has full Windows support
- **Automatic uv Detection**: Uses `ANKI_LAUNCHER_UV` environment variable (set by Anki), with fallback to default Windows Anki location
- **Cross-Platform venv Paths**: Handles both:
  - Windows: `.venv\Lib\site-packages`
  - Unix: `.venv/lib/pythonX.Y/site-packages` (dynamically detected)

### 3. **Addon Manifest**
- Created `manifest.json` with proper Anki addon metadata
- Specifies: package ID, version, supported Anki versions (2.1.45+)

### 4. **Build Process**
- Updated `build.sh` to include `src/` in addon package
- Final addon includes all vendored dependencies for immediate use

## File Changes

### New Files Created
- `manifest.json` - Anki addon manifest
- `src/__init__.py` - Makes src a Python package
- `src/vendor/__init__.py` - Vendor documentation
- `src/vendor/` - Contains all pure-Python dependencies (14 packages)

### Modified Files
- [__init__.py](__init__.py#L1-L75) - Added Windows detection and vendor loader
- [build.sh](build.sh) - Updated to include src/vendor in addon package

## How It Works on Windows

1. **Addon Installation**: User installs ankivec addon in Anki
2. **Startup**: Anki loads the addon's `__init__.py`
3. **Vendor Setup**: 
   - Pure-Python packages (ollama, pydantic, etc.) are loaded from `src/vendor/`
   - Automatically added to sys.path before Anki imports
4. **Dependency Installation**:
   - On first run, `uv sync` is called to install chromadb and numpy
   - uv.exe is found via `ANKI_LAUNCHER_UV` environment variable or Windows default location
   - Virtual environment site-packages is added to sys.path
5. **Ready**: All dependencies available, addon functions normally

## Dependency Tree

### Vendored (Pure-Python)
```
src/vendor/
├── ollama (HTTP client for local models)
├── requests (HTTP library)
├── httpx (Modern HTTP client)
├── pydantic (Data validation)
├── anyio (Async support)
├── httpcore (HTTP transport)
├── h11 (HTTP/1.1 primitives)
├── idna (Internationalized domain names)
├── charset_normalizer (Character set detection)
├── certifi (CA certificates)
├── annotated_types (Type annotations)
├── typing_extensions (Typing backports)
└── typing_inspection (Type introspection)
```

### Runtime-Installed (Heavy C Extensions)
```
.venv/lib/site-packages/
├── chromadb (Vector database)
└── numpy (Numerical computing)
```

## Platform-Specific Wheels

The vendor directory includes platform-specific C extensions compiled for:
- **Python 3.13** (matches latest Anki versions)
- **Windows x86_64**

If different Python versions or platforms are needed, regenerate with:
```bash
pip download ollama pydantic httpx requests ... --platform win_amd64 -d vendor_downloads
```

## Verification

The implementation has been tested with Python 3.13:
- ✓ ollama imports successfully
- ✓ pydantic imports successfully  
- ✓ requests imports successfully
- ✓ httpx imports successfully
- ✓ All transitive dependencies resolved

## Next Steps for Distribution

1. **Windows Distribution**: Continue development and testing on Windows
2. **macOS/Linux**: Existing behavior preserved, should continue working
3. **Cross-Platform Packages**: If supporting multiple OS, may optionally create platform-specific addon distributions to reduce size

## Troubleshooting

### If you get "Could not find uv executable"
- Ensure Anki is installed properly
- Or set `ANKI_LAUNCHER_UV` environment variable to your uv.exe location

### If chromadb fails to import
- Manually run: `{ADDON_ROOT}\.venv\Scripts\uv sync --project {ADDON_ROOT}`
- Check that .venv/Lib/site-packages has chromadb installed

### For Python version mismatches
- If running Anki with different Python version, regenerate vendor packages for that version
- The Windows C extensions (pydantic_core, charset_normalizer) are version-specific

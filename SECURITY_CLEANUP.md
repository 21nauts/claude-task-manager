# Security & Privacy Cleanup

## Changes Made

### ✅ Removed Hardcoded Credentials

1. **SSH Key Configuration**
   - **Before:** Hardcoded `id_48nauts` in `sync_manager.py`
   - **After:** Uses `.env` configuration with `GIT_SSH_KEY_PATH`
   - Falls back to default SSH config if not specified

2. **User-Specific Shebangs**
   - **Before:** `#!/Users/jarvis/.pyenv/shims/uv run --script`
   - **After:** `#!/usr/bin/env -S uv run --script`
   - Now works for any user with `uv` in PATH

### ✅ Environment Configuration

Created `.env.example` with all configurable values:
- `GIT_SSH_KEY_PATH` - Custom SSH key path (optional)
- `TASKS_REPO_PATH` - Local tasks repository path
- `TASKS_REPO_REMOTE` - Git remote URL
- Sync configuration options
- Server configuration

### ✅ Dependencies Updated

Added `python-dotenv>=1.0.0` to `requirements.txt` for environment variable management.

### ✅ Legacy Code Removed

- **Deleted:** `database.py` - Unused SQLite legacy code
- **Active:** Git-based storage via `git_storage.py`

## Setup Instructions

### For End Users

1. **Copy environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Configure SSH key (optional):**
   ```bash
   # Edit .env and add:
   GIT_SSH_KEY_PATH=~/.ssh/id_rsa
   ```

3. **Install dependencies:**
   ```bash
   uv pip install -r requirements.txt
   # or
   pip install -r requirements.txt
   ```

4. **Start server:**
   ```bash
   uv run server.py
   ```

### For Developers

**Never commit:**
- `.env` file (already in .gitignore)
- Personal SSH keys
- User-specific paths
- GitHub usernames/organizations (use placeholders in docs)

**Always use:**
- `Path.home()` for home directory references
- `os.getenv()` or `load_dotenv()` for configuration
- `#!/usr/bin/env` for portable shebangs
- Generic examples in documentation (e.g., `YOUR_USERNAME`)

## Files Modified

### Core Files
- ✅ `sync_manager.py` - Added .env support for SSH key
- ✅ `requirements.txt` - Added python-dotenv
- ✅ `.env.example` - Created configuration template
- ✅ `post_tool_use_task_hook.py` - Fixed shebang
- ✅ `.claude/hooks/post_tool_use.py` - Fixed shebang

### Documentation
- 📝 `README.md` - Update with security notes (TODO)
- 📝 `WORKFLOW.md` - Replace hardcoded examples (TODO)
- 📝 `SETUP.md` - Add .env configuration steps (TODO)

### Deleted
- 🗑️ `database.py` - Legacy SQLite code (unused)

## Security Checklist

Before pushing to GitHub:

- [ ] No hardcoded credentials in code
- [ ] All user-specific paths use `Path.home()` or env vars
- [ ] `.env` file in `.gitignore`
- [ ] `.env.example` provided with placeholders
- [ ] Documentation uses generic examples
- [ ] No personal GitHub usernames in code
- [ ] Shebangs use `#!/usr/bin/env`

## GitHub Examples to Replace

### In Documentation Files

**Find and replace:**
- `21nauts` → `YOUR_USERNAME` or `YOUR_ORG`
- `CandooLabs` → `YOUR_ORG`
- `48nauts` → (remove references)
- `id_48nauts` → `id_rsa` or generic example
- `git@github.com:21nauts/` → `git@github.com:YOUR_USERNAME/`

**Files to check:**
- `README.md`
- `WORKFLOW.md`
- `SETUP.md`

## Testing

After cleanup, verify:

1. **Without .env:** System works with default SSH config
   ```bash
   rm .env
   uv run server.py
   # Should work with default ~/.ssh/id_rsa or id_ed25519
   ```

2. **With custom SSH key:** System uses specified key
   ```bash
   echo "GIT_SSH_KEY_PATH=~/.ssh/custom_key" > .env
   uv run server.py
   # Should use custom_key for Git operations
   ```

3. **Portable shebangs:** Hooks work for any user
   ```bash
   ./.claude/hooks/post_tool_use.py --help
   # Should execute without errors
   ```

## Migration Notes

### For Existing Users

If you were using the hardcoded `id_48nauts` key:

1. Create `.env` file:
   ```bash
   echo "GIT_SSH_KEY_PATH=~/.ssh/id_48nauts" > .env
   ```

2. Update dependencies:
   ```bash
   uv pip install python-dotenv
   ```

3. Restart server:
   ```bash
   uv run server.py
   ```

Everything will continue working exactly as before!

### For New Users

The system now works out-of-the-box with standard SSH configurations. No additional setup needed unless you use custom SSH keys.

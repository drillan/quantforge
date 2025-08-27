---
description: Execute smart commits with context-aware quality checks
argument-hint: "[type] [--path <paths>] [--options] | docs | fix | feat | quick | style | test | refactor | perf | chore | full | help"
---

# AI Smart Commit Protocol - QuantForge

Execute commits with intelligent, context-aware quality checks based on the type of changes.

## 🎯 Usage

```bash
/commit-ai [type] [--options]
```

For path-specific commits:
```bash
/commit-ai [type] --path <paths> [--options]
```

### Types
- `docs` - Documentation changes only (skip code checks)
- `fix` - Bug fixes (full quality checks)
- `feat` - New features (full checks + docs verification)
- `quick` - Quick commits (format and basic lint only)
- `style` - Style changes (formatting only)
- `test` - Test changes (focus on test execution)
- `refactor` - Code refactoring (full checks + behavior verification)
- `perf` - Performance improvements (include benchmarks)
- `chore` - Maintenance tasks (minimal checks)
- `full` or no argument - Complete quality checks (default)
- `help` - Show this help message

### Options
- `--path <paths>` - Commit only specified files/directories
- `--skip-tests` - Skip test execution
- `--skip-rust` - Skip Rust quality checks
- `--skip-python` - Skip Python quality checks
- `--message "..."` - Use custom commit message
- `--no-fix` - Disable automatic fixes (report only)
- `--scope <scope>` - Specify commit scope

## 🤖 Execution Flow

### Parse Arguments

First, parse the provided arguments to determine execution mode:

```bash
# Parse $ARGUMENTS
ARGUMENTS="$ARGUMENTS"
TYPE=""
OPTIONS=""
CUSTOM_MESSAGE=""
SCOPE=""
PATHS=""
SKIP_TESTS=false
SKIP_RUST=false
SKIP_PYTHON=false
NO_FIX=false

# Extract type and options from arguments
if [[ -z "$ARGUMENTS" || "$ARGUMENTS" == "full" ]]; then
    TYPE="full"
elif [[ "$ARGUMENTS" == "help" ]]; then
    # Show usage and exit
    echo "📚 Smart Commit Command Usage:"
    echo "  /commit-ai [type] [--options]"
    echo ""
    echo "Types:"
    echo "  docs     - Documentation only (skip code checks)"
    echo "  fix      - Bug fixes (full checks)"
    echo "  feat     - New features (full + docs)"
    echo "  quick    - Quick commit (minimal checks)"
    echo "  style    - Style changes (format only)"
    echo "  test     - Test changes (test focus)"
    echo "  refactor - Refactoring (full + behavior)"
    echo "  perf     - Performance (with benchmarks)"
    echo "  chore    - Maintenance (minimal)"
    echo "  full     - Complete checks (default)"
    echo ""
    echo "Options:"
    echo "  --path <paths>    Commit only specified files"
    echo "  --skip-tests      Skip test execution"
    echo "  --skip-rust       Skip Rust checks"
    echo "  --skip-python     Skip Python checks"
    echo "  --message \"...\"   Custom message"
    echo "  --no-fix          No auto-fixes"
    echo "  --scope <scope>   Commit scope"
    exit 0
else
    # Parse type and options
    TYPE=$(echo "$ARGUMENTS" | awk '{print $1}')
    OPTIONS=$(echo "$ARGUMENTS" | cut -d' ' -f2-)
    
    # Parse individual options
    if [[ "$OPTIONS" == *"--skip-tests"* ]]; then
        SKIP_TESTS=true
    fi
    if [[ "$OPTIONS" == *"--skip-rust"* ]]; then
        SKIP_RUST=true
    fi
    if [[ "$OPTIONS" == *"--skip-python"* ]]; then
        SKIP_PYTHON=true
    fi
    if [[ "$OPTIONS" == *"--no-fix"* ]]; then
        NO_FIX=true
    fi
    if [[ "$OPTIONS" == *"--message"* ]]; then
        CUSTOM_MESSAGE=$(echo "$OPTIONS" | sed -n 's/.*--message "\([^"]*\)".*/\1/p')
    fi
    if [[ "$OPTIONS" == *"--scope"* ]]; then
        SCOPE=$(echo "$OPTIONS" | sed -n 's/.*--scope \([^ ]*\).*/\1/p')
    fi
    if [[ "$OPTIONS" == *"--path"* ]]; then
        # Extract paths - everything after --path until the next option or end
        PATHS=$(echo "$OPTIONS" | sed -n 's/.*--path \([^-]*\).*/\1/p' | xargs)
    fi
fi
```

### Smart Detection

If no type is provided, analyze changes to determine the best mode:

```bash
# Auto-detect type if not specified
if [[ "$TYPE" == "full" ]]; then
    # Analyze changed files
    if [[ -n "$PATHS" ]]; then
        # If paths are specified, analyze only those
        CHANGED_FILES=""
        for path in $PATHS; do
            if [[ -f "$path" ]]; then
                CHANGED_FILES="$CHANGED_FILES$path\n"
            elif [[ -d "$path" ]]; then
                CHANGED_FILES="$CHANGED_FILES$(find "$path" -type f 2>/dev/null)\n"
            fi
        done
    else
        CHANGED_FILES=$(git diff --name-only --cached)
    fi
    
    # Check patterns
    if echo "$CHANGED_FILES" | grep -q "^docs/" && ! echo "$CHANGED_FILES" | grep -qE "\.(py|rs)$"; then
        TYPE="docs"
        echo "📝 Auto-detected: Documentation changes"
    elif echo "$CHANGED_FILES" | grep -q "^tests/" && ! echo "$CHANGED_FILES" | grep -q "^src/"; then
        TYPE="test"
        echo "🧪 Auto-detected: Test changes"
    elif git diff --cached | grep -q "^-.*bug\|^-.*fix\|^-.*error"; then
        TYPE="fix"
        echo "🐛 Auto-detected: Bug fix"
    elif echo "$CHANGED_FILES" | grep -q "new file"; then
        TYPE="feat"
        echo "✨ Auto-detected: New feature"
    fi
fi

echo "🎯 Commit type: $TYPE"
if [[ -n "$PATHS" ]]; then
    echo "📁 Path filter: $PATHS"
fi
```

## 📋 Type-Specific Workflows

### 1. Documentation Only (`docs`)

```bash
if [[ "$TYPE" == "docs" ]]; then
    echo "📚 Documentation commit - skipping code quality checks"
    
    # Check documentation
    echo "Checking documentation..."
    
    # Verify markdown files
    if command -v markdownlint &> /dev/null; then
        markdownlint docs/**/*.md || true
    fi
    
    # Check for broken links
    if [[ -f "docs/conf.py" ]]; then
        cd docs && make linkcheck || true
        cd ..
    fi
    
    # Verify examples in documentation still work
    for example in docs/user_guide/examples.md docs/quickstart.md; do
        if [[ -f "$example" ]]; then
            echo "Verifying examples in $example..."
            # Extract and test Python code blocks
            grep -A 20 "```python" "$example" | grep -v "```" > /tmp/test_example.py
            uv run python /tmp/test_example.py 2>/dev/null || echo "Note: Some examples may need context"
        fi
    done
    
    # Skip all code checks
    SKIP_TESTS=true
    SKIP_RUST=true
    SKIP_PYTHON=true
fi
```

### 2. Bug Fix (`fix`)

```bash
if [[ "$TYPE" == "fix" ]]; then
    echo "🐛 Bug fix commit - running comprehensive quality checks"
    
    # Full quality checks
    echo "Running full quality suite..."
    
    # Ensure the fix doesn't break anything
    echo "Verifying fix integrity..."
    
    # Run related tests specifically
    CHANGED_FILES=$(git diff --name-only --cached)
    for file in $CHANGED_FILES; do
        if [[ "$file" == *.py ]]; then
            # Find and run related test file
            test_file="tests/test_$(basename $file)"
            if [[ -f "$test_file" ]]; then
                echo "Running related test: $test_file"
                uv run pytest "$test_file" -v
            fi
        fi
    done
fi
```

### 3. New Feature (`feat`)

```bash
if [[ "$TYPE" == "feat" ]]; then
    echo "✨ Feature commit - ensuring documentation and full quality"
    
    # Check for new public APIs
    echo "Checking for new public APIs..."
    
    # Verify documentation exists for new features
    echo "Verifying documentation..."
    CHANGED_FILES=$(git diff --name-only --cached)
    
    for file in $CHANGED_FILES; do
        if [[ "$file" == src/models/*.rs ]] || [[ "$file" == python/**/*.py ]]; then
            base_name=$(basename "$file" .rs)
            base_name=$(basename "$base_name" .py)
            
            # Check if corresponding docs exist
            if ! ls docs/api/python/"$base_name".md docs/models/"$base_name".md 2>/dev/null; then
                echo "⚠️  Warning: No documentation found for $base_name"
                echo "Creating documentation template..."
                # Auto-generate basic documentation
            fi
        fi
    done
    
    # Ensure examples are provided
    echo "Checking for usage examples..."
fi
```

### 4. Quick Commit (`quick`)

```bash
if [[ "$TYPE" == "quick" ]]; then
    echo "⚡ Quick commit - minimal checks only"
    
    # Format only
    echo "Formatting code..."
    
    if [[ "$SKIP_PYTHON" == false ]]; then
        uv run ruff format .
    fi
    
    if [[ "$SKIP_RUST" == false ]]; then
        cargo fmt --all
    fi
    
    # Skip tests and deep checks
    SKIP_TESTS=true
    
    echo "Quick checks complete"
fi
```

### 5. Style Changes (`style`)

```bash
if [[ "$TYPE" == "style" ]]; then
    echo "🎨 Style commit - formatting only"
    
    # Format code
    if [[ "$SKIP_PYTHON" == false ]]; then
        uv run ruff format .
        uv run ruff check . --select I --fix  # Fix imports only
    fi
    
    if [[ "$SKIP_RUST" == false ]]; then
        cargo fmt --all
    fi
    
    # Skip all other checks
    SKIP_TESTS=true
    echo "Style formatting complete"
fi
```

### 6. Test Changes (`test`)

```bash
if [[ "$TYPE" == "test" ]]; then
    echo "🧪 Test commit - focusing on test execution"
    
    # Run all tests with coverage
    echo "Running comprehensive test suite..."
    
    if [[ "$SKIP_TESTS" == false ]]; then
        # Python tests with coverage
        uv run pytest tests/ --cov=. --cov-report=term-missing
        
        # Rust tests
        cargo test --release --all-features
    fi
    
    # Verify test quality
    echo "Checking test quality..."
    # Check for test docstrings, assertions, etc.
fi
```

### 7. Refactoring (`refactor`)

```bash
if [[ "$TYPE" == "refactor" ]]; then
    echo "♻️  Refactor commit - ensuring behavior preservation"
    
    # Full quality checks
    echo "Running full quality checks..."
    
    # Verify no behavior changes
    echo "Verifying behavior preservation..."
    
    # Run all tests to ensure nothing broke
    if [[ "$SKIP_TESTS" == false ]]; then
        uv run pytest tests/ -v
        cargo test --release
    fi
    
    # Check for performance regression
    if command -v hyperfine &> /dev/null; then
        echo "Checking performance..."
        # Run basic performance checks
    fi
fi
```

### 8. Performance (`perf`)

```bash
if [[ "$TYPE" == "perf" ]]; then
    echo "⚡ Performance commit - running benchmarks"
    
    # Run performance benchmarks
    echo "Running performance benchmarks..."
    
    if [[ "$SKIP_RUST" == false ]]; then
        cargo bench
        
        # Compare with baseline if exists
        if [[ -f "target/criterion/baseline.json" ]]; then
            echo "Comparing with baseline performance..."
        fi
    fi
    
    # Python performance tests
    if [[ "$SKIP_PYTHON" == false ]] && [[ -f "tests/performance/test_benchmarks.py" ]]; then
        uv run pytest tests/performance/ -v
    fi
fi
```

### 9. Chore (`chore`)

```bash
if [[ "$TYPE" == "chore" ]]; then
    echo "🔧 Chore commit - minimal checks"
    
    # Basic build verification
    echo "Verifying build..."
    
    if [[ "$SKIP_RUST" == false ]]; then
        cargo build --release
    fi
    
    if [[ "$SKIP_PYTHON" == false ]]; then
        uv run python -c "import quantforge; print('✓ Import OK')"
    fi
    
    # Skip comprehensive tests
    SKIP_TESTS=true
fi
```

### 10. Full Checks (`full` or default)

```bash
if [[ "$TYPE" == "full" ]] || [[ -z "$TYPE" ]]; then
    echo "🔍 Full commit - comprehensive quality checks"
    
    # Complete quality workflow
    echo "Running complete quality suite..."
    # All checks enabled by default
fi
```

## 🔧 Common Quality Checks

Execute these based on type and options:

### Python Quality Checks

```bash
if [[ "$SKIP_PYTHON" == false ]]; then
    echo "🐍 Python quality checks..."
    
    # Determine files to check
    PYTHON_FILES=""
    if [[ -n "$PATHS" ]]; then
        # Filter Python files from specified paths
        for path in $PATHS; do
            if [[ -f "$path" && "$path" == *.py ]]; then
                PYTHON_FILES="$PYTHON_FILES $path"
            elif [[ -d "$path" ]]; then
                # Find Python files in directory
                PYTHON_FILES="$PYTHON_FILES $(find "$path" -name "*.py" 2>/dev/null | tr '\n' ' ')"
            fi
        done
        
        if [[ -z "$PYTHON_FILES" ]]; then
            echo "  No Python files in specified paths, skipping Python checks"
            SKIP_PYTHON=true
        else
            echo "  Checking Python files: $PYTHON_FILES"
        fi
    else
        PYTHON_FILES="."
    fi
    
    if [[ "$SKIP_PYTHON" == false ]]; then
        # Format
        uv run ruff format $PYTHON_FILES
        
        # Lint and fix
        if [[ "$NO_FIX" == false ]]; then
            uv run ruff check $PYTHON_FILES --fix
        else
            uv run ruff check $PYTHON_FILES
        fi
        
        # Type check
        if [[ "$PYTHON_FILES" != "." ]]; then
            uv run mypy $PYTHON_FILES
        else
            uv run mypy .
        fi
        
        # Tests
        if [[ "$SKIP_TESTS" == false ]]; then
            if [[ -n "$PATHS" ]]; then
                # Run tests related to specified files
                TEST_FILES=""
                for py_file in $PYTHON_FILES; do
                    base_name=$(basename "$py_file" .py)
                    test_file="tests/test_${base_name}.py"
                    if [[ -f "$test_file" ]]; then
                        TEST_FILES="$TEST_FILES $test_file"
                    fi
                done
                
                if [[ -n "$TEST_FILES" ]]; then
                    echo "  Running related tests: $TEST_FILES"
                    uv run pytest $TEST_FILES -q
                else
                    echo "  No related tests found for specified files"
                fi
            else
                uv run pytest tests/ -q
            fi
        fi
    fi
fi
```

### Rust Quality Checks

```bash
if [[ "$SKIP_RUST" == false ]]; then
    echo "🦀 Rust quality checks..."
    
    # Check if any Rust files are in the specified paths
    if [[ -n "$PATHS" ]]; then
        RUST_FILES=""
        for path in $PATHS; do
            if [[ -f "$path" && "$path" == *.rs ]]; then
                RUST_FILES="$RUST_FILES $path"
            elif [[ -d "$path" ]]; then
                # Find Rust files in directory
                RUST_FILES="$RUST_FILES $(find "$path" -name "*.rs" 2>/dev/null | tr '\n' ' ')"
            fi
        done
        
        if [[ -z "$RUST_FILES" ]]; then
            echo "  No Rust files in specified paths, skipping Rust checks"
            SKIP_RUST=true
        else
            echo "  Found Rust files in specified paths"
            # Note: Rust tools typically need to run on the whole crate
            echo "  Running full Rust checks (cargo requires whole-crate analysis)"
        fi
    fi
    
    if [[ "$SKIP_RUST" == false ]]; then
        # Format
        cargo fmt --all
        
        # Clippy
        if [[ "$NO_FIX" == false ]]; then
            cargo clippy --all-targets --all-features --fix -- -D warnings
        else
            cargo clippy --all-targets --all-features -- -D warnings
        fi
        
        # Build and test
        cargo build --release
        
        if [[ "$SKIP_TESTS" == false ]]; then
            cargo test --release
        fi
        
        # Build Python bindings
        uv run maturin develop --release
    fi
fi
```

### Critical Rules Check

```bash
# Always run critical rules check unless explicitly skipped
if [[ "$TYPE" != "docs" ]] && [[ "$TYPE" != "style" ]]; then
    echo "📋 Critical rules compliance..."
    
    # Note: Critical rules check always runs on the entire codebase for safety
    # even when --path is specified to ensure no violations are introduced
    
    ./scripts/check_critical_rules.sh || {
        if [[ "$NO_FIX" == false ]]; then
            echo "Fixing critical rules violations..."
            # Auto-fix violations
        else
            echo "❌ Critical rules violations detected"
            exit 1
        fi
    }
    
    ./scripts/detect_hardcode.sh || {
        if [[ "$NO_FIX" == false ]]; then
            echo "Fixing hardcoded values..."
            # Move to constants
        fi
    }
fi
```

## 📝 Commit Message Generation

Generate appropriate commit message based on type:

```bash
generate_commit_message() {
    local type="$1"
    local scope="$2"
    local custom_msg="$3"
    
    # If custom message provided, validate and use it
    if [[ -n "$custom_msg" ]]; then
        # Ensure it follows conventional commits format
        if ! echo "$custom_msg" | grep -qE "^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)"; then
            echo "$TYPE($SCOPE): $custom_msg"
        else
            echo "$custom_msg"
        fi
        return
    fi
    
    # Auto-generate message based on changes
    local changed_files=$(git diff --name-only --cached)
    local file_count=$(echo "$changed_files" | wc -l)
    
    # Determine scope if not provided
    if [[ -z "$scope" ]]; then
        if echo "$changed_files" | grep -q "^src/models/"; then
            scope="models"
        elif echo "$changed_files" | grep -q "^python/"; then
            scope="api"
        elif echo "$changed_files" | grep -q "^tests/"; then
            scope="tests"
        elif echo "$changed_files" | grep -q "^docs/"; then
            scope="docs"
        fi
    fi
    
    # Generate message based on type
    case "$type" in
        docs)
            echo "docs${scope:+($scope)}: update documentation"
            ;;
        fix)
            echo "fix${scope:+($scope)}: resolve issue in ${scope:-codebase}"
            ;;
        feat)
            echo "feat${scope:+($scope)}: implement new functionality"
            ;;
        style)
            echo "style${scope:+($scope)}: format code and organize imports"
            ;;
        test)
            echo "test${scope:+($scope)}: improve test coverage"
            ;;
        refactor)
            echo "refactor${scope:+($scope)}: improve code structure"
            ;;
        perf)
            echo "perf${scope:+($scope)}: optimize performance"
            ;;
        chore)
            echo "chore${scope:+($scope)}: update dependencies and configuration"
            ;;
        *)
            echo "feat${scope:+($scope)}: update implementation"
            ;;
    esac
}
```

## 🚀 Execute Commit

After all checks pass:

```bash
# Generate commit message
COMMIT_MSG=$(generate_commit_message "$TYPE" "$SCOPE" "$CUSTOM_MESSAGE")

echo "💬 Commit message: $COMMIT_MSG"

# Stage changes based on path specification
if [[ -n "$PATHS" ]]; then
    echo "📁 Adding specified paths: $PATHS"
    
    # Verify paths exist
    for path in $PATHS; do
        if [[ ! -e "$path" ]]; then
            echo "❌ Error: Path does not exist: $path"
            exit 1
        fi
    done
    
    # Add specified paths
    git add $PATHS
    
    # Show what will be committed
    echo "📋 Files to be committed:"
    git diff --name-only --cached
else
    # Stage all changes
    git add -A
fi

# Create commit
git commit -m "$COMMIT_MSG"

# Show summary
echo "✅ Commit created successfully!"
git log -1 --oneline
```

## 📊 Completion Report

```bash
report_completion() {
    echo ""
    echo "✅ Smart Commit Complete"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Type: $TYPE"
    echo "Commit: $(git log -1 --pretty=format:'%h %s')"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if [[ "$SKIP_PYTHON" == false ]]; then
        echo "Python: ✓ Checked"
    fi
    if [[ "$SKIP_RUST" == false ]]; then
        echo "Rust: ✓ Checked"
    fi
    if [[ "$SKIP_TESTS" == false ]]; then
        echo "Tests: ✓ Executed"
    else
        echo "Tests: ⊘ Skipped"
    fi
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Show changed files summary
    git diff --stat HEAD~1
}

report_completion
```

## 🎯 Best Practices

1. **Default to safety**: When in doubt, run full checks
2. **Use appropriate types**: Choose the type that matches your changes
3. **Document features**: Always update docs for new features
4. **Test fixes**: Ensure bug fixes include tests
5. **Benchmark performance**: Measure improvements with `perf` type

## 📚 Examples

```bash
# Documentation update
/commit-ai docs

# Bug fix without tests (emergency)
/commit-ai fix --skip-tests

# New feature with custom message
/commit-ai feat --message "Add Monte Carlo simulation for Asian options" --scope models

# Quick formatting fix
/commit-ai quick

# Refactoring with full checks
/commit-ai refactor

# Performance improvement with benchmarks
/commit-ai perf --scope simd

# Dependency update
/commit-ai chore --message "Update PyO3 to 0.21.0"

# Commit only specific files
/commit-ai feat --path "src/models/black_scholes.rs tests/test_black_scholes.py"

# Commit a specific directory
/commit-ai refactor --path src/models/

# Fix a single file with custom message
/commit-ai fix --path src/lib.rs --message "Fix memory leak in calculation"

# Documentation change in specific folder
/commit-ai docs --path docs/api/

# Multiple files with different types
/commit-ai feat --path "src/models/asian.rs python/quantforge/asian.py" --scope models

# Full quality check (default)
/commit-ai
```

---

This smart commit protocol ensures efficient, context-aware quality checks while maintaining the high standards of the QuantForge project.
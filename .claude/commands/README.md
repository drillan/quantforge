# QuantForge AI Command Reference

This directory contains custom slash commands for AI assistants working on the QuantForge project.

## Available Commands

### `/commit-ai` - Smart Commit System

Execute intelligent commits with context-aware quality checks.

**Usage:**
```bash
/commit-ai [type] [--options]
```

**Quick Reference:**

| Type | Purpose | Quality Checks |
|------|---------|----------------|
| `docs` | Documentation only | Skip code checks |
| `fix` | Bug fixes | Full checks + related tests |
| `feat` | New features | Full checks + docs verify |
| `quick` | Rapid commits | Format + basic lint only |
| `style` | Code formatting | Format only |
| `test` | Test changes | Test execution focus |
| `refactor` | Code improvement | Full + behavior verify |
| `perf` | Performance | Include benchmarks |
| `chore` | Maintenance | Minimal checks |
| `full` | Complete checks | Everything (default) |

**Options:**
- `--skip-tests` - Skip test execution
- `--skip-rust` - Skip Rust checks
- `--skip-python` - Skip Python checks
- `--message "..."` - Custom commit message
- `--no-fix` - Report only, no auto-fixes
- `--scope <scope>` - Specify commit scope

**Examples:**
```bash
# Documentation update (skip code checks)
/commit-ai docs

# Quick bug fix without tests
/commit-ai fix --skip-tests

# New feature with custom message
/commit-ai feat --message "Add Asian option pricing" --scope models

# Quick format fix
/commit-ai quick

# Full quality check (default)
/commit-ai
```

### `/python-quality-check` - Python Quality Assurance

Run comprehensive Python code quality checks.

**Usage:**
```bash
/python-quality-check
```

Executes:
- ruff format
- ruff check with auto-fix
- mypy type checking
- pytest test suite

### `/rust-quality-check` - Rust Quality Assurance

Run comprehensive Rust code quality checks.

**Usage:**
```bash
/rust-quality-check
```

Executes:
- cargo fmt
- cargo clippy with fixes
- cargo test
- maturin develop

### `/track_implementation` - Implementation Progress Tracking

Track and update implementation progress.

**Usage:**
```bash
/track_implementation
```

### Other Commands

- `/auto-imp` - Automated implementation assistance
- `/python-refactor` - Python code refactoring
- `/rust-refactor` - Rust code refactoring
- `/update-plan-status` - Update plan status
- `/plan` - Plan management
- `/learnings` - Record learnings

## Best Practices

1. **Choose the right commit type**: Use `docs` for documentation-only changes to save time
2. **Use options wisely**: Skip unnecessary checks with `--skip-*` options
3. **Provide context**: Use `--scope` to clarify what part of the codebase is affected
4. **Custom messages**: Use `--message` for more descriptive commit messages

## Command Development

To create a new command:

1. Create a file in `.claude/commands/` with `.md` extension
2. Add YAML frontmatter:
   ```yaml
   ---
   description: Brief description of the command
   argument-hint: "expected arguments format"
   ---
   ```
3. Use `$ARGUMENTS` to access user-provided arguments
4. Follow the existing command structure for consistency

## Notes

- Commands are available to AI assistants only
- All commands follow the project's quality standards
- Commands automatically fix issues when possible
- Critical rules (C001-C014) are always enforced
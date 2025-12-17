#!/usr/bin/env python3
"""Git diff test filter: run only tests for changed files (Level 2.1 optimization)."""
import subprocess
import sys
from pathlib import Path
from typing import Set

def get_changed_files() -> Set[str]:
    """Get list of files changed in current PR."""
    try:
        # Get merge base (common ancestor)
        base = subprocess.check_output(
            ['git', 'merge-base', 'HEAD', 'origin/main'],
            text=True
        ).strip()
        
        # Get diff between base and current branch
        diff_output = subprocess.check_output(
            ['git', 'diff', '--name-only', base, 'HEAD'],
            text=True
        )
        
        return set(diff_output.strip().split('\n'))
    except subprocess.CalledProcessError:
        print("❌ Failed to get git diff. Running all tests.")
        return set()

def map_changed_to_tests(changed_files: Set[str]) -> Set[str]:
    """Map changed files to test modules."""
    test_modules = set()
    
    for file in changed_files:
        if not file:
            continue
        
        # Direct test file changes
        if file.startswith('tests/'):
            test_modules.add(file)
        
        # Map src/ changes to tests/
        elif file.startswith('src/'):
            # src/models.py -> tests/test_models.py
            module_name = Path(file).stem
            test_file = f"tests/test_{module_name}.py"
            test_modules.add(test_file)
        
        # Map ml_training/ changes
        elif file.startswith('ml_training/'):
            module_name = Path(file).stem
            test_file = f"tests/test_{module_name}.py"
            test_modules.add(test_file)
    
    return test_modules

def filter_existing_tests(test_modules: Set[str]) -> Set[str]:
    """Filter to only existing test files."""
    existing = set()
    for test_file in test_modules:
        if Path(test_file).exists():
            existing.add(test_file)
    return existing

def main():
    """Main entry point."""
    print("🔍 Level 2.1: Git Diff Test Filtering...")
    
    # Get changed files
    changed = get_changed_files()
    if not changed:
        print("⚠️  No changes detected or on main branch. Running all tests.")
        print("tests/")
        return
    
    print(f"✓ Changed files: {len(changed)}")
    for f in sorted(changed)[:5]:  # Show first 5
        print(f"  - {f}")
    if len(changed) > 5:
        print(f"  ... and {len(changed) - 5} more")
    
    # Map to test modules
    test_modules = map_changed_to_tests(changed)
    print(f"\n📝 Potentially affected test modules: {len(test_modules)}")
    
    # Filter to existing tests
    existing_tests = filter_existing_tests(test_modules)
    
    if not existing_tests:
        print("⚠️  No corresponding tests found. Running all tests.")
        print("tests/")
        return
    
    print(f"✓ Running {len(existing_tests)} test module(s):")
    for test in sorted(existing_tests):
        print(f"  - {test}")
    
    # Output as pytest arguments
    print("\n" + " ".join(sorted(existing_tests)))

if __name__ == "__main__":
    main()

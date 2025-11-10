#!/usr/bin/env python3
"""
Unified test runner for DIGiDIG project
Runs all unit tests, integration tests, and Playwright tests
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, cwd=None, env=None):
    """Run a command and return the result"""
    print(f"Running: {' '.join(cmd)}")
    if cwd:
        print(f"  in directory: {cwd}")
    result = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Command failed with exit code {result.returncode}")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        return False
    else:
        print("✅ Command succeeded")
        return True

def main():
    """Main test runner"""
    import argparse

    parser = argparse.ArgumentParser(description="DIGiDIG test runner")
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    parser.add_argument("--e2e", action="store_true", help="Run only end-to-end tests")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage")
    parser.add_argument("--playwright", action="store_true", help="Run only Playwright tests")

    args = parser.parse_args()

    # If no specific type requested, run all
    run_all = not any([args.unit, args.integration, args.e2e, args.playwright])

    repo_root = Path(__file__).parent.parent
    os.chdir(repo_root)

    print("🚀 Starting DIGiDIG test suite")
    print("=" * 50)

    # Set up environment
    env = os.environ.copy()
    env['PYTHONPATH'] = str(repo_root)

    success = True

    # Build pytest command
    pytest_cmd = [sys.executable, "-m", "pytest", "-v"]
    if args.coverage:
        pytest_cmd.extend(["--cov=services", "--cov=lib", "--cov-report=html:_test/htmlcov", "--cov-report=term"])

    # 1. Run unit tests for services
    if run_all or args.unit:
        print("\n📋 Running unit tests...")
        unit_test_dirs = [
            "services/admin/tests",
            "services/identity/tests",
            "services/storage/tests",
            "services/smtp/tests",
            "services/imap/tests",
            "services/client/tests",
            "services/apidocs/tests",
            "services/sso/tests",
            "services/mail/tests"
        ]

        for test_dir in unit_test_dirs:
            if Path(test_dir).exists():
                print(f"\n  Running tests in {test_dir}")
                cmd = pytest_cmd + [test_dir, "-m", "not integration and not e2e"]
                if not run_command(cmd, env=env):
                    success = False

    # 2. Run lib tests
    if run_all or args.unit:
        print("\n📋 Running lib tests...")
        lib_test_dirs = [
            "_test/unit"
        ]

        for test_dir in lib_test_dirs:
            if Path(test_dir).exists():
                print(f"\n  Running tests in {test_dir}")
                cmd = pytest_cmd + [test_dir, "-m", "not integration and not e2e"]
                if not run_command(cmd, env=env):
                    success = False

    # 3. Run Playwright tests
    if run_all or args.e2e or args.playwright:
        print("\n🎭 Running Playwright tests...")
        playwright_dir = "_test/playwright"
        if Path(playwright_dir).exists():
            print(f"\n  Running tests in {playwright_dir}")
            cmd = pytest_cmd + [playwright_dir]
            if not run_command(cmd, env=env):
                success = False

    # 4. Run integration tests (if any)
    if run_all or args.integration:
        print("\n🔗 Running integration tests...")
        integration_test_dirs = [
            "services/admin/tests/integration",
            "services/identity/tests/integration",
            "services/storage/tests/integration",
            "services/smtp/tests/integration",
            "services/imap/tests/integration",
            "services/client/tests/integration",
            "services/apidocs/tests/integration",
            "services/sso/tests/integration",
            "services/mail/tests/integration"
        ]

        for test_dir in integration_test_dirs:
            if Path(test_dir).exists():
                print(f"\n  Running tests in {test_dir}")
                cmd = pytest_cmd + [test_dir, "-m", "integration"]
                if not run_command(cmd, env=env):
                    success = False

    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
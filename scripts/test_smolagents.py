#!/usr/bin/env python3
"""
Test script to verify custom smolagents can be imported and used
"""

import os
import sys
from pathlib import Path

# Setup path to use custom smolagents
project_root = Path(__file__).parent.parent
masee_site_packages = project_root / "masee" / "Lib" / "site-packages"

if masee_site_packages.exists():
    sys.path.insert(0, str(masee_site_packages))
    print(f"[OK] Added custom smolagents path: {masee_site_packages}")
else:
    print(f"[WARN] Custom smolagents path not found: {masee_site_packages}")

# Add src to path
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

def test_smolagents_import():
    """Test importing smolagents components."""
    print("\n=== Testing Smolagents Import ===")

    try:
        import smolagents
        print(f"[OK] smolagents imported successfully")
        print(f"  Version: {smolagents.__version__}")
        print(f"  Path: {smolagents.__file__}")
    except ImportError as e:
        print(f"[FAIL] Failed to import smolagents: {e}")
        return False

    # Test specific components used in MASEE
    components_to_test = [
        ('CodeAgent', 'smolagents.CodeAgent'),
        ('ToolCallingAgent', 'smolagents.ToolCallingAgent'),
        ('DuckDuckGoSearchTool', 'smolagents.DuckDuckGoSearchTool'),
        ('LiteLLMModel', 'smolagents.LiteLLMModel'),
        ('load_model', 'smolagents.cli.load_model'),
    ]

    for name, import_path in components_to_test:
        try:
            parts = import_path.split('.')
            module = __import__(parts[0])
            for part in parts[1:]:
                module = getattr(module, part)
            print(f"[OK] {name} imported successfully")
        except (ImportError, AttributeError) as e:
            print(f"[FAIL] Failed to import {name}: {e}")

    return True

def test_masee_imports():
    """Test importing MASEE components."""
    print("\n=== Testing MASEE Imports ===")

    masee_components = [
        ('utils.config', 'Configuration utilities'),
        ('core.experiment', 'Experiment manager'),
        ('core.evaluation', 'Evaluation engine'),
        ('core.agent_factory', 'Agent factory'),
    ]

    for module_name, description in masee_components:
        try:
            __import__(module_name)
            print(f"[OK] {description} imported successfully")
        except ImportError as e:
            print(f"[FAIL] Failed to import {description}: {e}")

def test_agent_creation():
    """Test creating agents with custom smolagents."""
    print("\n=== Testing Agent Creation ===")

    try:
        from smolagents import CodeAgent, LiteLLMModel

        # Create a mock model
        model = LiteLLMModel(model_id="test-model")
        print("[OK] LiteLLMModel created")

        # Create a CodeAgent
        agent = CodeAgent(
            tools=[],
            model=model,
            additional_authorized_imports=['time', 'numpy']
        )
        print("[OK] CodeAgent created successfully")

        return True

    except Exception as e:
        print(f"[FAIL] Failed to create agents: {e}")
        return False

def main():
    """Run all tests."""
    print("MASEE Custom Smolagents Test")
    print("=" * 50)

    tests = [
        test_smolagents_import,
        test_masee_imports,
        test_agent_creation
    ]

    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"[FAIL] Test {test.__name__} crashed: {e}")

    print("\n" + "=" * 50)
    print(f"Results: {passed}/{len(tests)} tests passed")

    if passed == len(tests):
        print("🎉 All tests passed! Custom smolagents is working correctly.")
        return 0
    else:
        print("[WARN] Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
"""Compatibility entry point for the current offline worker regression suite."""
import unittest
from test_form_worker import FormWorkerTests

def test_application_flow():
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(FormWorkerTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    assert result.wasSuccessful(), "Application worker regression checks failed"

if __name__ == '__main__':
    test_application_flow()

import unittest
import logging

logging.basicConfig(level=logging.CRITICAL)

if __name__ == "__main__":
    suite = unittest.TestLoader().discover("tests", pattern="test_*.py")
    unittest.TextTestRunner(verbosity=2).run(suite)

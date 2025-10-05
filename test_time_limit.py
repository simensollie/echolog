#!/usr/bin/env python3
"""
Basic unit tests for time limit functionality.
"""

import unittest
from echolog import EchologRecorder


class TestTimeLimitParsing(unittest.TestCase):
    """Test duration parsing functionality."""
    
    def test_parse_duration_seconds(self):
        """Test parsing various duration formats."""
        # Test integer seconds
        self.assertEqual(EchologRecorder._parse_duration_to_seconds(0), 0)
        self.assertEqual(EchologRecorder._parse_duration_to_seconds(30), 30)
        self.assertEqual(EchologRecorder._parse_duration_to_seconds(3600), 3600)
        
        # Test string seconds
        self.assertEqual(EchologRecorder._parse_duration_to_seconds("0"), 0)
        self.assertEqual(EchologRecorder._parse_duration_to_seconds("30"), 30)
        self.assertEqual(EchologRecorder._parse_duration_to_seconds("90s"), 90)
        self.assertEqual(EchologRecorder._parse_duration_to_seconds("90S"), 90)
        
        # Test minutes
        self.assertEqual(EchologRecorder._parse_duration_to_seconds("1m"), 60)
        self.assertEqual(EchologRecorder._parse_duration_to_seconds("30m"), 1800)
        self.assertEqual(EchologRecorder._parse_duration_to_seconds("30M"), 1800)
        
        # Test hours
        self.assertEqual(EchologRecorder._parse_duration_to_seconds("1h"), 3600)
        self.assertEqual(EchologRecorder._parse_duration_to_seconds("2h"), 7200)
        self.assertEqual(EchologRecorder._parse_duration_to_seconds("2H"), 7200)
        
        # Test edge cases
        self.assertEqual(EchologRecorder._parse_duration_to_seconds(""), 0)
        self.assertEqual(EchologRecorder._parse_duration_to_seconds(None), 0)
        
    def test_parse_duration_errors(self):
        """Test error handling for invalid durations."""
        with self.assertRaises(ValueError):
            EchologRecorder._parse_duration_to_seconds(-1)
        
        with self.assertRaises(ValueError):
            EchologRecorder._parse_duration_to_seconds("-30")
        
        with self.assertRaises(ValueError):
            EchologRecorder._parse_duration_to_seconds("-30s")
        
        with self.assertRaises(ValueError):
            EchologRecorder._parse_duration_to_seconds("invalid")
        
        with self.assertRaises(ValueError):
            EchologRecorder._parse_duration_to_seconds("30x")
        
        with self.assertRaises(ValueError):
            EchologRecorder._parse_duration_to_seconds("abc")


if __name__ == '__main__':
    unittest.main()

# Log Fetcher

![Tests](tests.svg)
![pylint](pylint.svg)
![Coverage](coverage.svg)

Log Fetcher is a utility to find and count IP addresses within log files.

## Overview

This is really a project for me to practice Python fundamentals 😅

This program scans specified files and directories for log files, parses them to find IP addresses, and then reports the frequency of each IP address found across all files.

## How it Works

1.  **File Discovery:** Accepts a list of file paths or glob patterns to search for log files.
2.  **IP Address Extraction:** Reads the content of each file to identify and extract IP addresses.
3.  **Frequency Count:** Aggregates the results and displays a count of how many times each unique IP address was found.

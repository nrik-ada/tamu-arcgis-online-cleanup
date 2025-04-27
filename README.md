# TAMU ArcGIS Online Cleanup Project

## Project Overview
This project provides a Python-based solution for identifying and removing redundant or outdated content from Texas A&M University's ArcGIS Online cloud servers. The goal is to improve organizational efficiency and reduce storage costs by targeting content that has not been modified or accessed in over 8 years and is associated with inactive user accounts.

## Core Functionality
- **User Inactivity Analysis**: Detects users who haven’t logged in within a specified timeframe (e.g., 4+ years).
- **Content Filtering**: Flags content by those inactive users that hasn't been modified or accessed recently (e.g., 8+ years).
- **Report Generation**: Summarizes flagged items and user activity in a structured report.
- **Manual Review and Deletion Confirmation**: Interactive CLI to approve or cancel deletion of selected content.
- **Public Content Review**: Optional tool to evaluate last accessed dates for publicly shared items.

## Workflow Summary
1. Connect to ArcGIS Online using the `arcgis.gis` module.
2. Search and filter users by login history.
3. Cross-reference content ownership with inactive users.
4. Filter content by last modified and/or last viewed date.
5. Output reports and prompt deletion review.
6. Log deletions with metadata for accountability.

## Requirements
- Python 3.8+
- [ArcGIS API for Python](https://developers.arcgis.com/python/)
- pandas
- datetime
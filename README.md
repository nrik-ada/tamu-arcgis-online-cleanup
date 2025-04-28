# Managing Content in Texas A&M University's ArcGIS Online Environment

## Project Motivation

Texas A&M University's ArcGIS Online environment has accumulated thousands of geospatial datasets, web maps, and applications over time. Without proper oversight, much of this content became outdated, unused, or redundant, resulting in increased ESRI cloud storage costs, reduced system performance, and difficulty accessing current resources.

This project developed a Python script to identify inactive users and redundant files, aiming to:
- Improve server organization
- Reduce storage expenses
- Maintain a more efficient ArcGIS Online environment

Additionally, the framework was designed to be replicable for other institutions facing similar challenges.

## Literature Review

The project's methods were based on:
- **ArcGIS API for Python Documentation**: Authentication, metadata retrieval
- **ArcGIS REST API Documentation**: Metadata attributes and error management
- **Pandas Library**: Metadata filtering and manipulation
- **DateTime Library**: Date calculations
- **Getpass Library**: Secure login credentials
- **ESRI Blog**: Configuring Visual Studio Code for ArcGIS Pro's Python environment

The project emphasized industry-supported practices to avoid compatibility issues with future API updates.

## Data

Data sourced from Texas A&M University's ArcGIS Online included:
- **User Metadata**: Username, last login, email, full name
- **Item Metadata**: Title, owner, last modified, last viewed, item type, sharing status, URL

Tools used:
- ArcGIS API for Python (metadata queries)
- Pandas (data processing)
- DateTime (date management)
- Getpass (secure authentication)

The focus was on internally shared content, excluding public items.

## Methods

### Connection and Authentication
- Connected using `GIS()` and `getpass` to securely authenticate and verify administrative permissions.

### Metadata Retrieval
- **`gis.users.search()`**: Retrieved user metadata
- **`gis.content.search()`**: Retrieved content metadata per user (limit 100 items)

### Inactive User Identification
- `getInactiveUsers()`: Identified users inactive for 4+ years or never logged in
- Exported results into a CSV report

### Content Flagging
- `getFlaggedContent()`: Flagged items unmodified for over 8 years or unviewed for over 1 year
- Compiled results into a DataFrame and exported as CSV

### Reporting
- `generateReport()`: Summarized inactive users, flagged items, and saved results as timestamped TXT reports

### Review and Decision Points
- Script prompted users to choose between reporting, canceling, or confirming deletion (no deletions were executed)

## Results

- **280** inactive users identified
- **128** content items flagged based on modification/view criteria
- **No deletions** due to administrative privilege limitations

### Challenges
- Pagination and indexing errors during metadata queries
- LastViewed attribute only available for content created after November 2022
- Learning curve setting up ArcGIS API and Visual Studio Code environment

Despite these challenges, the script effectively extracted and analyzed metadata while safeguarding important datasets.

## Analyzing

Findings included:
- Older content typically consisted of outdated survey maps and project layers.
- Public, unviewed items posed a risk of disseminating obsolete information.
- Many inactive users owned redundant project files.

These insights highlight the need for regular server audits.

## Conclusion

The project successfully:
- Connected securely to ArcGIS Online
- Extracted and analyzed user/item metadata
- Identified inactive users and outdated content
- Generated detailed, reviewable reports

No data deletion was performed without higher administrative approval. 

### Future Improvements
- Resolve pagination and indexing errors
- Archive important older datasets
- Develop a simple graphical interface
- Implement an annual auditing cycle

This project provides a strong foundation for Texas A&M University to maintain a more organized and efficient ArcGIS Online environment.

---

> **Author**: Enrique Buruca  
> **Course**: GEOG 476 - Capstone Project  
> **Date**: 2025-04-28

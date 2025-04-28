from arcgis.gis import GIS
from datetime import datetime, timedelta
import pandas as pd
import getpass

# Connect to ArcGIS Online
gis = GIS("home") # Assumes you are logged in to ArcGIS Online
org_id = gis.properties.id # Get the organization ID
executor = gis.users.me.username if gis.users.me else getpass.getuser() # Get the username of the executor
print(f"Connected to organization: {gis.properties.name} as {executor}")

# Configuration
YEARS_UNVIEWED = 1 # Number of years since last viewed
YEARS_INACTIVE = 4 # Number of years since last login
YEARS_UNMODIFIED = 8 # Number of years since last modified
TODAY = datetime.now() # Current date
CUTOFF_VIEWED = TODAY - timedelta(days=YEARS_UNVIEWED * 365) # Cutoff date for last viewed
CUTOFF_LOGIN = TODAY - timedelta(days=YEARS_INACTIVE * 365) # Cutoff date for last login
CUTOFF_MODIFIED = TODAY - timedelta(days=YEARS_UNMODIFIED * 365) # Cutoff date for last modified
TIMESTAMP = TODAY.strftime('%Y%m%d_%H%M%S') # Timestamp for file names

# Step 1: Identify Inactive Users
def getInactiveUsers():
    all_users = gis.users.search(max_users=1000, sort_field='lastLogin', sort_order='desc') # Get all users in the organization
    inactive_users = [] # List to store inactive users

    for user in all_users: # Get each user
        try: # Check if the user is a member of the organization
            if user.lastLogin == 0: # If lastLogin is 0, the user has never logged in
                last_login_date = datetime(1970, 1, 1)  # Unix epoch
                last_login_str = "Never"
            else: # Convert lastLogin to a datetime object
                last_login_date = datetime.utcfromtimestamp(user.lastLogin / 1000)
                last_login_str = last_login_date.strftime('%Y-%m-%d')

            if last_login_date < CUTOFF_LOGIN: # Check if the user has been inactive for more than the cutoff date
                inactive_users.append({
                    "Username": user.username,
                    "Full Name": getattr(user, "fullName", "N/A"),
                    "Email": getattr(user, "email", "N/A"),
                    "Last Login": last_login_str,
                    "_SortKey": last_login_date
                })
        except Exception as e: # Handle any exceptions that occur while processing users
            print(f"Error processing user {user.username}: {e}")

    inactive_users.sort(key=lambda x: x["_SortKey"]) # Sort inactive users by last login date
    for u in inactive_users: # Remove the sort key from the user dictionary
        del u["_SortKey"]
    
    df_inactive = pd.DataFrame(inactive_users) # Create a DataFrame from the inactive users list
    filename = f"inactive_users_{TIMESTAMP}.csv" # Generate a filename with a timestamp
    df_inactive.to_csv(filename, index=False) # Export the DataFrame to a CSV file
    print(f"Inactive users exported: {filename}") # Print the number of inactive users found
    
    return df_inactive["Username"].tolist(), df_inactive # Return the list of inactive usernames and the DataFrame

# Step 2: Identify Flagged Content
def getFlaggedContent(usernames):
    flagged_content = [] # List to store flagged content
    for username in usernames: # Iterate through each inactive user
        try: # Get the user's content
            user_content = gis.content.search(query=f"owner:{username} AND orgid:{org_id}", max_items=100) # Search for items owned by the user in the organization
            for item in user_content: # Iterate through each item owned by the user
                modified_date = datetime.utcfromtimestamp(item.modified / 1000) # Convert modified date to a datetime object

                if hasattr(item, "lastViewed") and item.lastViewed: # Check if the item has a last viewed date
                    last_viewed_date = datetime.utcfromtimestamp(item.lastViewed / 1000) # Convert last viewed date to a datetime object
                else: # If no last viewed date, set it to a default value
                    last_viewed_date = datetime(1970, 1, 1)

                is_unmodified = modified_date < CUTOFF_MODIFIED # Check if the item has been unmodified for more than the cutoff date
                is_unviewed = last_viewed_date < CUTOFF_VIEWED # Check if the item has been unviewed for more than the cutoff date

                if is_unmodified and is_unviewed: # Check if the item is both unmodified and unviewed
                    reason = "unmodified & unviewed"
                elif is_unmodified: 
                    reason = "unmodified"
                elif is_unviewed:
                    reason = "unviewed"
                else:
                    continue  # Skip items that don't match

                flagged_content.append({ # Append flagged content to the list
                    "Title": item.title,
                    "Owner": item.owner,
                    "Item Type": item.type,
                    "Item ID": item.id,
                    "Last Modified": modified_date.strftime('%Y-%m-%d'),
                    "Last Viewed": last_viewed_date.strftime('%Y-%m-%d'),
                    "URL": item.homepage if hasattr(item, 'homepage') else f"https://www.arcgis.com/home/item.html?id={item.id}",
                    "Reason": reason
                })
        except Exception as e: # Handle any exceptions that occur while processing items
            print(f"Error processing content for user {username}: {e}")

    df_flagged = pd.DataFrame(flagged_content) # Create a DataFrame from the flagged content list
    if not df_flagged.empty: # If there are flagged items, process them
        df_flagged["Last Modified"] = pd.to_datetime(df_flagged["Last Modified"]) # Convert last modified date to a datetime object
        df_flagged["Last Viewed"] = pd.to_datetime(df_flagged["Last Viewed"]) # Convert last viewed date to a datetime object
        df_flagged.sort_values(by="Last Modified", inplace=True) # Sort flagged items by last modified date

        filename = f"flagged_items_{TIMESTAMP}.csv" # Generate a filename with a timestamp
        df_flagged.to_csv(filename, index=False) # Export the DataFrame to a CSV file
        print(f"Flagged content exported: {filename}") 
    return df_flagged # Return the DataFrame of flagged items

# Step 3: Remove Flagged Content
def removeFlaggedContent(df_flagged):
    removed = [] # List to store removed items
    for _, row in df_flagged.iterrows(): # Iterate through each flagged item
        try: # Get the item by ID
            item = gis.content.get(row["Item ID"]) # Get the item by ID
            item.delete() # Delete the item
            removed.append(row) # Append the removed item to the list
            print(f"Deleted: {row['Title']} (ID: {row['Item ID']})") # Print the title and ID of the deleted item
        except Exception as e: # Handle any exceptions that occur while deleting items
            print(f"Failed to delete {row['Item ID']}: {e}")
    return pd.DataFrame(removed)

# Step 4: Generate Report
def generateReport(df_inactive, df_flagged, df_removed):
    report_lines = [ # Generate report lines
        f"GIS Cleanup Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", # Report title
        f"Executor: {executor}", # Executor name
        f"Organization: {gis.properties.name}", # Organization name
        f"\nSummary:", # Summary section
        f"Total Inactive Users: {len(df_inactive)}", # Total inactive users
        f"Total Flagged Content: {len(df_flagged)}", # Total flagged content
        f"Total Removed Items: {len(df_removed)}", # Total removed items
    ]

    if not df_flagged.empty: # If there are flagged items, add them to the report
        report_lines.append("\nFlagged Content:")
        preview = (df_removed if not df_removed.empty else df_flagged).head(10) # Preview of flagged items
        for _, row in preview.iterrows(): # Iterate through each flagged item
            report_lines.append( # Append flagged item details to the report
                f"- {row.get('Title', 'N/A')} ({row.get('Item ID', 'N/A')}) "
                f"by {row.get('Owner', 'N/A')} | Last Modified: {row.get('Last Modified', 'N/A')} | Last Viewed: {row.get('Last Viewed', 'N/A')}"
            )

    else: # If no flagged items, add a message to the report
        report_lines.append("\nNo flagged content found.")

    report_filename = f"cleanup_report_{TIMESTAMP}.txt" # Generate a filename with a timestamp
    with open(report_filename, "w") as file: # Open the report file for writing
        file.write("\n".join(report_lines))

    print(f"Report generated: {report_filename}")

# Step 5: Main Function
inactive_usernames, df_inactive = getInactiveUsers() # Get inactive users and their DataFrame
df_flagged = getFlaggedContent(inactive_usernames) # Get flagged content based on inactive users

if df_flagged.empty: # If no flagged items found, print a message
    print("No flagged content found.")
else: # If flagged items found, print the number of flagged items and options
    print(f"{len(df_flagged)} items flagged for potential removal.")
    print("Options:")
    print("Type 'report'  → Generate a report of flagged items")
    print("Type 'cancel'  → Exit without removing anything")
    print("Type 'confirm' → Proceed to removal of flagged items")

    choice = input("Enter your choice: ").strip().lower() # Get user input for action

    if choice == "report": # If user chooses to generate a report
        generateReport(df_inactive, df_flagged, pd.DataFrame())
    elif choice == "cancel": # If user chooses to cancel
        print("Exiting without changes.")
    elif choice == "confirm": # If user chooses to confirm removal
        confirm = input("Are you sure you want to remove flagged items? (yes/no): ").strip().lower() # Get user confirmation
        if confirm == "yes": # If user confirms removal
            df_removed = removeFlaggedContent(df_flagged)
            generateReport(df_inactive, df_flagged, df_removed)
        else: # If user does not confirm removal
            print("Exiting without changes.")
            generateReport(df_inactive, df_flagged, pd.DataFrame())
    else: # If user input is invalid, print a message
        print("Invalid choice. No actions taken.")

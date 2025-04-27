from arcgis.gis import GIS
from datetime import datetime, timedelta
import pandas as pd
import getpass

# Connect to ArcGIS Online
gis = GIS("home")
org_id = gis.properties.id
executor = gis.users.me.username if gis.users.me else getpass.getuser()
print(f"Connected to organization: {gis.properties.name} as {executor}")

# Configuration
YEARS_UNVIEWED = 1 
YEARS_INACTIVE = 4
YEARS_UNMODIFIED = 8
TODAY = datetime.now()
CUTOFF_VIEWED = TODAY - timedelta(days=YEARS_UNVIEWED * 365)
CUTOFF_LOGIN = TODAY - timedelta(days=YEARS_INACTIVE * 365)
CUTOFF_MODIFIED = TODAY - timedelta(days=YEARS_UNMODIFIED * 365)
TIMESTAMP = TODAY.strftime('%Y%m%d_%H%M%S')

# Step 1: Identify Inactive Users
def getInactiveUsers():
    all_users = gis.users.search(max_users=1000, sort_field='lastLogin', sort_order='desc')
    inactive_users = []

    for user in all_users:
        try:
            if user.lastLogin == 0:
                last_login_date = datetime(1970, 1, 1)  # Unix epoch
                last_login_str = "Never"
            else:
                last_login_date = datetime.utcfromtimestamp(user.lastLogin / 1000)
                last_login_str = last_login_date.strftime('%Y-%m-%d')

            if last_login_date < CUTOFF_LOGIN:
                inactive_users.append({
                    "Username": user.username,
                    "Full Name": getattr(user, "fullName", "N/A"),
                    "Email": getattr(user, "email", "N/A"),
                    "Last Login": last_login_str,
                    "_SortKey": last_login_date
                })
        except Exception as e:
            print(f"Error processing user {user.username}: {e}")

    inactive_users.sort(key=lambda x: x["_SortKey"])
    for u in inactive_users:
        del u["_SortKey"]
    
    df_inactive = pd.DataFrame(inactive_users)
    filename = f"inactive_users_{TIMESTAMP}.csv"
    df_inactive.to_csv(filename, index=False)
    print(f"Inactive users exported: {filename}")
    
    return df_inactive["Username"].tolist(), df_inactive

# Step 2: Identify Flagged Content
def getFlaggedContent(usernames):
    flagged_content = []
    for username in usernames:
        try:
            user_content = gis.content.search(query=f"owner:{username} AND orgid:{org_id}", max_items=100)
            for item in user_content:
                modified_date = datetime.utcfromtimestamp(item.modified / 1000)

                if hasattr(item, "lastViewed") and item.lastViewed:
                    last_viewed_date = datetime.utcfromtimestamp(item.lastViewed / 1000)
                else:
                    last_viewed_date = datetime(1970, 1, 1)

                is_unmodified = modified_date < CUTOFF_MODIFIED
                is_unviewed = last_viewed_date < CUTOFF_VIEWED

                if is_unmodified and is_unviewed:
                    reason = "unmodified & unviewed"
                elif is_unmodified:
                    reason = "unmodified"
                elif is_unviewed:
                    reason = "unviewed"
                else:
                    continue  # Skip items that don't match

                flagged_content.append({
                    "Title": item.title,
                    "Owner": item.owner,
                    "Item Type": item.type,
                    "Item ID": item.id,
                    "Last Modified": modified_date.strftime('%Y-%m-%d'),
                    "Last Viewed": last_viewed_date.strftime('%Y-%m-%d'),
                    "URL": item.homepage if hasattr(item, 'homepage') else f"https://www.arcgis.com/home/item.html?id={item.id}",
                    "Reason": reason
                })
        except Exception as e:
            print(f"Error processing content for user {username}: {e}")

    df_flagged = pd.DataFrame(flagged_content)
    if not df_flagged.empty:
        df_flagged["Last Modified"] = pd.to_datetime(df_flagged["Last Modified"])
        df_flagged["Last Viewed"] = pd.to_datetime(df_flagged["Last Viewed"])
        df_flagged.sort_values(by="Last Modified", inplace=True)

        filename = f"flagged_items_{TIMESTAMP}.csv"
        df_flagged.to_csv(filename, index=False)
        print(f"Flagged content exported: {filename}")
    return df_flagged

# Step 3: Remove Flagged Content
def remove_flagged_content(df_flagged):
    removed = []
    for _, row in df_flagged.iterrows():
        try:
            item = gis.content.get(row["Item ID"])
            item.delete()
            removed.append(row)
            print(f"Deleted: {row['Title']} (ID: {row['Item ID']})")
        except Exception as e:
            print(f"Failed to delete {row['Item ID']}: {e}")
    return pd.DataFrame(removed)

# Step 4: Generate Report
def generate_report(df_inactive, df_flagged, df_removed):
    report_lines = [
        f"GIS Cleanup Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Executor: {executor}",
        f"Organization: {gis.properties.name}",
        f"\nSummary:",
        f"Total Inactive Users: {len(df_inactive)}",
        f"Total Flagged Content: {len(df_flagged)}",
        f"Total Removed Items: {len(df_removed)}",
    ]

    if not df_flagged.empty:
        report_lines.append("\nFlagged Content:")
        preview = (df_removed if not df_removed.empty else df_flagged).head(10)
        for _, row in preview.iterrows():
            report_lines.append(
                f"- {row.get('Title', 'N/A')} ({row.get('Item ID', 'N/A')}) "
                f"by {row.get('Owner', 'N/A')} | Last Modified: {row.get('Last Modified', 'N/A')} | Last Viewed: {row.get('Last Viewed', 'N/A')}"
            )

    else:
        report_lines.append("\nNo flagged content found.")

    report_filename = f"cleanup_report_{TIMESTAMP}.txt"
    with open(report_filename, "w") as file:
        file.write("\n".join(report_lines))

    print(f"Report generated: {report_filename}")

# Step 5: Main Function
inactive_usernames, df_inactive = getInactiveUsers()
df_flagged = getFlaggedContent(inactive_usernames)

if df_flagged.empty:
    print("No flagged content found.")
else:
    print(f"{len(df_flagged)} items flagged for potential removal.")
    print("Options:")
    print("Type 'report'  → Generate a report of flagged items")
    print("Type 'cancel'  → Exit without removing anything")
    print("Type 'confirm' → Proceed to removal of flagged items")

    choice = input("Enter your choice: ").strip().lower()

    if choice == "report":
        generate_report(df_inactive, df_flagged, pd.DataFrame())
    elif choice == "cancel":
        print("Exiting without changes.")
    elif choice == "confirm":
        confirm = input("Are you sure you want to remove flagged items? (yes/no): ").strip().lower()
        if confirm == "yes":
            df_removed = remove_flagged_content(df_flagged)
            generate_report(df_inactive, df_flagged, df_removed)
        else:
            print("Exiting without changes.")
            generate_report(df_inactive, df_flagged, pd.DataFrame())
    else:
        print("Invalid choice. No actions taken.")

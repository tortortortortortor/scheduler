import pulp

# Initialize the problem
schedule_problem = pulp.LpProblem("Healthcare_Scheduling", pulp.LpMaximize)

# Constants
num_weeks = 52
days_per_week = 7
total_hours_in_period = num_weeks * days_per_week * 24  # Total hours in 8 weeks

# Staff information
staff_info = {
    "Hildur ": {"shift": "D1", "work_percentage": 100, "pref_consecutive_days": 3, "overtime_allowance_hrs": 20},
    "Sandra ": {"shift": "D1", "work_percentage": 100, "pref_consecutive_days": 3, "overtime_allowance_hrs": 20},
    "Hege   ": {"shift": "D1", "work_percentage": 100, "pref_consecutive_days": 7, "overtime_allowance_hrs": 20},
    "Nina   ": {"shift": "D2", "work_percentage": 100, "pref_consecutive_days": 3, "overtime_allowance_hrs": 20},
    "Salmir ": {"shift": "Mx", "work_percentage": 100, "pref_consecutive_days": 4, "overtime_allowance_hrs": 20},
    "AnnK.  ": {"shift": "D2", "work_percentage": 100, "pref_consecutive_days": 5, "overtime_allowance_hrs": 20},
    "Lillian": {"shift": "D2", "work_percentage": 100, "pref_consecutive_days": 7, "overtime_allowance_hrs": 20},
    "Siv I. ": {"shift": "Mx", "work_percentage": 83, "pref_consecutive_days": 3, "overtime_allowance_hrs": 20},
    "Kristi ": {"shift": "Mx", "work_percentage": 80, "pref_consecutive_days": 3, "overtime_allowance_hrs": 20},
    "Erna. 🌒": {"shift": "Night", "work_percentage": 66, "pref_consecutive_days": 4, "overtime_allowance_hrs": 150},
    "Liv J 🌒": {"shift": "Night", "work_percentage": 66, "pref_consecutive_days": 4, "overtime_allowance_hrs": 150},
    "Siliva🌒": {"shift": "Night", "work_percentage": 66, "pref_consecutive_days": 4, "overtime_allowance_hrs": 150},
}

# Define work hours for each shift type
shift_hours = {
    "D1": 13,  # 0700 to 2000
    "D2": 13,  # 0800 to 2100
    "Mx": 12,  # 1000 to 2200
    "Night": 10 # 2100 to 0700
}

# Constants
hours_per_year_full_time = 1622  # Maximum hours in a year for a 100% position

# Dictionary to hold the shift variables for each staff member and shift type
shifts = {(staff_member, week, day, shift_type): pulp.LpVariable(f"shift_{staff_member}_{week}_{day}_{shift_type}", cat='Binary')
          for staff_member in staff_info
          for week in range(num_weeks)
          for day in range(days_per_week)
          for shift_type in shift_hours}

# Add constraints and objective function components
total_work_hours_constraints = []
objective_function_components = []

isolated_day_penalty_weight = 100
fairness_penalty_weight = 1


# Additional binary variables for isolated days
isolated_work_vars = {}
isolated_off_vars = {}


for staff_member in staff_info:
    for week in range(num_weeks):
        for day in range(days_per_week):
            isolated_work_var = pulp.LpVariable(f"isolated_work_{staff_member}_{week}_{day}", cat='Binary')
            isolated_off_var = pulp.LpVariable(f"isolated_off_{staff_member}_{week}_{day}", cat='Binary')
            isolated_work_vars[(staff_member, week, day)] = isolated_work_var
            isolated_off_vars[(staff_member, week, day)] = isolated_off_var


            # Constraints for isolated working day
            if day == 0:  # First day of the week
                schedule_problem += isolated_work_var >= shifts[staff_member, week, day, staff_info[staff_member]["shift"]] - (shifts[staff_member, week, day + 1, staff_info[staff_member]["shift"]] if day + 1 < days_per_week else 0)
            elif day == days_per_week - 1:  # Last day of the week
                schedule_problem += isolated_work_var >= shifts[staff_member, week, day, staff_info[staff_member]["shift"]] - shifts[staff_member, week, day - 1, staff_info[staff_member]["shift"]]
            else:  # Other days
                schedule_problem += isolated_work_var >= shifts[staff_member, week, day, staff_info[staff_member]["shift"]] - (shifts[staff_member, week, day - 1, staff_info[staff_member]["shift"]] + shifts[staff_member, week, day + 1, staff_info[staff_member]["shift"]])

            # Constraints for isolated off day
            if day == 0:
                schedule_problem += isolated_off_var >= (1 - shifts[staff_member, week, day, staff_info[staff_member]["shift"]]) - (1 - shifts[staff_member, week, day + 1, staff_info[staff_member]["shift"]] if day + 1 < days_per_week else 0)
            elif day == days_per_week - 1:
                schedule_problem += isolated_off_var >= (1 - shifts[staff_member, week, day, staff_info[staff_member]["shift"]]) - (1 - shifts[staff_member, week, day - 1, staff_info[staff_member]["shift"]])
            else:
                schedule_problem += isolated_off_var >= (1 - shifts[staff_member, week, day, staff_info[staff_member]["shift"]]) - ((1 - shifts[staff_member, week, day - 1, staff_info[staff_member]["shift"]]) + (1 - shifts[staff_member, week, day + 1, staff_info[staff_member]["shift"]]))

            # Add penalty for isolated days to the objective function
            objective_function_components.append(-isolated_day_penalty_weight * (isolated_work_vars[(staff_member, week, day)] + isolated_off_vars[(staff_member, week, day)]))

# Additional variables for tracking weekends worked
weekend_work_vars = {(staff_member, week): pulp.LpVariable(f"weekend_work_{staff_member}_{week}", cat='Binary')
                     for staff_member in staff_info
                     for week in range(num_weeks)}

# Count weekends worked
weekends_worked = {staff_member: pulp.lpSum(weekend_work_vars[staff_member, week] for week in range(num_weeks))
                   for staff_member in staff_info}

# Apply constraints for weekend work variables
for staff_member in staff_info:
    for week in range(num_weeks):
        # Assuming weekend is Saturday (5) and Sunday (6)
        schedule_problem += weekend_work_vars[staff_member, week] >= shifts[staff_member, week, 5, staff_info[staff_member]["shift"]]
        schedule_problem += weekend_work_vars[staff_member, week] >= shifts[staff_member, week, 6, staff_info[staff_member]["shift"]]

# Fairness penalty weight
  # Adjust this based on the scale of other components in your objective function - see slider

# Apply fairness penalty
max_weekends_worked = pulp.lpSum([weekends_worked[staff_member] for staff_member in staff_info])
min_weekends_worked = pulp.lpSum([weekends_worked[staff_member] for staff_member in staff_info])

fairness_penalty = max_weekends_worked - min_weekends_worked
objective_function_components.append(-fairness_penalty_weight * fairness_penalty)

# Add all components to the objective function
schedule_problem += pulp.lpSum(objective_function_components)

# Constants
MAX_HOURS_FULL_TIME = 1622
TOLERANCE = 0.05  # 5%

# Additional constants for night shift staff
MAX_HOURS_NIGHT_SHIFT = 2000  # Increased maximum hours for night shift workers
NIGHT_SHIFT_TOLERANCE = 0.20  # Increased tolerance for night shift workers

# Lower and upper bounds for full-time
lower_bound_full_time = MAX_HOURS_FULL_TIME * (1 - TOLERANCE)
upper_bound_full_time = MAX_HOURS_FULL_TIME * (1 + TOLERANCE)

# Lower and upper bounds for night shift full-time
lower_bound_night_shift = MAX_HOURS_NIGHT_SHIFT * (1 - NIGHT_SHIFT_TOLERANCE)
upper_bound_night_shift = MAX_HOURS_NIGHT_SHIFT * (1 + NIGHT_SHIFT_TOLERANCE)

# Constraints
for staff_member, info in staff_info.items():
    work_percentage = info["work_percentage"] / 100

    # Determine max and min hours based on shift type
    if info["shift"] == "Night":
        max_hours = upper_bound_night_shift * work_percentage
        min_hours = lower_bound_night_shift * work_percentage
    else:
        max_hours = upper_bound_full_time * work_percentage
        min_hours = lower_bound_full_time * work_percentage

    staff_hours = pulp.lpSum(shifts[staff_member, week, day, shift_type] * shift_hours[shift_type]
                             for week in range(num_weeks)
                             for day in range(days_per_week)
                             for shift_type in shift_hours if shift_type in info["shift"])

    # Apply constraints for maximum and minimum hours
    schedule_problem += (staff_hours <= max_hours)
    schedule_problem += (staff_hours >= min_hours)

    # Enforce that non-night workers cannot be assigned to night shifts
    if info["shift"] != "Night":
        for week in range(num_weeks):
            for day in range(days_per_week):
                schedule_problem += (shifts[staff_member, week, day, "Night"] == 0)

    # Enforce that night workers cannot be assigned to day shifts
    else:
        for week in range(num_weeks):
            for day in range(days_per_week):
                for day_shift in ["D1", "D2", "Mx"]:
                    schedule_problem += (shifts[staff_member, week, day, day_shift] == 0)

                    # Constraint: Ensure exactly one of each shift type per day - Confirmed solid
for week in range(num_weeks):
    for day in range(days_per_week):
        # Ensure exactly one D1 shift per day
        schedule_problem += pulp.lpSum(shifts[staff_member, week, day, "D1"] for staff_member in staff_info) == 1, f"One_D1_Shift_Week{week}_Day{day}"

        # Ensure exactly one D2 shift per day
        schedule_problem += pulp.lpSum(shifts[staff_member, week, day, "D2"] for staff_member in staff_info) == 1, f"One_D2_Shift_Week{week}_Day{day}"

        # Ensure exactly one Mx or M3 shift per day (not both)
        schedule_problem += pulp.lpSum(shifts[staff_member, week, day, "Mx"] for staff_member in staff_info) == 1, f"One_Mx_Shift_Week{week}_Day{day}"

        # Ensure exactly one Night shift per day
        schedule_problem += pulp.lpSum(shifts[staff_member, week, day, "Night"] for staff_member in staff_info) == 1, f"One_Night_Shift_Week{week}_Day{day}"

# 1. Nurses work no more than three days in any 7-day period
for staff_member, info in staff_info.items():
    if info["shift"] == "D1":
        for week in range(num_weeks):
            for start_day in range(days_per_week):
                end_day = min(start_day + 7, days_per_week)
                schedule_problem += pulp.lpSum(shifts[staff_member, week, day, "D1"] 
                                               for day in range(start_day, end_day)) <= 3

# Constraint: No staff member works more than seven consecutive days
for staff_member in staff_info.keys():
    for week in range(num_weeks):
        for start_day in range(days_per_week):
            # Calculate the end day and adjust for week transition
            end_day = start_day + 7
            if end_day > days_per_week:
                # Window spans two weeks
                days_in_current_week = days_per_week - start_day
                days_in_next_week = end_day - days_per_week
                next_week = (week + 1) % num_weeks

                # Sum shifts across the 7-day window spanning two weeks
                shift_sum = pulp.lpSum(shifts[staff_member, week, day, shift_type] 
                                       for day in range(start_day, days_per_week)
                                       for shift_type in shift_hours) + \
                            pulp.lpSum(shifts[staff_member, next_week, day, shift_type] 
                                       for day in range(days_in_next_week)
                                       for shift_type in shift_hours)
            else:
                # Window within a single week
                shift_sum = pulp.lpSum(shifts[staff_member, week, day, shift_type] 
                                       for day in range(start_day, end_day)
                                       for shift_type in shift_hours)

            # Apply the constraint
            schedule_problem += (shift_sum <= 7, f"Max_7_Consecutive_Days_{staff_member}_Week{week}_StartDay{start_day}")

# 2. Work at least one weekend per month for nurses
# Assuming 4 weeks per month, and week starts on Monday
for staff_member, info in staff_info.items():
    if info["shift"] == "D1":
        for month in range(num_weeks // 4):
            schedule_problem += pulp.lpSum(shifts[staff_member, month * 4 + week, 5, "D1"] + 
                                           shifts[staff_member, month * 4 + week, 6, "D1"]
                                           for week in range(4)) >= 1, f"Weekend_Work_{staff_member}_Month{month + 1}"

# Add all constraints to the problem
for constraint in total_work_hours_constraints:
    schedule_problem += constraint

# Define the objective function to maximize total work hours
schedule_problem += pulp.lpSum(objective_function_components)

# Solve the problem with chosen solver
solver = pulp.PULP_CBC_CMD(msg=1, threads=8, maxSeconds=300)

schedule_problem.solve(solver)

# Constants
MAX_HOURS_FULL_TIME = 1622  # Maximum hours in a year for a 100% position

# Check the status of the solution and print the schedule
if schedule_problem.status == pulp.LpStatusOptimal:
    print("An optimal solution was found.\n")

    total_hours_all_staff = 0
    overworked_staff = []
    underworked_staff = []

    # Calculate and print the hours worked per week per employee
    for staff_member, info in staff_info.items():
        total_hours_staff_member = 0
        expected_hours = (info["work_percentage"] / 100) * MAX_HOURS_FULL_TIME
        print(f"Hours worked by {staff_member} (Expected: {expected_hours}):")

        for week in range(num_weeks):
            weekly_hours = sum(pulp.value(shifts[staff_member, week, day, shift_type]) * shift_hours[shift_type]
                               for day in range(days_per_week)
                               for shift_type in shift_hours)
            total_hours_staff_member += weekly_hours

        discrepancy = total_hours_staff_member - expected_hours
        if discrepancy > 0:
            print(f"Total hours worked by {staff_member}: {total_hours_staff_member} hours (Needs {discrepancy} fewer hours)\n")
            overworked_staff.append((staff_member, info["shift"], discrepancy))
        else:
            print(f"Total hours worked by {staff_member}: {total_hours_staff_member} hours (Needs {-discrepancy} more hours)\n")
            underworked_staff.append((staff_member, info["shift"], -discrepancy))
        total_hours_all_staff += total_hours_staff_member

    print(f"Total hours worked by all staff: {total_hours_all_staff} hours\n")

    # Suggest swaps
    print("Suggested Swaps:")
    for overworked in overworked_staff:
        for underworked in underworked_staff:
            if overworked[1] == underworked[1]:  # Matching shift types
                print(f"{overworked[0]} (Overworked by {overworked[2]} hours) can swap with {underworked[0]} (Underworked by {underworked[2]} hours)")
else:
    print("No optimal solution found. Please check the problem constraints.")

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import datetime


# Start date of the schedule
start_date = datetime.datetime(2024, 1, 1)

# Prepare the header
header = ['Staff Member', 'Shift', 'Total Hours']
dates = [start_date + datetime.timedelta(days=week * days_per_week + day) for week in range(num_weeks) for day in range(days_per_week)]
date_headers = [date.strftime('%Y-%m-%d') for date in dates]
header.extend(date_headers)

# Prepare the data for each staff member
data = []
for staff_member, info in staff_info.items():
    # Calculate total hours worked
    total_hours = sum(pulp.value(shifts[staff_member, week, day, shift_type]) * shift_hours[shift_type]
                      for week in range(num_weeks)
                      for day in range(days_per_week)
                      for shift_type in shift_hours)
    # Prepare row data
    row = [staff_member, info['shift'], total_hours]
    for week in range(num_weeks):
        for day in range(days_per_week):
            shift_worked = next((shift_type for shift_type in shift_hours if pulp.value(shifts[staff_member, week, day, shift_type]) == 1), 'Off')
            row.append(shift_worked)
    data.append(row)

# Create a DataFrame
df = pd.DataFrame(data, columns=header)

# Now you can interact with this DataFrame in Deepnote
print(df.head())  # For example, print the first few rows

# Assuming 'df' is your existing DataFrame

# Melt the DataFrame to long format
df_long = df.melt(id_vars=['Staff Member', 'Shift', 'Total Hours'], 
                  var_name='Date', 
                  value_name='Shift Worked')

# Filter out 'Off' days for clarity in the plot
df_long = df_long[df_long['Shift Worked'] != 'Off']

df_pivot = df_long.pivot(index='Staff Member', columns='Date', values='Shift Worked')

# Reset the index to make 'Staff Member' a column again
df_pivot.reset_index(inplace=True)

# Fill NaN values with an empty string or a placeholder if needed
df_pivot.fillna('', inplace=True)

df_pivot.to_excel("Staff_Shift_Schedule_2024.xlsx", index=False)


from healthcare_schedule import HealthcareSchedule
# Import other necessary modules or constants

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

print("Running the healthcare scheduling problem...")

def main():
    schedule = HealthcareSchedule(num_weeks=52, days_per_week=7, staff_info=staff_info, shift_hours=shift_hours)
    schedule.add_constraints()
    schedule.set_objective()
    schedule.solve()
    schedule.generate_report()

if __name__ == "__main__":
    main()
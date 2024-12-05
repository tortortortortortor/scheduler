# Healthcare Scheduling

The HealthcareSchedule class is a Python-based optimization tool designed for healthcare staff scheduling. It leverages the PuLP library to create a Linear Programming (LP) model that assigns shifts to staff members while satisfying a variety of constraints and optimizing for fairness and efficiency. The class also includes methods for analyzing, visualizing, and exporting the generated schedules.

# Constraints

Constraints are modular and designed to be customizable. These allow the user to fine-tune the schedule by adjusting penalty weights, thresholds, or specific rules.

## How Constraints Enable Customization

1.	Penalty Weights:
	•	Constraints like isolated days, shift distribution, and weekend fairness use penalty weights. Adjusting these weights alters the priority of the corresponding rule in the optimization process.
2.	Flexible Thresholds:
	•	Many constraints accept parameters such as max_days_in_7, day_shift_tolerance, and night_shift_tolerance. These can be modified to reflect organizational policies.
3.	Binary Variables:
	•	Binary decision variables (isolated_work_var, weekend_work_var) allow fine-grained control over specific scheduling nuances.
4.	Role-Specific Rules:
	•	Constraints like _add_role_specific_shift_constraints ensure that staff members are only assigned to roles they are trained for.

## Setup

use python enviornment manager to start a terminal with correct env

run
```bash
python3 main.py
```
you might have to install a bunch of thing, noone really knows how package management works in python.

Define worker preferences

# Staff information
```json
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
```


<img width="710" alt="image" src="https://github.com/user-attachments/assets/4bbf19af-c6d3-45dc-bc4a-a92e99d9e556">
<img width="561" alt="image" src="https://github.com/user-attachments/assets/bed5544b-178f-474a-aca5-a6a1f03a3c6d">
<img width="1388" alt="image" src="https://github.com/user-attachments/assets/c8d60942-8bac-46e8-9350-d49ad80d9889">
<img width="1408" alt="image" src="https://github.com/user-attachments/assets/e44b6008-06c3-40ee-a46e-10e98df00f37">

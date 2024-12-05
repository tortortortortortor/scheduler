# Healthcare Scheduling

This project aims to solve a healthcare scheduling problem using linear programming.

## Setup

use python enviornment manager to start a terminal with correct env

run

python3 main.py

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

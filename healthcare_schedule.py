import pulp
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import datetime

class HealthcareSchedule:
    def __init__(self, num_weeks, days_per_week, staff_info, shift_hours):
        self.num_weeks = num_weeks
        self.days_per_week = days_per_week
        self.staff_info = staff_info
        self.shift_hours = shift_hours
        self.problem = pulp.LpProblem("Healthcare_Scheduling", pulp.LpMaximize)
        self.shifts = None
        self.objective_function_components = []  # Initialize the list to store objective function components
        self.MAX_HOURS_FULL_TIME = 1622  # Maximum hours for full time staff per year
        self.initialize_variables()

    def initialize_variables(self):
        # Create LP variables
        self.shifts = {
            (staff_member, week, day, shift_type): pulp.LpVariable(
                f"shift_{staff_member}_{week}_{day}_{shift_type}", cat='Binary'
            )
            for staff_member in self.staff_info
            for week in range(self.num_weeks)
            for day in range(self.days_per_week)
            for shift_type in self.shift_hours
        }

    def add_constraints(self):
        # Add various constraints
        self._add_work_hours_constraints()
        self._add_isolated_day_constraints()
        self._add_weekend_work_constraints()

        # ... other constraints
        self._compile_objective_function()


    def _add_work_hours_constraints(self):
        # Constants
        MAX_HOURS_FULL_TIME = 1622
        TOLERANCE = 0.05  # 5%
        MAX_HOURS_NIGHT_SHIFT = 2000  # Increased maximum hours for night shift workers
        NIGHT_SHIFT_TOLERANCE = 0.20  # Increased tolerance for night shift workers

        # Lower and upper bounds for full-time and night shift full-time
        lower_bound_full_time = MAX_HOURS_FULL_TIME * (1 - TOLERANCE)
        upper_bound_full_time = MAX_HOURS_FULL_TIME * (1 + TOLERANCE)
        lower_bound_night_shift = MAX_HOURS_NIGHT_SHIFT * (1 - NIGHT_SHIFT_TOLERANCE)
        upper_bound_night_shift = MAX_HOURS_NIGHT_SHIFT * (1 + NIGHT_SHIFT_TOLERANCE)

        for staff_member, info in self.staff_info.items():
            work_percentage = info["work_percentage"] / 100

            # Determine max and min hours based on shift type
            if info["shift"] == "Night":
                max_hours = upper_bound_night_shift * work_percentage
                min_hours = lower_bound_night_shift * work_percentage
            else:
                max_hours = upper_bound_full_time * work_percentage
                min_hours = lower_bound_full_time * work_percentage

            # Calculate total hours for each staff member
            staff_hours = pulp.lpSum(self.shifts[staff_member, week, day, shift_type] * self.shift_hours[shift_type]
                                     for week in range(self.num_weeks)
                                     for day in range(self.days_per_week)
                                     for shift_type in self.shift_hours if shift_type in info["shift"])

            # Apply constraints for maximum and minimum hours
            self.problem += (staff_hours <= max_hours)
            self.problem += (staff_hours >= min_hours)

            # Enforce that non-night workers cannot be assigned to night shifts
            if info["shift"] != "Night":
                for week in range(self.num_weeks):
                    for day in range(self.days_per_week):
                        self.problem += (self.shifts[staff_member, week, day, "Night"] == 0)

            # Enforce that night workers cannot be assigned to day shifts
            else:
                for week in range(self.num_weeks):
                    for day in range(self.days_per_week):
                        for day_shift in ["D1", "D2", "Mx"]:
                            self.problem += (self.shifts[staff_member, week, day, day_shift] == 0)

    def _add_isolated_day_constraints(self):
        isolated_day_penalty_weight = 100
        self.isolated_work_vars = {}
        self.isolated_off_vars = {}

        for staff_member in self.staff_info:
            for week in range(self.num_weeks):
                for day in range(self.days_per_week):
                    self._add_single_isolated_day_constraint(staff_member, week, day, isolated_day_penalty_weight)

    def _add_single_isolated_day_constraint(self, staff_member, week, day, penalty_weight):
        # Create variables for isolated work and off days
        isolated_work_var = pulp.LpVariable(f"isolated_work_{staff_member}_{week}_{day}", cat='Binary')
        isolated_off_var = pulp.LpVariable(f"isolated_off_{staff_member}_{week}_{day}", cat='Binary')
        self.isolated_work_vars[(staff_member, week, day)] = isolated_work_var
        self.isolated_off_vars[(staff_member, week, day)] = isolated_off_var

        # Constraint for isolated working day
        if day == 0:  # First day of the week
            self.problem += isolated_work_var >= self.shifts[staff_member, week, day, self.staff_info[staff_member]["shift"]] - (self.shifts[staff_member, week, day + 1, self.staff_info[staff_member]["shift"]] if day + 1 < self.days_per_week else 0)
        elif day == self.days_per_week - 1:  # Last day of the week
            self.problem += isolated_work_var >= self.shifts[staff_member, week, day, self.staff_info[staff_member]["shift"]] - self.shifts[staff_member, week, day - 1, self.staff_info[staff_member]["shift"]]
        else:  # Other days
            self.problem += isolated_work_var >= self.shifts[staff_member, week, day, self.staff_info[staff_member]["shift"]] - (self.shifts[staff_member, week, day - 1, self.staff_info[staff_member]["shift"]] + self.shifts[staff_member, week, day + 1, self.staff_info[staff_member]["shift"]])

        # Constraint for isolated off day
        if day == 0:
            self.problem += isolated_off_var >= (1 - self.shifts[staff_member, week, day, self.staff_info[staff_member]["shift"]]) - (1 - self.shifts[staff_member, week, day + 1, self.staff_info[staff_member]["shift"]] if day + 1 < self.days_per_week else 0)
        elif day == self.days_per_week - 1:
            self.problem += isolated_off_var >= (1 - self.shifts[staff_member, week, day, self.staff_info[staff_member]["shift"]]) - (1 - self.shifts[staff_member, week, day - 1, self.staff_info[staff_member]["shift"]])
        else:
            self.problem += isolated_off_var >= (1 - self.shifts[staff_member, week, day, self.staff_info[staff_member]["shift"]]) - ((1 - self.shifts[staff_member, week, day - 1, self.staff_info[staff_member]["shift"]]) + (1 - self.shifts[staff_member, week, day + 1, self.staff_info[staff_member]["shift"]]))

        # Add penalty for isolated days to the objective function
        self.objective_function_components.append(-penalty_weight * (isolated_work_var + isolated_off_var))

    def _add_weekend_work_constraints(self):
        # Initialize dictionary for weekend work variables
        self.weekend_work_vars = {}

        # Loop through staff members and weeks to create weekend work variables
        for staff_member in self.staff_info:
            for week in range(self.num_weeks):
                self._add_single_weekend_work_constraint(staff_member, week)

    def _add_single_weekend_work_constraint(self, staff_member, week):
        # Create a binary variable to track if a staff member works on the weekend
        weekend_work_var = pulp.LpVariable(f"weekend_work_{staff_member}_{week}", cat='Binary')
        self.weekend_work_vars[(staff_member, week)] = weekend_work_var

        # Add constraints for weekend work
        # Assuming weekend is Saturday (5) and Sunday (6)
        self.problem += weekend_work_var >= self.shifts[staff_member, week, 5, self.staff_info[staff_member]["shift"]]
        self.problem += weekend_work_var >= self.shifts[staff_member, week, 6, self.staff_info[staff_member]["shift"]]


    def set_objective(self):
        # Set the objective function
        self.problem += pulp.lpSum(self.objective_function_components), "Total Objective Function"

    def solve(self):
        # Solve the LP problem and handle the solution
        # Use PuLP's solver to solve the problem
        solver = pulp.PULP_CBC_CMD(msg=1, threads=8, maxSeconds=300)
        self.problem.solve(solver)

        # Check if an optimal solution was found
        if self.problem.status == pulp.LpStatusOptimal:
            print("An optimal solution was found.")
        else:
            print("No optimal solution found. Please check the problem constraints.")

    def generate_report(self):
        # Check the status of the solution and print the schedule
        if self.problem.status == pulp.LpStatusOptimal:
            print("An optimal solution was found.\n")
            # Generate textual report as shown in your example
         #   self.debugVariables()
            self.generate_textreport()
            self.print_schedule()
        else:
            print("No optimal solution found. Will not generate a report.")

    def print_schedule(self):
            # Check the status of the solution and print the schedule
            if self.problem.status == pulp.LpStatusOptimal:
                for week in range(self.num_weeks):
                    print(f"Week {week + 1}:")
                    for day in range(self.days_per_week):
                        day_schedule = []
                        for shift_type in self.shift_hours:
                            # List of staff members working this shift on this day
                            working_staff = [staff_member for staff_member in self.staff_info if pulp.value(self.shifts[staff_member, week, day, shift_type]) == 1]
                            
                            # Check for non-night workers assigned to night shifts
                            if shift_type == "Night":
                                non_night_workers = [staff_member for staff_member in working_staff if self.staff_info[staff_member]["shift"] != "Night"]
                                if non_night_workers:
                                    print(f"  Error: Non-night workers assigned to night shift: {', '.join(non_night_workers)}")

                            if working_staff:
                                day_schedule.append(f"{', '.join(working_staff)} {shift_type}")
                        print(f"  Day {day + 1}: {' | '.join(day_schedule)}")
                    print()  # Adds an empty line for better readability between weeks
            else:
                print("No optimal solution found. Please check the problem constraints.")

    def debugVariables(self):
        for variable in self.problem.variables():
            print(f"{variable.name} = {variable.varValue}")

    def generate_textreport(self):
        # Check the status of the solution and print the schedule
        if self.problem.status == pulp.LpStatusOptimal:
            print("An optimal solution was found.\n")

            total_hours_all_staff = 0
            overworked_staff = []
            underworked_staff = []

            # Calculate and print the hours worked per week per employee
            for staff_member, info in self.staff_info.items():
                total_hours_staff_member = 0
                expected_hours = (info['work_percentage'] / 100) * self.MAX_HOURS_FULL_TIME
                print(f"Hours worked by {staff_member} (Expected: {expected_hours}):")

                for week in range(self.num_weeks):
                    weekly_hours = 0  # Initialize weekly_hours here before it's used
                    for day in range(self.days_per_week):
                        for shift_type in self.shift_hours:
                            shift_value = pulp.value(self.shifts[staff_member, week, day, shift_type])
                            if shift_value is not None:  # Check if the shift_value is not None
                                weekly_hours += shift_value * self.shift_hours[shift_type]
                    total_hours_staff_member += weekly_hours

                discrepancy = total_hours_staff_member - expected_hours
                if discrepancy > 0:
                    print(f"Total hours worked by {staff_member}: {total_hours_staff_member} hours (Needs {discrepancy} fewer hours)\n")
                    overworked_staff.append((staff_member, discrepancy))
                else:
                    print(f"Total hours worked by {staff_member}: {total_hours_staff_member} hours (Needs {-discrepancy} more hours)\n")
                    underworked_staff.append((staff_member, -discrepancy))

                total_hours_all_staff += total_hours_staff_member

            print(f"Total hours worked by all staff: {total_hours_all_staff} hours\n")

            # Suggest swaps
            print("Suggested Swaps:")
            for overworked in overworked_staff:
                for underworked in underworked_staff:
                    print(f"{overworked[0]} (Overworked by {overworked[1]} hours) can swap with {underworked[0]} (Underworked by {underworked[1]} hours)")
        else:
            print("No optimal solution found. Please check the problem constraints.")


    def plot_schedule(self):
        # Assuming we have a DataFrame df_long with the schedule data
        # This function would plot the schedule
        pass # for now

    def create_schedule_dataframe(self):
        # This function would convert the solution into a DataFrame
        # Return a DataFrame similar to df_long from earlier examples
        pass # for nwo

    def plot_schedule_from_dataframe(self, df_long):
        # Function to plot the schedule
        pass # for now
    
    def _compile_objective_function(self):
        self.problem += pulp.lpSum(self.objective_function_components)

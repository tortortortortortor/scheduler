import pulp
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import datetime
import warnings


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
        self._add_shift_type_constraints()
        self._add_max_days_worked_constraints()
        self._add_max_consecutive_days_worked_constraints()
        self._add_role_specific_shift_constraints()
        self._add_shift_distribution_objective()

        # ... other constraints
        
        #  self._add_weekend_fairness_constraint()
        self._compile_objective_function()

    def _add_max_consecutive_days_worked_constraints(self):
        max_consecutive_days = 7  # Maximum number of consecutive days a staff member can work
        for staff_member in self.staff_info:
            for week in range(self.num_weeks):
                for start_day in range(self.days_per_week):
                    # Calculate the end day and adjust for week transition
                    end_day = start_day + max_consecutive_days
                    if end_day > self.days_per_week:
                        # Window spans two weeks
                        days_in_current_week = self.days_per_week - start_day
                        days_in_next_week = end_day - self.days_per_week
                        next_week = (week + 1) % self.num_weeks

                        # Sum shifts across the 7-day window spanning two weeks
                        shift_sum = pulp.lpSum(self.shifts[staff_member, week, day, shift_type] 
                                               for day in range(start_day, self.days_per_week)
                                               for shift_type in self.shift_hours) + \
                                    pulp.lpSum(self.shifts[staff_member, next_week, day, shift_type] 
                                               for day in range(days_in_next_week)
                                               for shift_type in self.shift_hours)
                    else:
                        # Window within a single week
                        shift_sum = pulp.lpSum(self.shifts[staff_member, week, day, shift_type] 
                                               for day in range(start_day, end_day)
                                               for shift_type in self.shift_hours)

                    # Apply the constraint
                    self.problem += (shift_sum <= max_consecutive_days, f"Max_Consecutive_Days_{staff_member}_Week{week}_StartDay{start_day}")

    # Tries to evenly distribute shifts
    def _add_shift_distribution_objective(self, penalty_weight=0.0000001):
        # Calculate total shifts for each staff member
        total_shift_count = {
            staff_member: pulp.lpSum(
                self.shifts[staff_member, week, day, shift_type]
                for week in range(self.num_weeks)
                for day in range(self.days_per_week)
                for shift_type in self.shift_hours
            ) for staff_member in self.staff_info
        }

        # Calculate the average shift count
        avg_shift_count = pulp.lpSum(total_shift_count.values()) / len(total_shift_count)

        # Auxiliary variables for differences
        shift_diff_vars = {staff_member: pulp.LpVariable(f"shift_diff_{staff_member}", lowBound=0)
                        for staff_member in total_shift_count}

        # Add objectives to minimize the absolute differences from the average
        for staff_member in total_shift_count:
            # Constraints to calculate the absolute difference
            self.problem += shift_diff_vars[staff_member] >= total_shift_count[staff_member] - avg_shift_count
            self.problem += shift_diff_vars[staff_member] >= avg_shift_count - total_shift_count[staff_member]

            # Add the absolute difference with a penalty weight to the objective function components
            self.objective_function_components.append(penalty_weight * shift_diff_vars[staff_member])

    # This constraint will try to set the maximum number of days worked in a 7-day period
    def _add_max_days_worked_constraints(self):
        max_days_in_7 = 4  # Relaxing the constraint to 4 days in a 7-day period

        for staff_member, info in self.staff_info.items():
            if info["shift"] == "D1":
                for week in range(self.num_weeks):
                    for start_day in range(self.days_per_week):
                        # Calculate the end day and adjust for week transition
                        end_day = start_day + 7
                        if end_day > self.days_per_week:
                            # Window spans two weeks
                            days_in_current_week = self.days_per_week - start_day
                            days_in_next_week = end_day - self.days_per_week
                            next_week = (week + 1) % self.num_weeks

                            # Sum shifts across the 7-day window spanning two weeks
                            shift_sum = pulp.lpSum(self.shifts[staff_member, week, day, "D1"] 
                                                   for day in range(start_day, self.days_per_week)) + \
                                        pulp.lpSum(self.shifts[staff_member, next_week, day, "D1"] 
                                                   for day in range(days_in_next_week))
                        else:
                            # Window within a single week
                            shift_sum = pulp.lpSum(self.shifts[staff_member, week, day, "D1"] 
                                                   for day in range(start_day, end_day))

                        # Apply the constraint
                        self.problem += (shift_sum <= max_days_in_7, f"Max_{max_days_in_7}_D1_Shifts_{staff_member}_Week{week}_StartDay{start_day}")

    # Prefer to assign staff members to their preferred shift type
    def _add_role_specific_shift_constraints(self):
            for staff_member, info in self.staff_info.items():
                assigned_shift = info["shift"]

                for week in range(self.num_weeks):
                    for day in range(self.days_per_week):
                        for shift_type in self.shift_hours:
                            # Staff member can only work their assigned shift type
                            if shift_type != assigned_shift:
                                self.problem += (self.shifts[staff_member, week, day, shift_type] == 0)


    def _add_shift_type_constraints(self):
        for week in range(self.num_weeks):
            for day in range(self.days_per_week):
                # Ensure exactly one D1 shift per day
                self.problem += pulp.lpSum(self.shifts[staff_member, week, day, "D1"] for staff_member in self.staff_info) == 1, f"One_D1_Shift_Week{week}_Day{day}"

                # Ensure exactly one D2 shift per day
                self.problem += pulp.lpSum(self.shifts[staff_member, week, day, "D2"] for staff_member in self.staff_info) == 1, f"One_D2_Shift_Week{week}_Day{day}"

                # Ensure exactly one Mx shift per day
                self.problem += pulp.lpSum(self.shifts[staff_member, week, day, "Mx"] for staff_member in self.staff_info) == 1, f"One_Mx_Shift_Week{week}_Day{day}"

                # Ensure exactly one Night shift per day
                self.problem += pulp.lpSum(self.shifts[staff_member, week, day, "Night"] for staff_member in self.staff_info) == 1, f"One_Night_Shift_Week{week}_Day{day}"

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

    def _add_weekend_fairness_constraint(self):
        # Initialize auxiliary variables for max and min weekends worked
        max_weekends_worked = pulp.LpVariable("max_weekends_worked", lowBound=0)
        min_weekends_worked = pulp.LpVariable("min_weekends_worked", lowBound=0, upBound=self.num_weeks * 2)

        # Track weekends worked for each staff member
        weekends_worked = {
            staff_member: pulp.lpSum(self.shifts[staff_member, week, day, shift_type] 
                                     for week in range(self.num_weeks)
                                     for day in [5, 6]  # Assuming 5 and 6 are weekend days
                                     for shift_type in self.shift_hours)
            for staff_member in self.staff_info
        }

        # Add constraints to link the auxiliary variables with the weekends worked
        for staff_member, weekends in weekends_worked.items():
            self.problem += max_weekends_worked >= weekends
            self.problem += min_weekends_worked <= weekends

        # Create an incremental penalty based on the range of unfairness
        fairness_metric = max_weekends_worked - min_weekends_worked

        # Define ranges for the incremental penalty
        small_unfairness_penalty = 0.01  # Small penalty for minor differences
        large_unfairness_penalty = 0.05  # Larger penalty for significant differences
        unfairness_threshold = 2  # Threshold for considering the unfairness significant

        # Add incremental penalty to the objective function
        self.objective_function_components.append(
            small_unfairness_penalty * fairness_metric
        )

        self.problem += large_unfairness_penalty * (fairness_metric - unfairness_threshold) >= 0


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
            self.suggest_improvements()
        else:
            print("No optimal solution found. Will not generate a report.")

    def suggest_improvements(self):
        """
        Analyzes the current scheduling solution and suggests improvements.
        """
        print("Suggested Improvements:")
        
        # Calculate total expected hours for all staff
        total_expected_hours = sum((info['work_percentage'] / 100) * self.MAX_HOURS_FULL_TIME for info in self.staff_info.values())

        # Calculate total actual hours worked by all staff
        total_actual_hours = sum(
            sum(pulp.value(self.shifts[staff_member, week, day, shift_type]) * self.shift_hours[shift_type]
                for week in range(self.num_weeks)
                for day in range(self.days_per_week)
                for shift_type in self.shift_hours)
            for staff_member in self.staff_info
        )

        # Calculate the shortfall or excess in hours
        hours_difference = total_actual_hours - total_expected_hours

        # If there's a significant shortfall, suggest hiring more staff
        if hours_difference < -100:  # Arbitrary threshold for significant shortfall
            print("- Consider hiring additional staff to cover the shortfall of", -hours_difference, "hours.")

        # If there's a significant excess, suggest reducing work percentages or reassigning tasks
        elif hours_difference > 100:  # Arbitrary threshold for significant excess
            print("- Consider reducing work percentages or reassigning tasks to manage the excess of", hours_difference, "hours.")

        # Check for staff members who are significantly overworked or underworked
        for staff_member, info in self.staff_info.items():
            total_hours_staff_member = sum(
                pulp.value(self.shifts[staff_member, week, day, shift_type]) * self.shift_hours[shift_type]
                for week in range(self.num_weeks)
                for day in range(self.days_per_week)
                for shift_type in self.shift_hours
            )
            expected_hours = (info['work_percentage'] / 100) * self.MAX_HOURS_FULL_TIME
            discrepancy = total_hours_staff_member - expected_hours

            # Suggest adjustments for individual staff members
            if discrepancy > 50:  # Threshold for considering someone as overworked
                print(f"- {staff_member} is overworked by {discrepancy} hours. Consider reducing workload.")
            elif discrepancy < -50:  # Threshold for considering someone as underworked
                print(f"- {staff_member} is underworked by {-discrepancy} hours. Consider increasing workload or reassigning tasks.")

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
        # Create the DataFrame
        df_schedule = self.create_schedule_dataframe()

        self.plot_staff_schedule(df_schedule)
        # Plot the schedule
       # self.save_schedule_to_excel(df_schedule, 'staff_schedule.xlsx')

    def create_schedule_dataframe(self):
        schedule_data = []
        start_date = datetime.date(2024, 1, 1)

        for staff_member in self.staff_info:
            for week in range(self.num_weeks):
                for day in range(self.days_per_week):
                    for shift_type in self.shift_hours:
                        shift_value = pulp.value(self.shifts[staff_member, week, day, shift_type])
                        if shift_value is not None and shift_value == 1:
                            date = start_date + datetime.timedelta(days=7 * week + day)
                            schedule_data.append([staff_member, date, shift_type])

        df = pd.DataFrame(schedule_data, columns=['Staff', 'Date', 'Shift'])
        
        return df

    def plot_staff_schedule(self, df_long):

        # Generate a timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file_path = f'staff_schedule_{timestamp}.png'

        # Check DataFrame format
        assert 'Staff' in df_long and 'Date' in df_long and 'Shift' in df_long, "DataFrame must have 'Staff', 'Date', and 'Shift' columns"

        # Suppress font-related warnings
        warnings.filterwarnings("ignore", category=UserWarning, message="Glyph .* missing from current font")

        # Define custom legend labels and colors
        legend_labels = {'D1': 'D1', 'D2': 'D2', 'Mx': 'Mx', 'Night': 'Night'}
        legend_colors = {'D1': 'blue', 'D2': 'green', 'Mx': 'orange', 'Night': 'purple'}

        # Create a custom legend
        custom_legend = [plt.Line2D([0], [0], marker='o', color='w', label=legend_labels[shift], markersize=10, markerfacecolor=legend_colors[shift]) for shift in legend_labels]

        # Plotting
        plt.figure(figsize=(20, 10))
        sns.scatterplot(data=df_long, x='Date', y='Staff', hue='Shift', s=100, palette=legend_colors, legend='full')

        # Customize the axes
        plt.yticks(range(len(df_long['Staff'].unique())), df_long['Staff'].unique())
        plt.gca().invert_yaxis()  # Invert y axis so that the top staff member is at the top
        plt.xlabel('Date')
        plt.ylabel('Staff')
        plt.title('Staff Shift Schedule')

        # Add the custom legend
        plt.legend(handles=custom_legend, title='Shifts', bbox_to_anchor=(1.05, 1), loc='upper left')

        plt.grid(True, which='major', linestyle='--', linewidth=0.5)
        plt.tight_layout()

        # Save the plot as a PNG file
        plt.savefig(output_file_path, bbox_inches='tight')
        plt.close()  # Close the figure

    def export_schedule_to_excel(self, output_file_path):
        """
        Exports the schedule data to an Excel file.

        Parameters:
        output_file_path (str): The file path to save the output Excel file.

        Returns:
        None
        """

        # Constants
        start_date = datetime.datetime(2024, 1, 1)

        # Prepare the header
        header = ['Staff Member', 'Shift', 'Total Hours']
        dates = [start_date + datetime.timedelta(days=week * self.days_per_week + day) 
                 for week in range(self.num_weeks) 
                 for day in range(self.days_per_week)]
        date_headers = [date.strftime('%Y-%m-%d') for date in dates]
        header.extend(date_headers)

        # Prepare the data for each staff member
        data = []
        for staff_member, info in self.staff_info.items():
            total_hours = sum(pulp.value(self.shifts[staff_member, week, day, shift_type]) * self.shift_hours[shift_type]
                              for week in range(self.num_weeks)
                              for day in range(self.days_per_week)
                              for shift_type in self.shift_hours)
            row = [staff_member, info['shift'], total_hours]
            for week in range(self.num_weeks):
                for day in range(self.days_per_week):
                    shift_worked = next((shift_type for shift_type in self.shift_hours 
                                         if pulp.value(self.shifts[staff_member, week, day, shift_type]) == 1), ' ')
                    row.append(shift_worked)
            data.append(row)

        # Create a DataFrame
        df = pd.DataFrame(data, columns=header)

        # Export to Excel
        df.to_excel(output_file_path, index=False)
        print(f"Schedule exported to {output_file_path}")
    
    def _compile_objective_function(self):
        self.problem += pulp.lpSum(self.objective_function_components)

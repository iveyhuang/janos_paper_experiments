#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
on 16:18 April 30, 2020

@author: huangteng

Description:
    Copied from evaluate_linearize_logistic_20200106.py
"""

from janos_main import *
import pandas as pd
import numpy as np
import sys
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from datetime import datetime
import time
from sklearn.neural_network import MLPRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error

pd.options.mode.chained_assignment = None

"""
load data
"""
# This is the data frame for training the predictive models.
historical_student_data = pd.read_csv("college_student_enroll-s1-1.csv")

# This is information of applicants, whose financial aid is to be determined.
# We will use these numbers (SAT, GPA) later in the objective function.
applications = pd.read_csv("college_applications6000.csv")

"""
set the constant in the model
"""
scholarships = [0, 2.5]  # lower and upper bound if the scholarship
n_simulations = 10  # to have meaningful mean and standard deviation; could also use 10 (original value in the paper)
student_sizes = [50, 500, 5000]  # we measure these predictions' RMSE
interview_sizes = [5, 10, 15, 20, 25]

"""
pretrained model
"""
# Assign X and y
X = historical_student_data[["SAT", "GPA", "merit"]]
y = historical_student_data[["enroll"]]

# Before training the model, standardize SAT and GPA.
# For convenience, we do not standardize merit.
scaler_sat = StandardScaler().fit(X[["SAT"]])
scaler_gpa = StandardScaler().fit(X[["GPA"]])
X['SAT_scaled'] = scaler_sat.transform(X[['SAT']])
X['GPA_scaled'] = scaler_gpa.transform(X[['GPA']])

# Then, train the logistic regression model.
my_logistic_regression = LogisticRegression(random_state=0, solver='lbfgs').fit(
    X[["SAT_scaled", "GPA_scaled", "merit"]], y)

# Also, standardize the SAT and GPA in the application data
applications["SAT_scaled"] = scaler_sat.transform(applications[["SAT"]])
applications["GPA_scaled"] = scaler_gpa.transform(applications[["GPA"]])

"""
Prepare the output file
"""
now = datetime.now()
date_time = now.strftime("%H-%M-%S-%Y%m%d")
filename = "20200501_logistic_regression_approximation_evaluation_" + date_time + ".txt"
output = open(filename, "w")
# output.write("interview_sizes\t\titeration\t\tRMSE\n")
output.write("student_size\t\tn_intervals\t\titeration\t\tRMSE\t\tgurobi_time\t\tjanos_time\t\tobj_val\n")
output.close()

"""
Experiments:
"""
for n_applications in student_sizes:
    # n_applications = student_sizes[0]
    BUDGET = int(0.2 * n_applications)
    for n_intervals in interview_sizes:
        for iter in range(n_simulations):

            random_sample = applications.sample(n_applications, random_state=iter)
            random_sample = random_sample.reset_index()

            m = JModel()

            # Define regular variables
            assign_scholarship = m.add_regular_variables([n_applications], "assign_scholarship")
            for app_index in range(n_applications):
                assign_scholarship[app_index].setContinuousDomain(lower_bound=scholarships[0],
                                                                  upper_bound=scholarships[1])
                assign_scholarship[app_index].setObjectiveCoefficient(0)

            # Define predicted variables
            # First, we need to create structures of predictive models. In this case, we associate such a structure with an existing / pretrained logistic regression model.
            logistic_regression_model = OptimizationPredictiveModel(m, pretrained_model=my_logistic_regression,
                                                                    feature_names=["SAT_scaled", "GPA_scaled", "merit"])
            logistic_regression_model.set_breakpoints(n_intervals)
            print("iter = ", iter, "\tn_intervals = ", n_intervals, "\tn_breakpoints = ",
                  logistic_regression_model.get_breakpoints())

            # Now, we could define the predicted decision variables and associate them with the predicted model structure.
            enroll_probabilities = m.add_predicted_variables([n_applications], "enroll_probs")
            for app_index in range(n_applications):
                enroll_probabilities[app_index].setObjectiveCoefficient(1)
                mapping_of_vars = {"merit": assign_scholarship[app_index],
                                   "SAT_scaled": random_sample["SAT_scaled"][app_index],
                                   "GPA_scaled": random_sample["GPA_scaled"][app_index]}
                enroll_probabilities[app_index].setPM(logistic_regression_model, mapping_of_vars)

            # Construct constraints
            # \sum_i x_i <= BUDGET
            scholarship_deployed = Expression()

            for app_index in range(n_applications):
                scholarship_deployed.add_term(assign_scholarship[app_index], 1)

            m.add_constraint(scholarship_deployed, "less_equal", BUDGET)

            # solve the model
            m.add_gurobi_param_settings('TimeLimit', 1800)
            m.add_gurobi_param_settings('DUALREDUCTIONS', 0)
            m.add_gurobi_param_settings('MIPGap', 0.001)
            m.add_gurobi_param_settings('Threads', 1)
            m.set_output_flag(0)
            m.solve()

            """
            write output
            borrowed from https://www.gurobi.com/documentation/8.1/examples/workforce1_py.html
            """
            status = m.gurobi_model.status

            if status == GRB.Status.UNBOUNDED:
                print('The model cannot be solved because it is unbounded')
                sys.exit(0)
            elif status == GRB.Status.OPTIMAL:
                # predicted values from the logistic regression
                predicted_values = []
                for rv_index in range(m.get_number_of_regular_variables()):
                    optimized_merit_decision = m.get_regular_variables()[rv_index].X
                    predicted_probability = \
                    my_logistic_regression.predict_proba([[random_sample["SAT_scaled"][rv_index],
                                                           random_sample["GPA_scaled"][rv_index],
                                                           optimized_merit_decision]])[0][1]
                    predicted_values.append(predicted_probability)

                # approximation values:  pv_index.X
                approximated_values = []
                for pv_index in range(m.get_number_of_predicted_variables()):
                    approximated_values.append(m.get_predicted_variables()[pv_index].X)

                RMSE = mean_squared_error(predicted_values, approximated_values) ** 0.5
                output = open(filename, "a")
                #                output.write(str(n_intervals) + "\t\t" + str(iter) + "\t\t" + str(RMSE) + "\n")
                output.write(str(n_applications) + "\t\t" + str(n_intervals) + "\t\t" + str(iter) +
                             "\t\t" + str(RMSE) +
                             "\t\t" + str(m.get_time()) + "\t\t" + str(m.gurobi_model.runtime) +
                             "\t\t" + str(m.gurobi_model.objval) + "\n")
                output.close()
            elif status != GRB.Status.INF_OR_UNBD and status != GRB.Status.INFEASIBLE:
                print('Optimization was stopped with status %d' % status)
            else:
                # if none of the above, then do IIS
                print('The model is infeasible; computing IIS')
                m.gurobi_model.computeIIS()
                m.gurobi_model.write("ip_model_inf.ilp")
                if m.gurobi_model.IISMinimal:
                    print('IIS is minimal\n')
                else:
                    print('IIS is not minimal\n')
                print('\nThe following constraint(s) cannot be satisfied:')
                for c in m.gurobi_model.getConstrs():
                    if c.IISConstr:
                        print('%s' % c.constrName)


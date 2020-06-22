# About this repo
This repository contains code and data files for replicating the validation experiments in [the JANOS paper](https://arxiv.org/abs/1911.09461).

Before executing the code, change `from janos_main import *` into `from janos import *`.

To execute a `.py` file and replicate our experimental results, first, make sure the code file and the data files are in the same folder. Then, direct to the folder where the files are located in the command line, type `python rewrite_08_20200430_s1.py` and press enter, here taking `rewrite_08_20200430_s1.py` as an example.

## Data files
`college_student_enroll-s1-1.csv` contains the 20,000 student records for training predictive models.

`college_applications6000.csv` contains 6,000 student application records. We randomly draw certain number of records from this pool for our experiments in the paper.


## Code files

`rewrite_08_20200430_s1.py` is for comparing JANOS_Discrete, JANOS_CONTINUOUS, and a greedy heuristic when using logistic regression models and neural networks respectively.

`evaluate_linearize_logistic_20200430.py` is for evaluating the accuracy of the linearization component for logistic regression models.

`evaluate_linear_regression_20200430.py` is for evaluating the performance of JANOS at solving various-sized problems when using linear regression models.

`evaluate_logistic_regression_20200430.py` is for evaluating the performance of JANOS at solving various-sized problems when using logistic regression models.

`evaluate_neural_network_20200430.py` is for evaluating the performance of JANOS at solving various-sized problems when using neural networks.

## Result files

`data_all_scale_20200501_summary.csv` contains the formatted results for generating Figure 3 (The average runtimes of three predictive models with different scales) in the most recent version.

`20200501_logistic_regression_approximation_evaluation_13-56-12-20200502.txt` contains the formatted results for generating Figure 4 (The quality of the linear approximation of the logistic regression function at optimal solutions) in the most recent version.

`rewrite_08_s1_full_15/09/27-20200501.xlsx` contains the formatted results for generating Table 1 in the most recent version.



## Contact us

_Please email us if you have any questions._

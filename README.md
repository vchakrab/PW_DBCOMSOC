# DBCOMSOC

Copyright 2019 Vishal Chakraborty. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE.txt file at the root of the project.

## Implementing The Possible Winner Problem
We reduce the PW problem to Integer Linear Programming and SAT. 

__Basic notation__

Number of candidates _m_

Number of voters _n_

### Experiments
We evaluate our system with two kinds of experiments. 
#### No Preprocessing
For every input, a new model is created from scratch and optimised (solved).
Each run of the program comprises of the following three steps-
```

1. Read the input file containing the patial profile
2. Create a model
    1. Initialise variables
    2. Transitivity constraints
    3. Antisymetric constraints
    4. Partial profile constraints
    5. PW definition constraints
3. Optimise (solve) the model
```
#### Preprocessing
In this case we create partial models for various parameter settings 

>__m__ = 5, 10, 15, 20, 25
>
> __n__ = 10, 100, 500, 1000, 5000, 10000.

This is possible because the transitivity constraints and antisymetry constraints are _independent_ of the input partial profile and the distinguished candidate. Therefore, we can preprocess the file thereby saving time whilst solving a problem instance. The preprocessing step consists of the following steps 

```
1. Create a partial model
    1. Initialise variables
    2. Position constraint 1
    3. Position constraint 2
2. Save model to disk
```

When we want to create a model for a specific input partial profile and a distinguished candidate, we do the following -
```
1. Load the corresponsing partial model from disk 
2. Update the model
    1. Partial Profile Constraints
    2. Possible winner constraint
3. Optimise (solve) the model
```

Each kind is evaluated with Gurobi ILP solver.

---

### Datasets

All experiments willbe run on three synthetically generated datasets

>1. Dataset 1 - Drop Cand (Kunal B. R.)
>2. Dataset 2 - RSM+ (Théo D.)
>3. Dataset 3 - Top k (Théo D.)

## Directory Tree

>__PW_DBCOMSOC__
>>
>>README.md
>>
>>LICENSE.txt
>>
>>gurobi_install.md
>>
>>__Possible Winner_Gurobi__
>>>
>>>_Contains all scripts that uses only the Gurobi optimiser_
>>>
>>>
>>> `multiprocess_pw_gen.py.py` script to compute the set of PW for an input file.
>>>
>>> `test_multi.py`  test script which repeatedly calls `multiprocess_pw_gen.py` on various data sets.
>>
>>__Possible Winner_G_Elim__
>>>_Contains all scripts that uses Xia's Up/Down elimination and the Gurobi optimiser_


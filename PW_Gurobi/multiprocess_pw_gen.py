'''
Run as follows:
python3 multi_pw_gen.py <input_file and path wrt to script location> <scoring rule option>
SCORING RULE OPTIONS-
'b' for borda; 
'k' followed by 1,2,3,... for k approval, 
'v' for veto
'''
import sys, os, math
sys.path.append( '/home/vishal/gurobi811/linux64/lib/python3.5_utf32')
from gurobipy import *
import csv
import time
from multiprocessing import Pool, Lock
import numpy as np
#number of processes used in the pool
NUM_PROCESSES = 5
#chunk size of multiprocessing NOT USED CURRENTLY
CHUNK_SIZE = 1
#list of tuples containg all the partial profiles in the data file
partial_profs = []
#number of voters
n = 0
#number of candidates
m = 0
#-1 if not k approval, int k if k-approval
k = -1
#the name of the file containing the partial profile
filename = sys.argv[1]
#Rule from arguements ('b' for borda; 'k' followed by 1,2,3,... for k approval, 'v' for veto)
rule = sys.argv[2]
#lock for gurobi file reading
lock = Lock()
'''
ProcessFail: Exception raised when a process within a pool returns an incoherent value
'''
class ProcessFail(Exception):
    pass

'''
Creates and saves partial model to file model.mps
Works for the following scoring rules --
borda scoring rules (m,m-1,m-2,..., 1)
k approval scoring rules (1,1,1,..., 1 (k times), 0,0,0,...,0)
Veto scoring rule (1,1,1,..., 0)

Arguments - rule 'b', 'v', or k
Return Value - A tuple (var_time, cstr1_time, cstr2_time)
'''
def createModel():
  global n, m, partial_profs 
  #initialize empty model
  model = Model("election_pw")
  model.setParam("Seed", 42)
  model.params.presolve = 0
  
  start_time = time.time()
  #Constrains - to rensure ordering 
  if rule is 'b':
    # Create decision variables for each x^l_{i,j}
    x = model.addVars(n, m, m, vtype = GRB.BINARY, name = "x" )
    var_time = time.time() - start_time
    model.addConstrs(  1 == sum(x[l,i,p] for p in range(m)  ) for l in range(n) for i in range(m) )
    cstr1_time = time.time() - (var_time + start_time)
    model.addConstrs( 1 == sum(x[l, i, p] for i in range(m) )  for l in range(n) for p in range(m) )
    cstr2_time = time.time() - (start_time + var_time + cstr1_time)
  elif rule is 'v':
    # Create decision variables for each x^l_{i,j}
    x = model.addVars(n, m, vtype = GRB.BINARY, name = "x" )
    var_time = time.time() - start_time
    model.addConstrs(m-1 == sum(x[l,i] for i in range(m)) for l in range(n))
    cstr1_time = time.time() - (start_time + var_time)
    #veto does not have second constraint. So this time is 0. 
    #Added to keep return type uniform for all functions
    cstr2_time = 0
  else:
    # Create decision variables for each x^l_{i,j}
    x = model.addVars(n, m, k, vtype = GRB.BINARY, name = "x" )
    var_time = time.time() - start_time
    model.addConstrs(  1 >= sum(x[l,i,p] for p in range(k)  ) for l in range(n) for i in range(m) )
    cstr1_time = time.time() - (start_time + var_time)
    #upholds that there is exactly one candidate in each of the first k positions
    model.addConstrs( 1 == sum(x[l, i, p] for i in range(m) )  for l in range(n) for p in range(k) )
    cstr2_time = time.time() - (start_time + var_time + cstr1_time)
    
  #save model file
  model.write('model.mps')
  return (var_time, cstr1_time, cstr2_time)
'''
Call back function for imap_unordered()
Checks if dist_cand is a PW.
Prints if dist_cand is a PW or NOT a PW.

Argument - dist_cand
Retrun Value - A tuple containing
(dist_cand, 1 if PW 0 if NOT PW, constrain PW time, optimise Time, partial profile constraint time)
'''
def checkPW(dist_cand):
  global m, n, lock, k, partial_profs
  output = -1
  pw_cstr_time = -1
  prtl_cstr_time = -1
  opt_time = -1
  start = -1
  tot_start = time.time()
  try:
    #Loading common constraints model
    # lock.acquire() 
    model = read('model.mps')
    # lock.release()
    x = model.getVars()
    model.params.mipFocus = 1
    model.params.preDepRow = 1
    model.params.presolve = 1
    model.params.presparsify = 1
    if rule == 'b':
      #reshaping variable for easy access
      x = np.array(x).reshape((n,m,m))
      #Constrains - partial profile  
      start = time.time() 
      for l in partial_profs:
          model.addConstr( 1 <= sum(p * (x[l[0], l[1],p] - x[l[0], l[2],p]) for p in range(m) ) )
      #profile coonstraint time end
      prtl_cstr_time = time.time() - start
      #sum for distinguished candidate
      winner_sum = sum(p * x[l, dist_cand ,p] for l in range(n) for p in range(m))
      #add winner constraint for dist_cand
      for cand in range(m):
          if cand != dist_cand:
              model.addConstr( sum(p * x[l, cand, p] for l in range(n)
                               for p in range(m) ) <= winner_sum )
      #timing winner constraints end
      pw_cstr_time = time.time() - (start + prtl_cstr_time)
    elif rule == 'v':
      #reshaping array for easy access
      x = np.array(x).reshape((n,m))
      #starting timer for constraints and optimization
      start = time.time()
      #these constraints are for ensuring prefrences are upheld, since l[1] has to be preferable
      #and there is only 1 zero l[1] must be 1
      for l in partial_profs:
        model.addConstr(1 == x[l[0], l[1]])
      prtl_cstr_time = time.time() - start
      #contraint checking for possible winner (comparing number of times it appears in first m-1 spots)
      #sum for distinguished candidate
      winner_sum = sum(x[l, dist_cand] for l in range(n))
      #PW constraint
      for cand in range(m):
          if cand != dist_cand:
              model.addConstr( sum(x[l, cand] for l in range(n) )<= winner_sum)
      #timing winner constraints end
      pw_cstr_time = time.time() - (start + prtl_cstr_time)
    else:
    	#rule is k-approval
      x = np.array(x).reshape((n,m,k))
      #timer for constraints and optimization
      start = time.time()
      #constraint checking for possible winner (comparing num times appearing in first k positions)
      #these constraints are for ensuring prefrences are upheld
      for l in partial_profs:
          model.addConstr(0 <= sum(x[l[0], l[1],p] - x[l[0], l[2],p] for p in range(k)))
      prtl_cstr_time = time.time() - start
      #sum for distiguished candidate
      winner_sum = sum(x[l, dist_cand ,p] for l in range(n) for p in range(k))
      #PW constrain
      for cand in range(m):
          if cand != dist_cand:
              model.addConstr( sum(x[l, cand, p] for l in range(n)
                               for p in range(k) ) <= winner_sum)
      #timing winner constraints end
      pw_cstr_time = time.time() - (start+prtl_cstr_time)
    #run model
    model.optimize()
    opt_time = time.time() - (start + pw_cstr_time + prtl_cstr_time)
    #gather possible winners and certain losers
    if model.status == GRB.Status.OPTIMAL:
        output = 1
    else:
        output = 0
  except Exception as e:
      print("ERROR in checkPW:",e)
      return e
  tot_time= time.time() - tot_start
  return (dist_cand, output, pw_cstr_time, opt_time, prtl_cstr_time, tot_time)
'''
Read partial profiles from text file (gobal filename)
and populates global partial_profs
with (l,i,j) 
if voter v_l preferes c_i to c_j, i.e., c_i > c_j

Arguments - global filename
Return Value - None. Populates global partial_profs
'''
def populate_partial_profiles():
  global partial_profs, n, m, filename,k
  #first row has m,n. This variables keeps a track of the first row.
  isFirstRow = True
  #votr used to index each voter.
  #voter indexing begins at 0, used for filling partial_profs
  votr = 0 
  
  with open(filename) as csvfile:
    readCSV = csv.reader(csvfile, delimiter=',')
    for row in readCSV:
      #the first row is m,n
      if isFirstRow == True:
          #number of candidates
          m = int(float(row[0]))
          #number of voters
          n = int(float(row[1]))
          isFirstRow = False
          continue
      #used for keeping track of first element in each row which is candidates dropped
      isFirstEle = True 
      
      #pair is each 'cell' in a row. Either a number or an ordered pair
      for pair in row:
          if isFirstEle:
              isFirstEle = False
          else:
              #pair is an ordered-pair "(x,y)"
              x = pair[1 : pair.find(',')]
              y = pair[pair.find(',')+1 : pair.find(')')]
              #create an element [l,i,j] to be appended
              prefEle = [votr, int(x), int(y)]
              #append the element [l,i,j] to the global list of partial profiles
              partial_profs.append(tuple(prefEle))
      votr = votr + 1
'''
main function

'''
def main():
    global k
    pw = []
    not_pw = []
    
    print("\n\nBEGIN:\n", filename, "----------------")
    #variables to keep track of timing
    tot_start = time.time()
    read_start = time.time()
    populate_partial_profiles()
    read_end = time.time()
    output = None
    #returned tuple from createModel functions
    time_tup = None
    tot_opt_time = 0
    tot_PW_cstr_time = 0
    tot_prtl_cstr_time = 0
    cand_times = {}
    #CHUNK_SIZE = int(math.floor(m/7))
    #assigning value to k
    if rule[:1]=='k':
        k = int(rule[1:])
    #creates a set of processes to simultaneously make calculations
    pool = Pool(processes = NUM_PROCESSES)
    #generates the common constraints
    time_tup = createModel()
    output = pool.imap_unordered(checkPW, range(m), CHUNK_SIZE)
    pool.close()
    pool.join()
    tot_end = time.time()
    #print(output)
    for retVal in output:
        print(retVal)
        if not isinstance(retVal,tuple):
            print(filename + ": ERROR in main:", retVal)
            #raise ProcessFail(filename + ": A candidate has failed with the following exception:", retVal)
            sys.exit(1)
        else:
            #[dist_cand, PW ?, Time PW constr, Optimize Time, partial prof constr, candidate time]
            tot_prtl_cstr_time += retVal[4]
            tot_opt_time += retVal[3] 
            tot_PW_cstr_time += retVal[2]
            cand_times[retVal[0]] = retVal[5]
            if retVal[1] == 1:
                pw.append(retVal[0])
            else:
                not_pw.append(retVal[0])  

    fname = filename.split('/')[-1]
    fname = fname.strip()
    print("FILE NAME: ", fname)
    fname_list = fname.split('_')
    #print all times as a tuple for convinience
    #adding mean partial profile constraint time
    time_tup = time_tup + (tot_prtl_cstr_time/m,)
    pre_tup = (fname, m, int(fname_list[1]), int(fname_list[2]) , int(fname_list[3][:-4]), tot_end - tot_start, read_end - read_start)
    post_tup = (tot_PW_cstr_time/m, tot_opt_time/m)
    answer_tup = pre_tup + time_tup + post_tup + (cand_times,)
    
    print("PW Computation for ", filename)
    print("POSSIBLE WINNERS:" , pw)
    print("NOT POSSIBLE WINNERS:" , not_pw)
    print('INPUT PROFILE READ TIME:', read_end - read_start)
    print("MEAN PW CONSTRAINT TIME:" , tot_PW_cstr_time/m)
    print("MEAN OPTIMISATION TIME PER CANDIDATE:" , tot_opt_time/m)
    print("TOTAL PROGRAM TIME:", tot_end - tot_start)
    print(fname + ", " + str(pw))
    print(answer_tup)
    print("---------------------------------------------------------------------------------")
    
if __name__ == "__main__":
    main()



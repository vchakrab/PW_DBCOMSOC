# Installing Gurobi

## Instructions to set up Gurobi on a remote Linux machine with sudo

1. Download the latest tar file from the Gurobi Website.
2. Unzip the file.


```bash
tar xvfz gurobi8.1.1_linux64.tar.gz
```


This should create a folder called "gurobi811" in the current directory.

3. Edit .bashrc file


```bash
nano $HOME/.bashrc
```


Copy paste the following at the end of the file.
Change `</FULL/PATH/>` to `<$HOME/>`. This path should point to the gurobi folder.

```bash
export GUROBI_HOME="/FULL/PATH/gurobi811/linux64"
export PATH="${PATH}:${GUROBI_HOME}/bin"
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:${GUROBI_HOME}/lib"
export GRB_LICENSE_FILE="$HOME/gurobi.lic"
```   


4. Issue the comand

```bash
source $HOME/.bashrc
```



5. Check if installation was successful with the command


```bash
grbgetkey
```

This should prompt for the license. If it does, your installation was successful. Now quit this.

6. Get the license from your Gurobi account online. Copy paste the line on the Your licenses page and enter it on the terminal.


```bash
grbgetkey < bbf398dc-6558-11e9-980e-02e454ff9c50 >
```


7. To use the python interactive shell of Gurobi


```bash
gurobi.sh
```



## Setting up proper library paths-

To use the Gurobi python library point the gurobi python3 library folder.

Add the following (if you are coding in python) before importing gurobipy

```python
import sys, os
sys.path.append( '/home/vishal/gurobi811/linux64/lib/python3.5_utf32')
from gurobipy import *
```
Obviously, this depends on where gurobi was installed.


## Gurobi licence on EC2
1. VPN to ucsc
2.Connect to EC@ instance and then

ssh -L8008:apps.gurobi.com:80 $vishal@vpn-pool-128-114-231-209.ucsc.edu
(get the address from the Sharing option in System preferences.

3. Make another connection to EC2 and then
 
$ grbgetkey --verbose --port=8008 --server=127.0.0.1 --http  ${YOUR_LICENSE HERE (format is xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)}

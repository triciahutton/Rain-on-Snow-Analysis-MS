#!/bin/bash

#SBATCH --partition=t1small
#SBATCH --account=dyndown
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mail-user=phutton5@alaska.edu
#SBATCH --mail-type=FAIL
#SBATCH --time=10:00:00
#SBATCH --output=ROS_TP_log.%j

ulimit -s unlimited
ulimit -l unlimited

source $(conda info --base)/etc/profile.d/conda.sh

conda activate newdyndown
echo "Conda environment activated"

chmod +x ROS_by_month_PT.py 

echo "starting ROS with temp pressure levels   " 

python -u ROS_by_month_PT.py --start-year 2023 --n-years 3 > log_ROS_month_out.${SLURM_JOB_ID} 2>&1



echo "script complete!"


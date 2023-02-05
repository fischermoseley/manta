import os

os.system('echo "#!/usr/bin/python3" > manta')
os.system("cat manta.py >> manta")
os.system("chmod +x manta")

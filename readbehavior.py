import json
import matplotlib.pyplot as plt
import os.path
import sys
import argparse

def findFiles(behdir,overwrite=False):
	exts = ['.vr', '.tdml']
	paths=[]
	for dirpath,dirnames,filenames in os.walk(behdir):
		paths.extend(map(lambda f: os.path.join(dirpath, f),filter(lambda f: os.path.splitext(f)[1] in exts, filenames)))
		return filenames,dirpath

def extractfile(filen):
	datay=[]
	data_time=[]
	with open(filen) as dataf:
		for line in dataf:
			datab=json.loads(line)
		#	print datab
			if 'y' in datab.keys():
				datay.append(float(datab['y']))
				if 'time' in datab.keys():
					data_time.append(float(datab['time']))


	plt.plot(data_time,datay,'-.',linewidth=2)
	plt.show()
		
def main():
	filepath=raw_input('Locate the desired behavior filepath:')
	[files,filedir]=findFiles(filepath)
#	print filedir
	for ffiles in files:
		filepath_=[filedir+'/'+ffiles]
		for filep in filepath_:
			pass

	#print filep
		extractfile(filep)
#	if 'y' in datab.keys():
		#datay.append(float(datab['y']))
		#print datay

if __name__=='__main__':
	main()



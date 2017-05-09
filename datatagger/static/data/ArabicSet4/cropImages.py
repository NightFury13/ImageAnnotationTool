#author: minesh
#for parsing pascal voc style xml annotation files saved by labelImg annotation tool
#date 5 feb 2017
# arg 1 - path of the dir where full images and xmls are
#arg 2- path to which script wise cropped word images will be written to
import os,sys,glob
import  xml.etree.ElementTree as ET
from PIL import Image, ImageDraw
import re
import codecs
scriptDir="" #script speciffic dir within  the outputdir
listOfXmls=glob.glob(sys.argv[1]+'*.xml')
for annotationFile in listOfXmls:
	wordCount=0
	print annotationFile
	tree=ET.parse(annotationFile)
	root=tree.getroot()
	#print root.tag
	
	for child in root:
		if child.tag=="path":
			fullImagePath=child.text
			fullImage=Image.open(fullImagePath)
			fullImageFileName=os.path.basename(fullImagePath)
			fullImageName=os.path.splitext(fullImageFileName)[0]
		if child.tag=="object":
			wordCount=wordCount+1
			for objectChild in child.iter():
				if objectChild.tag=="name":
					gt=objectChild.text
					#check if the string has any malayalam unicode in it
					if re.findall(ur'[\u0d00-\u0d7f]+', gt):
						#print gt
						#print gt.encode('utf-8')
						scriptDir="Malayalam/"
						
					#check if the string has any hindi unicode in it.
					elif re.findall(ur'[\u0900-\u097f]+', gt):
						scriptDir="Devanagari/"
					elif re.findall(ur'[\u0600-\u06ff]+', gt):
						scriptDir="Arabic/"
					else:
						scriptDir="English/"
						#print "English"
						
				if objectChild.tag=="bndbox":
					for bndBoxChild in objectChild.iter():
						if bndBoxChild.tag=="xmin":
							xmin=bndBoxChild.text
						if bndBoxChild.tag=="ymin":
                                                        ymin=bndBoxChild.text
						if bndBoxChild.tag=="xmax":
                                                        xmax=bndBoxChild.text
						if bndBoxChild.tag=="ymax":
                                                        ymax=bndBoxChild.text
					croppedImageName=sys.argv[2]+scriptDir+fullImageName+"_"+str(wordCount)+"_"+xmin+"_"+ymin+"_"+xmax+"_"+ymax+".jpg"
					croppedWord=fullImage.crop((int(xmin),int(ymin),int(xmax),int(ymax)))
					croppedWord.save(croppedImageName)
					annotationFileName=sys.argv[2]+scriptDir+"annotation.txt"
					annFile=file = codecs.open(annotationFileName, "a", "utf-8")
					annFile.write(os.path.basename(croppedImageName) + " ")
					annFile.write(gt + "\n")
					annFile.close()




		
		
		
	
	


    
    

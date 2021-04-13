'''
@Author: Matheus Barros
Date: 04/13/2021

'''

import Funcoes as fc
import cv2
import numpy as np
import imutils
import glob
import boto3
import os
import pandas as pd
from datetime import datetime

#CREATING CLIENT CONNECTION
AWS_KEY_ID = os.environ['AWS_KEY_ID']
AWS_SECRET = os.environ['AWS_SECRET']

s3 = boto3.client('s3',
					region_name='us-east-1',
					aws_access_key_id=AWS_KEY_ID,
					aws_secret_access_key=AWS_SECRET)


rekog = boto3.client('rekognition',
					region_name='us-east-1',
					aws_access_key_id=AWS_KEY_ID,
					aws_secret_access_key=AWS_SECRET)


count = 0
vidcap = cv2.VideoCapture('Video 2.mp4')
success,image = vidcap.read()
success = True
numObjects = []


while success:

	#SEPARING FRAMES (1 FRAME FOR EVERY 2 SECONDS)
	vidcap.set(cv2.CAP_PROP_POS_MSEC,(count*2000))
	success,image = vidcap.read()
	if success != False:
		count = count + 1
		#SAVING FRAME AS AN IMAGE
		cv2.imwrite( "imgs\\frame%d.jpg" % count, image)
	else:
		break
	
	filename = 'imgs\\frame' + str(count) + '.jpg'
	print(filename)
	
	#UPLOADING IMAGE TO S3
	s3.upload_file(
					Filename=filename,
					Bucket='mybucketpopx',
					Key='Rekognition/frame.png')
	
	#REKOGNITION
	response = rekog.detect_labels(
									Image={'S3Object': {'Bucket': 'mybucketpopx',
														'Name': 'Rekognition/frame.png'}},
											MaxLabels=20,
											MinConfidence=95
											)

	response = response['Labels']

	if count == 1:
		df_principal = pd.DataFrame(response)
	else:
		df_secundaria = pd.DataFrame(response)
	


	#GETTING QUANTITY OF OBJECTS
	count2 = 0

	for i in response:
		count2 = len(i['Instances'])
		numObjects.append(count2)

		if count2 > 0:
			print('Total of {} found: {}'.format(i['Name'],count2))
			continue

	#GETTING TIMESTAMPS
	if count == 1:
		now = datetime.now()
		df_principal = df_principal.assign(TimeStamp = now, Frame = 'Frame: ' + str(count))

	else:
		now = datetime.now()
		df_secundaria = df_secundaria.assign(TimeStamp = now, Frame = 'Frame: ' + str(count))		
		df_principal = df_principal.append(df_secundaria)


df_principal = df_principal.assign(Total = numObjects)

df_principal.to_excel('Result.xlsx',index=False)


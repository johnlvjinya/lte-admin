
import sys
f_handler=open('log.txt', 'a') 
sys.stdout=f_handler 

print('test')

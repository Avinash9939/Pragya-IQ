import os
os.chdir('frontend')
print('CWD:', os.getcwd())
p = os.path.abspath('../backend/storage/5')
print('resolved:', p)
print('exists:', os.path.exists(p))

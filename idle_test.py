import time
import machine

t0 = time.time()

for i in range(1000):
    machine.idle()

t1 = time.time()


for i in range(1000):
    pass

t2 = time.time()

print('With idles = ', t1-t0)
print('Without idles = ', t2-t1)
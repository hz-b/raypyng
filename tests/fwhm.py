import matplotlib.pyplot as plt
import numpy as np
import time




def gaussian(x, mu, sig):
    return np.exp(-np.power(x - mu, 2.) / (2 * np.power(sig, 2.)))


def find_FWHM(y):

    max_y = np.amax(y)  # Find the maximum y value

    xs = [x for x in range(y.shape[0]) if y[x] > max_y/2.0]

    return np.amax(xs)-np.amin(xs)


#simulate the number of rays

n_rays = 2000000
stepsize = 3/n_rays

# box
a = np.arange(0,1,stepsize)
b = np.arange(1,2,stepsize)
c = np.arange(2,3.01,stepsize)

x = np.concatenate((a,b))
x = np.concatenate((x,c))

y = np.full(a.shape[0], 0)
y = np.concatenate((y, np.full(b.shape[0], 1)))
y = np.concatenate((y, np.full(c.shape[0], 0)))

#  gaussian
g = gaussian(x,1.5,1/2.355)




fig, (axs) = plt.subplots(2, 2,figsize=(10,10))


# np.std() - box

st = time.time()
sigma = np.std(y)
fwhm = 2.3555*sigma
et = time.time()

print('np.std():box:', fwhm)
elapsed_time = et - st
print('Execution time:', elapsed_time, 'seconds')

ax = axs[0,0]
ax.scatter(1.5-fwhm/2, 0.5, color='r', label='FWHM')
ax.scatter(1.5+fwhm/2, 0.5, color='r')
ax.plot(x,y)
ax.set_title('np.std() - box, et: ' + str(np.round(elapsed_time,3))+' s')
ax.legend()


# np.std() - gaussian

st = time.time()
sigma = np.std(g)
fwhm = 2.3555*sigma
et = time.time()

print('np.std():gaussian:', fwhm)
elapsed_time = et - st
print('Execution time:', elapsed_time, 'seconds')

ax = axs[0,1]
ax.plot(x,g)
ax.scatter(1.5-fwhm/2, 0.5, color='r', label='FWHM')
ax.scatter(1.5+fwhm/2, 0.5, color='r')
ax.set_title('np.std() - gaussian, et: ' + str(np.round(elapsed_time,3))+' s')
ax.legend()




# np.std() - box

st = time.time()
fwhm = find_FWHM(y)*(x[1]-x[0])
et = time.time()

print('Spline:box:', fwhm)
elapsed_time = et - st
print('Execution time:', elapsed_time, 'seconds')

ax = axs[1,0]
ax.scatter(1.5-fwhm/2, 0.5, color='r', label='FWHM')
ax.scatter(1.5+fwhm/2, 0.5, color='r')
ax.plot(x,y)
ax.set_title('SplineRoots - box, et: ' + str(np.round(elapsed_time,3))+' s')
ax.legend()


# np.std() - gaussian

st = time.time()
fwhm = find_FWHM(g)*(x[1]-x[0])
et = time.time()

print('Spline:gaussian:', fwhm)
elapsed_time = et - st
print('Execution time:', elapsed_time, 'seconds')

ax = axs[1,1]
ax.plot(x,g)
ax.scatter(1.5-fwhm/2, 0.5, color='r', label='FWHM')
ax.scatter(1.5+fwhm/2, 0.5, color='r')
ax.set_title('SplineRoots - gaussian, et: ' + str(np.round(elapsed_time,3))+' s')
ax.legend()



fig.suptitle('FWHM, time and accuracy for {} nrays'.format(n_rays))
plt.tight_layout()
plt.savefig('fwhm.png')
plt.show()
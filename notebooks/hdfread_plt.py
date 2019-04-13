# import matplotlib
# matplotlib.use('pdf')
import matplotlib.pyplot as plt
import numpy as np
import h5py

# SETUP

plt.rcParams['figure.figsize'] = [15, 5]
num_rows = 3
num_samples = 4
f, axes = plt.subplots(num_rows, num_samples)

# DATA

file = h5py.File('../snapshots/prob_unet/test_sample.hdf', 'r')
volumes = file['volumes']
data = [volumes['labels'], volumes['gt_affs'], volumes['raw']]

shape = data[0].shape
print "shape: ", shape

cropx = slice(44, 88)
cropy = slice(44, 88)
cropz = 66

for i, ax in enumerate(axes[0]):
	if i == 3:
		break
	if data[i].name == "/volumes/labels": # labels, todo: base on name
		labels = data[i]
		ax.imshow(labels[22])
	elif data[i].name == "/volumes/gt_affs":
		affs = np.sum(data[i], axis=0)
		ax.imshow(affs[cropz, cropy, cropx], cmap="Greys_r")
	elif data[i].name == "/volumes/raw":
		raw = data[i]
		ax.imshow(raw[cropz, cropy, cropx], cmap="Greys_r")

# PREDICTIONS
file_1 = h5py.File('../snapshots/prob_unet/setup_15/prediction_00000000.hdf', 'r')
file_2 = h5py.File('../snapshots/prob_unet/setup_15/prediction_00000001.hdf', 'r')
file_3 = h5py.File('../snapshots/prob_unet/setup_15/prediction_00000002.hdf', 'r')
file_4 = h5py.File('../snapshots/prob_unet/setup_15/prediction_00000003.hdf', 'r')
volumes_1 = file_1['volumes']
volumes_2 = file_2['volumes']
volumes_3 = file_3['volumes']
volumes_4 = file_4['volumes']
pred = [volumes_1['pred_affs'], volumes_2['pred_affs'], volumes_3['pred_affs'], volumes_4['pred_affs']]
samples = [volumes_1['sample_z'], volumes_2['sample_z'], volumes_3['sample_z'], volumes_4['sample_z']]

cropz = 21  # todo: base on data size

for i, ax in enumerate(axes[1]):
	affs = np.sum(pred[i], axis=0)
	ax.imshow(affs[cropz], cmap="Greys_r")

for i, ax in enumerate(axes[2]):
	sample_z = samples[i][0]
	ax.imshow(sample_z)
	ax.get_yaxis().set_ticks([])

# DISPLAY

plt.show()

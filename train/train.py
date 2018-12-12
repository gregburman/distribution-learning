from __future__ import print_function
import sys
sys.path.append('../')
from gunpowder import *
from gunpowder.tensorflow import *
import malis
import os
import math
import json
import tensorflow as tf
import numpy as np
import logging

from nodes import ToyNeuronSegmentationGenerator
from nodes import AddJoinedAffinities
from nodes import AddRealism


logging.basicConfig(level=logging.INFO)

neighborhood = [[-1, 0, 0], [0, -1, 0], [0, 0, -1]]

def train_until(max_iteration):

	if tf.train.latest_checkpoint('.'):
		trained_until = int(tf.train.latest_checkpoint('.').split('_')[-1])
	else:
		trained_until = 0
	if trained_until >= max_iteration:
		return

	with open('train_net.json', 'r') as f:
		config = json.load(f)

	# define array-keys
	raw = ArrayKey('RAW')
	labels = ArrayKey('GT_LABELS')
	# labels_mask = ArrayKey('GT_LABELS_MASK')
	# artifacts = ArrayKey('ARTIFACTS')
	# artifacts_mask = ArrayKey('ARTIFACTS_MASK')
	affs = ArrayKey('PREDICTED_AFFS')
	gt = ArrayKey('GT_AFFINITIES')
	gt_joined = ArrayKey('GT_JOINED_AFFINITIES')
	gt_mask = ArrayKey('GT_AFFINITIES_MASK')
	gt_scale = ArrayKey('GT_AFFINITIES_SCALE')
	affs_gradient = ArrayKey('AFFS_GRADIENT')

	voxel_size = Coordinate((1, 1, 1))
	input_size = Coordinate(config['input_shape']) * voxel_size
	output_size = Coordinate(config['output_shape']) * voxel_size

	print ("input_size: ", input_size)
	print ("output_size: ", output_size)

	# define requests
	request = BatchRequest()
	request.add(raw, input_size)
	request.add(labels, output_size)
	# request.add(labels_mask, output_size)
	request.add(gt, output_size)
	request.add(gt_mask, output_size)
	request.add(gt_scale, output_size)

	train_pipeline = (
		ToyNeuronSegmentationGenerator(
			shape=np.array ([300, 300, 300]),
			n_objects=50,
			points_per_skeleton=5,
			smoothness=3,
			interpolation="linear") + 
		# RandomProvider()+
		ElasticAugment(
			control_point_spacing=[4,40,40],
			jitter_sigma=[0,2,2],
			rotation_interval=[0,math.pi/2.0],
			prob_slip=0.05,
			prob_shift=0.05,
			max_misalign=10,
			subsample=8) +
		SimpleAugment(transpose_only=[1, 2]) +
		IntensityAugment(raw, 0.9, 1.1, -0.1, 0.1, z_section_wise=True) +
		# GrowBoundary(labels, labels_mask, steps=1, only_xy=True) +
        AddAffinities(
            neighborhood,
            labels=labels,
            affinities=gt,
            affinities_mask=gt_mask) +
		AddJoinedAffinities(
			input_affinities=gt,
			joined_affinities=gt_joined) +
		AddRealism(
			affinities = gt,
			realistic_data = raw,
			sp=0.25,
			sigma=1) +
		BalanceLabels(
			gt,
			gt_scale,
			gt_mask) +
		# DefectAugment(
		# 	raw,
		# 	prob_missing=0.03,
		# 	prob_low_contrast=0.01,
		# 	prob_artifact=0.03,
		# 	artifact_source=artifact_source,
		# 	artifacts=artifacts,
		# 	artifacts_mask=artifacts_mask,
		# 	contrast_scale=0.5,
		# 	axis=0) +
		IntensityScaleShift(raw, 2,-1) +
		PreCache(
			cache_size=40,
			num_workers=10) +
		Train(
			'train_net',
			optimizer=config['optimizer'],
			loss=config['loss'],
			inputs={
				config['raw']: raw,
				config['gt_affs']: gt,
				config['affs_loss_weights']: gt_scale,
			},
			outputs={
				config['affs']: affs
			},
			gradients={
				config['affs']: affs_gradient
			},
			# summary=config['summary'],
			log_dir='log',
			save_every=10000) +
		# IntensityScaleShift(raw, 0.5, 0.5) +
		# Snapshot({
		# 		raw: 'volumes/raw',
		# 		labels: 'volumes/labels/neuron_ids',
		# 		gt: 'volumes/gt_affinities',
		# 		affs: 'volumes/pred_affinities',
		# 		gt_mask: 'volumes/labels/gt_mask',
		# 		labels_mask: 'volumes/labels/mask',
		# 		affs_gradient: 'volumes/affs_gradient'
		# 	},
		# 	dataset_dtypes={
		# 		labels: np.uint64
		# 	},
		# 	every=1000,
		# 	output_filename='batch_{iteration}.hdf',
		# 	additional_request=snapshot_request) +
		PrintProfilingStats(every=10)
	)

	print("Starting training...")
	with build(train_pipeline) as b:
		for i in range(max_iteration - trained_until):
			b.request_batch(request)
	print("Training finished")

if __name__ == "__main__":

	iteration = int(sys.argv[1])
	train_until(iteration)
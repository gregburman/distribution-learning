import mala
import tensorflow as tf
from  tensorflow_probability import distributions as tfd
import json
import prob_unet

def create_network(input_shape, output_shape, name):

	beta = 1

	tf.reset_default_graph()

	raw = tf.placeholder(tf.float32, shape=input_shape)
	raw_batched = tf.reshape(raw, (1, 1) + input_shape)
	gt = tf.placeholder(tf.float32, shape=input_shape)
	gt_batched = tf.reshape(raw, (1, 1) + input_shape)

	unet, prior, posterior, f_comb = prob_unet.prob_unet(
		fmaps_in=raw_batched,
		affmaps_in=gt_batched,
		num_layers=3,
		num_classes=3,
		latent_dim=6,
		base_num_fmaps=32,
		fmap_inc_factor=2,
		downsample_factors=[[3,3,3], [2,2,2], [2,2,2]],
		num_1x1_convs=3)

	affs_batched = tf.layers.conv3d(
		inputs=f_comb,
		filters=3, 
		kernel_size=1,
		padding='valid',
		data_format="channels_first",
		activation='sigmoid',
		name="affs")

	output_shape_batched = affs_batched.get_shape().as_list()
	output_shape = output_shape_batched[1:] # strip the batch dimension

	affs = tf.reshape(affs_batched, output_shape)
	gt_affs = tf.placeholder(tf.float32, shape=output_shape)
	affs_loss_weights = tf.placeholder(tf.float32, shape=output_shape)

	sample_p = prob_unet.sample_z(prior)
	sample_q = prob_unet.sample_z(posterior)

	kl_loss = kl(sample_p, sample_q, 1)
	ce_loss = tf.losses.sigmoid_cross_entropy(gt_affs, affs, affs_loss_weights)
	loss = ce_loss + beta * kl_loss

	summary = tf.summary.scalar('kl_loss', kl_loss)
	summary = tf.summary.scalar('ce_loss', ce_loss)
	# summary = tf.summary.scalar(['loss'], loss)

	opt = tf.train.AdamOptimizer(
		learning_rate=1e-6,
		beta1=0.95,
		beta2=0.999,
		epsilon=1e-8)
	optimizer = opt.minimize(loss)

	output_shape = output_shape[1:]
	print("input shape : %s"%(input_shape,))
	print("output shape: %s"%(output_shape,))

	tf.train.export_meta_graph(filename=name + '.meta')

	config = {
		'raw': raw.name,
		'affs': affs.name,
		'gt_affs': gt_affs.name,
		'affs_loss_weights': affs_loss_weights.name,
		'loss': loss.name,
		'optimizer': optimizer.name,
		'input_shape': input_shape,
		'output_shape': output_shape,
		'summary': summary.name
	}
	with open(name + '.json', 'w') as f:
		json.dump(config, f)

def kl(mean, log_sigma, batch_size, free_bits=0.0):
    kl_div = tf.reduce_sum(tf.maximum(free_bits,
                                      0.5 * (tf.square(mean) + tf.exp(2 * log_sigma) - 2 * log_sigma - 1)))
    kl_div /= float(batch_size)
    return kl_div

if __name__ == "__main__":
	create_network((199, 199, 199), (68, 68, 68), 'train_net')

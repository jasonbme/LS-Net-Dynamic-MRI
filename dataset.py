import tensorflow as tf
import os
import scipy.io as scio
import numpy as np

# GPU setup
#os.environ['CUDA_VISIBLE_DEVICES'] = '5'
#GPUs = tf.config.experimental.list_physical_devices('GPU')
#tf.config.experimental.set_memory_growth(GPUs[0], True)


def get_dataset(mode, dataset_name, batch_size, shuffle=False):
    if dataset_name == 'DYNAMIC_V2_MULTICOIL':  # multi-coil data
        dataset_suffix = 'cine_multicoil_'
        filenames = [os.path.join('data/20coil', dataset_suffix+mode+'.tfrecord')]

        dataset = tf.data.TFRecordDataset(filenames)
        dataset = dataset.map(parse_function)
        
    elif dataset_name == 'DYNAMIC_V2':          # single-coil data
        dataset_suffix = 'newdata_v2'
        k = np.load(os.path.join('data', mode+'_k_'+dataset_suffix+'.npy')).astype(np.complex64)
        label = np.load(os.path.join('data', mode+'_label_'+dataset_suffix+'.npy')).astype(np.complex64)
        k_dataset = tf.data.Dataset.from_tensor_slices(k)
        label_dataset = tf.data.Dataset.from_tensor_slices(label)
        dataset = tf.data.Dataset.zip((k_dataset, label_dataset))

    if shuffle:
        dataset = dataset.shuffle(buffer_size=50)
    dataset = dataset.batch(batch_size)
    
    return dataset


def parse_function(example_proto):
    dics = {'k_real': tf.io.VarLenFeature(dtype=tf.float32),
            'k_imag': tf.io.VarLenFeature(dtype=tf.float32),
            'label_real': tf.io.VarLenFeature(dtype=tf.float32),
            'label_imag': tf.io.VarLenFeature(dtype=tf.float32),
            'csm_real': tf.io.VarLenFeature(dtype=tf.float32),
            'csm_imag': tf.io.VarLenFeature(dtype=tf.float32),
            'k_shape': tf.io.FixedLenFeature(shape=(4,), dtype=tf.int64),
            'img_shape': tf.io.FixedLenFeature(shape=(3,), dtype=tf.int64),
            'csm_shape': tf.io.FixedLenFeature(shape=(4,), dtype=tf.int64)}
    parsed_example = tf.io.parse_single_example(example_proto, dics)
    parsed_example['k_real'] = tf.sparse.to_dense(parsed_example['k_real'])
    parsed_example['k_imag'] = tf.sparse.to_dense(parsed_example['k_imag'])
    parsed_example['label_real'] = tf.sparse.to_dense(parsed_example['label_real'])
    parsed_example['label_imag'] = tf.sparse.to_dense(parsed_example['label_imag'])
    parsed_example['csm_real'] = tf.sparse.to_dense(parsed_example['csm_real'])
    parsed_example['csm_imag'] = tf.sparse.to_dense(parsed_example['csm_imag'])

    k = tf.complex(parsed_example['k_real'], parsed_example['k_imag'])
    label = tf.complex(parsed_example['label_real'], parsed_example['label_imag'])
    csm = tf.complex(parsed_example['csm_real'], parsed_example['csm_imag'])
    
    k = tf.reshape(k, parsed_example['k_shape'])
    label = tf.reshape(label, parsed_example['img_shape'])
    csm = tf.reshape(csm, parsed_example['csm_shape'])

    return k, label, csm

import os
import shutil

from preprocessing import *
import multiprocessing
import tensorflow as tf


def get_record_raw(dataset):
    file = []
    for root, _, files in os.walk(dataset):
        for f in files:
            if '.hea' in f:
                file.append(os.path.join(root, f))
    return file


def get_record_preprocessed(mode):
    train_dir = PREPROCESSED_DATA_DIR + 'train/'
    eval_dir = PREPROCESSED_DATA_DIR + 'eval/'

    # Bước 1: Luôn tạo thư mục nếu chưa có
    if not os.path.exists(train_dir):
        os.makedirs(train_dir)
    if not os.path.exists(eval_dir):
        os.makedirs(eval_dir)

    # Bước 2: Luôn quét thư mục GỐC để di chuyển file
    # (Giả định PREPROCESSED_DATA_DIR là thư mục gốc chứa file .tfrecord)
    for file in os.listdir(PREPROCESSED_DATA_DIR):
        if file.endswith('.tfrecord') is False:
            continue
        
        file_path = PREPROCESSED_DATA_DIR + file
        if not os.path.isfile(file_path): # Bỏ qua thư mục con (như 'train', 'eval')
            continue

        # Kiểm tra file đã được di chuyển chưa
        target_dir = train_dir if (os.path.basename(file)).split('.')[0] in DS1 else eval_dir
        
        if not os.path.exists(target_dir + os.path.basename(file)):
            # Nếu chưa, di chuyển nó
            shutil.move(file_path, target_dir + os.path.basename(file))
        else:
            # Nếu file đã ở đúng chỗ, xóa file rác ở thư mục gốc
            os.remove(file_path)

    # Bước 3: Bây giờ mới trả về danh sách file
    return sorted(os.listdir(PREPROCESSED_DATA_DIR + mode))


def _bytes_feature(value):
    return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))


def _float_feature(value):
    return tf.train.Feature(float_list=tf.train.FloatList(value=value))


def _int64_feature(value):
    return tf.train.Feature(int64_list=tf.train.Int64List(value=value))


def save_tf_record(file_path, separate=None):
    file_name = os.path.splitext(os.path.basename(file_path))[0]
    if file_name.startswith('x_'):
        file_name = file_name[2:]
    if separate is not None:
        file_name += f".{int(separate)}"

    tfrecord_path = os.path.join(PREPROCESSED_DATA_DIR, file_name + '.tfrecord')

    if os.path.exists(tfrecord_path):
        print(f'File {file_name}.tfrecord đã tồn tại.')
        return

    data, label = preprocess_data(file_path, separate)
    label = tf.keras.utils.to_categorical(label, 2).astype('int8')
    print('filename:', file_name, 'data_shape=', data.shape, 'label_shape=', label.shape)

    with tf.io.TFRecordWriter(PREPROCESSED_DATA_DIR + file_name + '.tfrecord') as writer:
        for index in range(data.shape[0]):
            feature = {'image': _float_feature(data[index].flatten().tolist()),
                       'label': _int64_feature(label[index].flatten().tolist())}

            example = tf.train.Example(features=tf.train.Features(feature=feature))
            writer.write(example.SerializeToString())


def generate_data(data_set, separate=None, max_workers=4):
    """
    Generate data with a limited number of concurrent processes

    Args:
        data_set: List of file paths to process
        separate: Parameter to pass to save_tf_record
        max_workers: Maximum number of concurrent processes to use
    """
    print('Generating data...')
    if not os.path.exists(PREPROCESSED_DATA_DIR):
        os.makedirs(PREPROCESSED_DATA_DIR)

    # Process files in batches
    for i in range(0, len(data_set), max_workers):
        batch = data_set[i:i + max_workers]
        processes = []

        # Start processes for the current batch
        for file_path in batch:
            p = multiprocessing.Process(target=save_tf_record, args=(file_path, separate))
            processes.append(p)
            p.start()

        # Wait for all processes in the batch to finish
        for process in processes:
            process.join()

    print('Finish generating data...')

    # Process the second part if separate is provided
    if separate:
        print('Generating data part 2...')

        # Process files in batches for part 2
        for i in range(0, len(data_set), max_workers):
            batch = data_set[i:i + max_workers]
            processes = []

            # Start processes for the current batch
            for file_path in batch:
                p = multiprocessing.Process(target=save_tf_record, args=(file_path, separate + 1))
                processes.append(p)
                p.start()

            # Wait for all processes in the batch to finish
            for process in processes:
                process.join()

        print('Finish generating data part 2...')


def parse_batch(record_batch):
    # Create a description of the features
    feature_description = {
        'image': tf.io.FixedLenFeature([NEIGHBOUR_POINT, 1], tf.float32),
        'label': tf.io.FixedLenFeature([2], tf.int64),
    }
    example = tf.io.parse_example(record_batch, feature_description)
    example['label'] = tf.cast(example['label'], tf.int8)

    return example['image'], example['label']


def get_tf_records(data_set, batch_size, shuffle_buffer, prefetch_buffer, mode='train'):
    """mode = ['train', 'valid', 'test]"""
    # files = tf.data.Dataset.list_files(files)
    # ds = files.interleave(lambda x: tf.data.TFRecordDataset(x).prefetch(100)
    #                       , num_parallel_calls=os.cpu_count())
    # ds = tf.data.TFRecordDataset(PREPROCESSED_TEST_DATA_RECORD_DIR + filename + '.tfrecord',
    #                              num_parallel_reads=os.cpu_count())
    if type(data_set) != list:
        data_set = [data_set]
    files = [PREPROCESSED_DATA_DIR + mode + "/{}".format(i) for i in data_set]

    ds = tf.data.TFRecordDataset(files, num_parallel_reads=os.cpu_count())
    ds = ds.map(parse_batch, num_parallel_calls=os.cpu_count())
    if mode == 'train':
        ds = ds.shuffle(shuffle_buffer, reshuffle_each_iteration=True)
        ds = ds.repeat()
    ds = ds.batch(batch_size)
    ds = ds.prefetch(prefetch_buffer)

    return ds

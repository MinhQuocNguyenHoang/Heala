import wfdb
import numpy as np
import scipy.signal as spysig
import scipy.ndimage as spynd
from scipy.signal import lfilter, firwin
from define import *
import os
import matplotlib.pyplot as plt
np.seterr(divide='ignore')


def baseline_wander_remove(signal, fs=250, f1=0.2, f2=0.6):
    # Tính kích thước cửa sổ lọc median cho từng giai đoạn
    # Nếu kết quả là số chẵn thì giảm đi 1 để thành số lẻ (median filter yêu cầu window size lẻ)
    window1 = int(f1 * fs) - 1 if int(f1 * fs) % 2 == 0 else int(f1 * fs)
    window2 = int(f2 * fs) - 1 if int(f2 * fs) % 2 == 0 else int(f2 * fs)

    # Lọc median lần 1 để loại bỏ nhiễu đột biến nhỏ
    med_signal_0 = spysig.medfilt(signal, window1)

    # Lọc median lần 2 (với cửa sổ lớn hơn) để ước lượng đường nền (baseline)
    med_signal_1 = spysig.medfilt(med_signal_0, window2)

    # Trừ baseline ra khỏi tín hiệu gốc → loại bỏ trôi đường nền (baseline wander)
    bwr_signal = signal - med_signal_1

    # Thiết kế bộ lọc FIR thông thấp (Hamming window), cắt tại 35 Hz để lọc thêm nhiễu cao tần
    taps = firwin(12, 35 / fs, window='hamming')

    # Áp dụng bộ lọc FIR vào tín hiệu sau khi loại bỏ baseline
    bwr_signal = lfilter(taps, 1.0, bwr_signal)

    return bwr_signal


# chuẩn hóa tín hiệu
def normalize(signal, fs=250, window=0.5):
    # window: kích thước cửa sổ tính toán (tính theo số mẫu)
    window = int(window * fs)

    # Lọc cực đại và cực tiểu trong cửa sổ trượt
    # → lấy được bao bọc trên/dưới của tín hiệu
    max_signal_f = spynd.maximum_filter1d(signal, window)
    min_signal_f = spynd.minimum_filter1d(signal, window)

    # Lấy giá trị tuyệt đối lớn nhất giữa cực đại và cực tiểu
    # → độ lớn biên (envelope amplitude)
    max_signal_g = np.maximum(np.absolute(max_signal_f), np.absolute(min_signal_f))

    # Làm mượt (average filter) để giảm dao động nhanh
    ave_signal = spysig.convolve(max_signal_g, np.ones(window), mode='same') / window

    # Ngưỡng tối thiểu để tránh chia cho số quá nhỏ
    bound = np.mean(ave_signal) / 2

    # Giới hạn (clip) biên độ trung bình xuống không nhỏ hơn bound
    ave_signal = np.clip(ave_signal, a_min=bound, a_max=None)

    # Chuẩn hóa: chia tín hiệu gốc cho biên độ trung bình
    nor_signal = signal / ave_signal

    return nor_signal

# gán nhãn label cho tín hiệu
def preprocess_data(file_path, separate=None):
    file_path = file_path[:-4]
    info = wfdb.rdheader(file_path)
    signal_length = info.sig_len
    if separate == 1:
        signal, _ = wfdb.rdsamp(file_path, channels=[1], sampfrom=0, sampto=signal_length//2)
        annotation = wfdb.rdann(file_path, 'atr', sampfrom=0, sampto=signal_length//2)
        signal_length = signal_length//2
    elif separate == 2:
        signal, _ = wfdb.rdsamp(file_path, channels=[1], sampfrom=signal_length//2, sampto=signal_length)
        annotation = wfdb.rdann(file_path, 'atr', sampfrom=signal_length//2, sampto=signal_length)
        annotation.sample = annotation.sample - (info.sig_len - info.sig_len // 2)
        signal_length = signal_length - signal_length // 2
    else:
        signal, _ = wfdb.rdsamp(file_path, channels=[1])
        annotation = wfdb.rdann(file_path, 'atr')

    signal.astype(DATA_TYPE)
    signal = np.squeeze(signal)

    if info.fs != FREQUENCY_SAMPLING:
        signal_length = int(FREQUENCY_SAMPLING / info.fs * signal_length)
        signal = spysig.resample(signal, signal_length)
        annotation.sample = annotation.sample * FREQUENCY_SAMPLING / info.fs
        annotation.sample = annotation.sample.astype('int')
    signal.astype(DATA_TYPE)

    signal = baseline_wander_remove(signal, FREQUENCY_SAMPLING, 0.2, 0.6)
    signal = normalize(signal, FREQUENCY_SAMPLING, 0.5)
    # Data and labelling
    data_sample = []
    for i in range(signal_length - (NEIGHBOUR_POINT - 1)):
        data_sample.append(signal[i:i + NEIGHBOUR_POINT])

    
    data_sample = np.expand_dims(np.array(data_sample, dtype='float32'), axis=2)

    label = np.zeros(signal_length, dtype='int8')
    for i in range(annotation.ann_len):
        if annotation.symbol[i] in ['+', '~', '|', '[', '!', ']', '"', 's', 'x']:
            continue
        label[annotation.sample[i] - POSITIVE_RANGE:annotation.sample[i] + POSITIVE_RANGE + 1] = 1
    label = np.array(label[int(0.1*FREQUENCY_SAMPLING):signal_length - int(0.3*FREQUENCY_SAMPLING)], dtype='int8')
    return data_sample, label

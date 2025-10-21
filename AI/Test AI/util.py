import numpy as np
from define import *
import wfdb
import os

def calculate_average_bpm(peak_indices, fs):
    """
    Tính BPM trung bình từ một danh sách các vị trí đỉnh.
    fs: Tần số lấy mẫu (ví dụ: 125 Hz)
    """
    if len(peak_indices) < 2:
        return 0.0 # Không thể tính nếu có ít hơn 2 đỉnh
        
    # 1. Tính khoảng cách (bằng giây) giữa các đỉnh
    #    np.diff(peak_indices) -> khoảng cách bằng "số mẫu"
    rr_intervals_sec = np.diff(peak_indices) / fs
    
    # 2. Loại bỏ các giá trị bất thường (ví dụ: nhịp < 40 hoặc > 200)
    #    (60/200 = 0.3s, 60/40 = 1.5s)
    rr_intervals_sec = rr_intervals_sec[(rr_intervals_sec > 0.4) & (rr_intervals_sec < 1.5)]
    
    if len(rr_intervals_sec) == 0:
        return 0.0
        
    # 3. Tính BPM (nhịp/phút)
    bpm_values = 60.0 / rr_intervals_sec
    
    # 4. Trả về BPM trung bình
    return np.mean(bpm_values)

def clustering(data):
    positive_point = np.where(data == 1)[0]
    beat = []
    if len(positive_point) > 1:
        cluster = np.array([positive_point[0]])
        for i in range(1, len(positive_point)):
            if positive_point[i] - cluster[-1] > 0.08 * FREQUENCY_SAMPLING or i == len(positive_point) - 1:
                if i == len(positive_point) - 1:
                    cluster = np.append(cluster, positive_point[i])
                if cluster.shape[0] > 5:
                    beat.append(int(np.mean(cluster)))
                cluster = np.array([positive_point[i]])
            else:
                cluster = np.append(cluster, positive_point[i])

    return np.asarray(beat)


# def evaluate(file, predicted, dataset, ec57=False):
#     header = wfdb.rdheader(os.path.join(dataset, file))
#     signal_length = header.sig_len
#     annotation = wfdb.rdann(os.path.join(dataset, file), 'atr')
#     # if file.split('.')[1] == '1':
#     #     annotation = wfdb.rdann(LTDB_DIR + file, 'atr', )
#     # else:
#     #     annotation = wfdb.rdann(LTDB_DIR + file, 'atr', )

#     fs = header.fs
#     if fs != FREQUENCY_SAMPLING:
#         signal_length = int(FREQUENCY_SAMPLING / fs * signal_length)
#         annotation.sample = annotation.sample * FREQUENCY_SAMPLING / fs
#         annotation.sample = annotation.sample.astype('int')

#     # condition = np.isin(annotation.symbol, ['+', '~', '|', '[', '!', ']', '"', 's', 'x'], invert=True)
#     condition = np.isin(annotation.symbol,
#                         ['[', '!', ']', 'x', '(', ')', 'p', 't', 'u', '`', '\'',
#                          '^', '|', '~', '+', 's', 'T', '*', 'D', '=', '"', '@'], invert=True)
#     sample = np.extract(condition, annotation.sample)
#     cluster = clustering(np.expand_dims(predicted[0:, 1], axis=1)) + int(0.1 * FREQUENCY_SAMPLING)
#     window = int(0.075 * FREQUENCY_SAMPLING)

#     if ec57:
#         ann_dir = TEMP_DIR + dataset.split('/')[-2] + '/'
#         symbol = ['N' for _ in range(sample.shape[0])]
#         symbol = np.asarray(symbol)
#         wfdb.wrann(file, extension='atr', sample=sample, symbol=symbol, write_dir=ann_dir, fs=250)
#         symbol = ['N' for _ in range(cluster.shape[0])]
#         symbol = np.asarray(symbol)
#         wfdb.wrann(file, extension='pred', sample=cluster, symbol=symbol, write_dir=ann_dir, fs=250)
#         return

#     recording = np.zeros(signal_length, dtype='int32')
#     detection = np.zeros(signal_length, dtype='int32')

#     np.put(recording, sample, 1)
#     np.put(detection, cluster, 1)

#     true_positive = 0
#     false_positive = 0
#     false_negative = 0

#     for i in range(len(sample)):
#         if sum(detection[sample[i] - window:sample[i] + window + 1]) > 0:
#             true_positive = true_positive + 1
#         else:
#             false_negative = false_negative + 1
#     for i in range(len(cluster)):
#         if sum(recording[cluster[i] - window:cluster[i] + window + 1]) == 0:
#             false_positive = false_positive + 1

#     sensitivity = true_positive / (true_positive + false_negative)
#     positive_value = true_positive / (true_positive + false_positive)

#     return true_positive, false_negative, false_positive, sensitivity, positive_value

# Tính BPM và sai số so với BPM chuẩn
def evaluate(file, predicted, dataset, ec57=False):
    # --- PHẦN 1: LẤY ĐỈNH "THẬT" (TRUE PEAKS) ---
    header = wfdb.rdheader(os.path.join(dataset, file))
    signal_length = header.sig_len
    annotation = wfdb.rdann(os.path.join(dataset, file), 'atr')

    fs = header.fs # Tần số gốc (ví dụ: 500)
    
    # Quan trọng: Phải "giảm mẫu" vị trí đỉnh thật để khớp với
    # tần số mới (ví dụ: 125)
    if fs != FREQUENCY_SAMPLING:
        signal_length = int(FREQUENCY_SAMPLING / fs * signal_length)
        annotation.sample = annotation.sample * FREQUENCY_SAMPLING / fs
        annotation.sample = annotation.sample.astype('int')
    
    # Lọc bỏ các ký hiệu không phải là nhịp đập
    condition = np.isin(annotation.symbol,
                        ['[', '!', ']', 'x', '(', ')', 'p', 't', 'u', '`', '\'',
                         '^', '|', '~', '+', 's', 'T', '*', 'D', '=', '"', '@'], invert=True)
    true_peaks = np.extract(condition, annotation.sample)

    # --- PHẦN 2: LẤY ĐỈNH "DỰ ĐOÁN" (PREDICTED PEAKS) ---
    # 'predicted' là output từ model, đã qua np.rint()
    # có shape (số cửa sổ, 2)
    
    # Lấy cột "is_peak" (cột 1)
    predicted_class_1 = predicted[:, 1]
    
    # Dùng clustering để tìm vị trí đỉnh dự đoán
    # (Cộng bù lại 0.1*FS đã bị cắt ở preprocessing.py)
    predicted_peaks = clustering(predicted_class_1) + int(0.1 * FREQUENCY_SAMPLING)

    # --- PHẦN 3: TÍNH TOÁN VÀ TRẢ VỀ BPM ---
    # (Dùng hàm mới đã tạo ở trên)
    
    bpm_true = calculate_average_bpm(true_peaks, FREQUENCY_SAMPLING)
    bpm_pred = calculate_average_bpm(predicted_peaks, FREQUENCY_SAMPLING)

    # Trả về BPM thay vì TP/FN/FP
    return bpm_true, bpm_pred

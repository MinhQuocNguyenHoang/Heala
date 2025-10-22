TEST_TIME = 'run-0'
# DATABASE = 'ltdb/'
DATABASE = 'mitdb/'
PROJECT_DIR = './qrs_detection_dataset/'

SAVE_MODEL_DIR = PROJECT_DIR + 'model/' + DATABASE
TEMP_DIR = PROJECT_DIR + 'temp/'
TENSOR_BOARD_DIR = PROJECT_DIR + 'log/' + DATABASE
RESULT_DIR = PROJECT_DIR + 'result/' + DATABASE


# LTDB_DIR = '/mnt/Data_1T/PhysionetData/ltdb/'
# MITDB_DIR = '/mnt/Data_1T/PhysionetData/mitdb/'
# AHADB_DIR = '/mnt/Data_1T/PhysionetData/ahadb/'
# ESCDB_DIR = '/mnt/Data_1T/PhysionetData/escdb/'
# NSTDB_DIR = '/mnt/Data_1T/PhysionetData/nstdb/'

PREPROCESSED_DATA_DIR = './qrs_detection_dataset/' + DATABASE
CHECK_POINT_DIR = './qrs_detection_dataset/checkpoint/' + DATABASE

FREQUENCY_SAMPLING = 200
NEIGHBOUR_POINT = int(FREQUENCY_SAMPLING * 0.1) + int(FREQUENCY_SAMPLING * 0.3) + 1
POSITIVE_RANGE = int(FREQUENCY_SAMPLING * 0.04) + 1

DATA_TYPE = 'float32'

DS1 = ['s1_run', 's1_walk', 's2_run', 's2_walk', 's3_run', 's3_walk', 's4_run', 's4_walk', 's5_run', 's5_walk', 's6_run', 's6_walk', 's7_run', 's7_walk', 's8_run', 's8_walk', 's9_run', 's9_walk', 's10_run', 's10_walk', 's11_run','s11_walk','s12_run','s12_walk'
       ,'s13_run','s13_walk','s14_run','s14_walk','s15_run','s15_walk','s16_run','s16_walk','s17_run','s17_walk','s18_run','s18_walk','s19_run','s19_walk','s20_run','s20_walk','s21_run','s21_walk','s22_run','s22_walk']
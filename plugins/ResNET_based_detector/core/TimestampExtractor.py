import numpy as np
from os import path
from glob import glob
from scipy.ndimage import binary_closing, binary_opening
from natsort import natsorted


class TimestampExtractor:
    def __init__(self, config) -> None:
        self.min_pair_resolution_secs = config["min_pair_resolution_secs"]
        self.min_pair_length_secs = config["min_pair_length_secs"]
        self.std_scaling_param = config["std_scaling_param"]

    def get_events_timestamps(self, folder_with_npy_vectors_path):
        mean_vec = self._calc_mean_vec(folder_with_npy_vectors_path)
        cos_similarities, timestamps = self._calc_cos_similarities_to_timestamps(
            mean_vec, folder_with_npy_vectors_path
        )

        # операция аналогичная поиску в пределах сигма окрестности от среднего
        events_time_mask = (
            (1 - cos_similarities) > self.std_scaling_param * np.std(cos_similarities)
        ).astype(int)

        start_stop_pairs = self._get_start_stop_pair_indexes(
            events_time_mask,
            np.ceil(self.min_pair_length_secs / (timestamps[1] - timestamps[0])).astype(int),
            np.ceil(self.min_pair_resolution_secs / (timestamps[1] - timestamps[0])).astype(int),
        )

        return [
            {"start": int(timestamps[start]), "stop": int(timestamps[stop])}
            for start, stop in start_stop_pairs
            if stop - start > 0
        ]

    def _calc_mean_vec(self, folder_with_npy_vectors_path):
        vec_sum = 0
        vec_count = 0
        for vec_file_path in glob(f"{folder_with_npy_vectors_path}/*.npy"):
            vec = np.load(vec_file_path)
            vec_sum += vec
            vec_count += 1

        return vec_sum / vec_count

    def _calc_cos_similarities_to_timestamps(self, mean_vec, folder_with_npy_vectors_path):
        cos_similarities = []
        timestamps = []
        for vec_file_path in natsorted(glob(f"{folder_with_npy_vectors_path}/*.npy")):
            vec = np.load(vec_file_path)
            cos_sim = np.dot(vec, mean_vec) / (np.linalg.norm(vec) * np.linalg.norm(mean_vec))
            timestamp = int(path.basename(vec_file_path[:-4]))
            cos_similarities.append(cos_sim)
            timestamps.append(timestamp)

        return np.array(cos_similarities), np.array(timestamps)

    def _get_start_stop_pair_indexes(self, events_time_mask, min_pair_length, min_pair_resolution):
        time_series = np.append(np.insert(events_time_mask, 0, 0), 0)
        if min_pair_resolution > 0:
            time_series = binary_closing(time_series, [1] * min_pair_resolution).astype(int)
        if min_pair_length > 0:
            time_series = binary_opening(time_series, [1] * min_pair_length).astype(int)

        diff = time_series[1:] - time_series[:-1]
        starts = np.where(diff > 0)[0]
        ends = np.where(diff < 0)[0] - 1

        return list(zip(starts, ends))

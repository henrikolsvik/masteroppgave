import sklearn.model_selection
import time
import numpy as np
import datetime
import os.path
from sklearn.feature_selection import SelectKBest, SelectPercentile
from sklearn.preprocessing import Normalizer


class Mlinterface:

    def __init__(self):
        self.config = None
        self.timekeeping = {"Start_time:": datetime.datetime.now()}

    def count_targets(self, target):
        num_targets = {}
        for i in range(0, len(target)):
            if target[i] not in num_targets:
                num_targets[target[i]] = 1
            else:
                num_targets[target[i]] += 1

        print("Type count")
        print(num_targets)
        return num_targets

    def targets_to_int(self, target):
        num_targets = {}
        for i in range(0, len(target)):
            if target[i] not in num_targets:
                num_targets[target[i]] = len(num_targets)
            target[i] = num_targets[target[i]]

        print("Binarified target files")
        print(num_targets)
        return target

    def read_config(self, file):
        data = open(file, "r")
        settings = {}
        for line in data:
            if line[0] != "#":
                settings[line.split("=")[0]] = line.split("=")[1].replace("\n", "")
        self.config = settings

    def write_results(self, output_filename, input_samples, input_samples_parameter, score, target):
        self.timekeeping["End_time:"] = datetime.datetime.now()
        self.timekeeping["Total_time:"] = (self.timekeeping["End_time:"] - self.timekeeping["Start_time:"]).total_seconds()
        self.write_txt_results(output_filename, target, score)
        self.write_csv_results(input_samples, input_samples_parameter, target, score)

    def write_csv_results(self, input_samples, input_samples_parameter, target, score):
        print(type(self))
        if not os.path.isfile("results/combined_results.csv"):
            open("results/combined_results.csv", "a").write("Algorithm;Runtime in Seconds;Score;Score_STD;Baseline;Start_time;End_time;Parameters;Samples_name;Preprocessing_config\n")
        open("results/combined_results.csv", "a").write(
            type(self).__name__ + ";" +
            str(self.timekeeping["Total_time:"]) + ";" +
            str(np.array(score).sum() / len(score)) + ";" +
            str(np.array(score).std()) + ";" +
            str(self.get_baseline_accuracy(target)) + ";" +
            str(self.timekeeping["Start_time:"]) + ";" +
            str(self.timekeeping["End_time:"]) + ";" +
            str(self.config) + ";" +
            str(input_samples) + ";" +
            str([str(x).replace("\n", "") for x in (open(input_samples_parameter, "r").readlines())]) + "\n")

    def write_txt_results(self, output_filename, target, score):
        file = open(output_filename, "w")
        file.write("FILE: " + output_filename + "\n")
        file.write("Baseline accuracy: {0:.2f}%".format(self.get_baseline_accuracy(target)) + "\n")
        file.write(self.generate_result_text(score))
        file.write(str(self.config))
        file.close()

    def get_baseline_accuracy(self, target):
        target_counts = self.count_targets(target)
        max_count, count = 0, 0
        for item in target_counts:
            if target_counts[item] > max_count:
                max_count = target_counts[item]
            count += target_counts[item]
        return (max_count / count) * 100

    def generate_result_text(self, score):
        return "Total Accuracy Score Of: " + "{:.2f}".format(np.array(score).sum() / len(score) * 100) \
               + "%.\n" + "Results of individual runs: " + str(score) + "\n**** \nConfig:\n"

    def load_files(self, input_samples_file, input_target_file):

        return Mlinterface.read_sample_file(self, input_samples_file), Mlinterface.read_target_file(self,
                                                                                                    input_target_file)

    def read_sample_file(self, filename):
        file = open(filename, "r")
        lines = file.readlines()
        data = []
        sample_names = []
        for i in range(1, len(lines)):
            line = lines[i].replace("\n", "")
            line = line.split(",")
            sample_names.append(line.pop(0))
            line_float = []
            for element in line:
                line_float.append(float(element))
            data.append(line_float)
        file.close()

        return [data, sample_names]

    def read_target_file(self, filename):
        file = open(filename, "r")
        lines = file.readlines()
        data = []
        for i in range(0, len(lines)):
            line = lines[i].replace("\n", "")
            line = line.split(",")
            data.append(line[1])
        file.close()

        return data

    def do_usf(self, input_samples, target):
        if self.config["ufs_stage"] == "pre":
            samples = []
            for i in range(0, len(input_samples[0])):
                samples.append(input_samples[0][i])
                target[i] = int(target[i])
        else:
            samples = input_samples

        if self.config["ufs_type"] == "percent":
            filtered_terms = SelectPercentile(percentile=int(self.config["ufs_number"])).fit_transform(samples, target)
        elif self.config["ufs_type"] == "count":
            filtered_terms = SelectKBest(k=int(self.config["ufs_number"])).fit_transform(samples, target)

        if self.config["ufs_stage"] == "pre":
            names = []
            for i in range(0, len(input_samples[0])):
                names.append(input_samples[1][i])
            return [filtered_terms, names]
        return filtered_terms

    def make_predictions(self, clf, train_sample, train_target, test_sample, test_target, test_name):
        predictions, score = [], []
        for i in range(0, len(train_sample)):
            clf.fit(np.array(train_sample[i]), np.array(train_target[i]))
            score.append(clf.score(np.array(test_sample[i]), np.array(test_target[i])))
            predictions.append([test_name[i], clf.predict(np.array(test_sample[i])), test_target[i]])

        return score, predictions

    def make_predictions_plc(self, clf, train_sample, train_target, test_sample, test_target, test_name):
        predictions, score = [], []
        for i in range(0, len(train_sample)):
            clf.fit(train_sample[i], train_target[i])
            score.append(clf.score(test_sample[i], test_target[i]))
            predictions.append([test_name[i], clf.predict(test_sample[i]), test_target[i]])

        return score, predictions

    def n_split_shuffle(self, samples, target, n):
        bound_samples_and_targets, train_sample, test_sample, test_target, train_target, test_name = [], [], [], [], [], []

        if bool(self.config["normalize"]):
            samples[0] = Normalizer().fit_transform(samples[0])


        for i in range(0, len(samples[1])):
            bound_samples_and_targets.append([samples[1][i], samples[0][i], target[i]])

        kf = sklearn.model_selection.KFold(n, shuffle=True, random_state=int(time.time())) \
            .split(bound_samples_and_targets)

        for items in kf:
            train_add_sample, train_add_target, test_add_sample, test_add_target, test_add_name = [], [], [], [], []

            for item in items[0]:
                train_add_sample.append(bound_samples_and_targets[item][1])
                train_add_target.append(bound_samples_and_targets[item][2])
            for item in items[1]:
                test_add_name.append(bound_samples_and_targets[item][0])
                test_add_sample.append(bound_samples_and_targets[item][1])
                test_add_target.append(bound_samples_and_targets[item][2])

            if self.config["ufs_stage"] == "kfold":
                train = self.do_usf(train_add_sample, train_add_target)
                train_add_sample = train
                test = self.do_usf(test_add_sample, test_add_target)
                test_add_sample = test

            train_sample.append(train_add_sample)
            train_target.append(train_add_target)
            test_sample.append(test_add_sample)
            test_target.append(test_add_target)
            test_name.append(test_add_name)

        return train_sample, train_target, test_sample, test_target, test_name

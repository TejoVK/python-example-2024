#!/usr/bin/env python

# Do *not* edit this script.
# These are helper functions that you can use with your code.
# Check the example code to see how to import these functions to your code.

import numpy as np
import os
import sys

### Challenge data I/O functions

# Find the records in a folder and its subfolders.
def find_records(folder):
    records = set()
    for root, directories, files in os.walk(folder):
        for file in files:
            extension = os.path.splitext(file)[1]
            if extension == '.hea':
                record = os.path.relpath(os.path.join(root, file), folder)[:-4]
                records.add(record)
    records = sorted(records)
    return records

# Load the image(s) for a record.
def load_image(record):
    from PIL import Image

    path = os.path.split(record)[0]
    header_file = get_header_file(record)
    header = load_text(header_file)
    image_files = get_images(header)

    if len(image_files) == 0:
        raise FileNotFoundError(f'There are no images for record {record}.')

    images = list()
    for image_file in image_files:
        image_file_path = os.path.join(path, image_file)
        if os.path.isfile(image_file_path):
            image = Image.open(image_file_path)
            images.append(image)

    return images

# Load the signal(s) for a record.
def load_signal(record):
    import wfdb

    signal_files = get_signal_files(record)
    if signal_files:
        signal, fields = wfdb.rdsamp(record)
    else:
        signal, fields = None, None
    return signal, fields

# Load the diagnosis or diagnoses for a record.
def load_diagnosis(record):
    header_file = get_header_file(record)
    header = load_text(header_file)
    diagnosis = get_diagnosis(header)
    return diagnosis

# Save the signal(s) for a record.
def save_signal(record, signal):
    header_file = get_header_file(record)
    header = load_text(header_file)

    path, record = os.path.split(record)
    sampling_frequency = get_sampling_frequency(header)
    signal_formats = get_signal_formats(header)
    adc_gains = get_adc_gains(header)
    baselines = get_baselines(header)
    signal_units = get_signal_units(header)
    signal_names = get_signal_names(header)

    if all(signal_format == '16' for signal_format in signal_formats):
        signal = np.clip(signal, -2**15 + 1, 2**15 - 1)
        signal = np.asarray(signal, dtype=np.int16)
    else:
        signal_format_string = ', '.join(sorted(set(signal_formats)))
        raise NotImplementedError(f'{signal_format_string} not implemented')

    import wfdb
    wfdb.wrsamp(record, fs=sampling_frequency, units=signal_units, sig_name=signal_names, \
                d_signal=signal, fmt=signal_formats, adc_gain=adc_gains, baseline=baselines, write_dir=path)

    return header

# Save the diagnosis or diagnoses for a record.
def save_diagnosis(record, diagnosis):
    header_file = get_header_file(record)
    header = load_text(header_file)
    header += '#Dx: ' + ', '.join(diagnosis) + '\n'
    save_text(header_file, header)

### Helper Challenge functions

# Load a text file as a string.
def load_text(filename):
    with open(filename, 'r') as f:
        string = f.read()
    return string

# Save a string as a text file.
def save_text(filename, string):
    with open(filename, 'w') as f:
        f.write(string)

# Get the record name from a header file.
def record(string):
    value = string.split('\n')[0].split(' ')[0].split('/')[0].strip()
    return value

# Get the number of signals from a header file.
def get_num_signals(string):
    value = string.split('\n')[0].split(' ')[1].strip()
    if is_integer(value):
        value = int(value)
    else:
        value = None
    return value

# Get the sampling frequency from a header file.
def get_sampling_frequency(string):
    value = string.split('\n')[0].split(' ')[2].split('/')[0].strip()
    if is_number(value):
        value = float(value)
    else:
        value = None
    return value

# Get the number of samples from a header file.
def get_num_samples(string):
    value = string.split('\n')[0].split(' ')[3].strip()
    if is_integer(value):
        value = int(value)
    else:
        value = None
    return value

# Get signal units from a header file.
def get_signal_formats(string):
    num_signals = get_num_signals(string)
    values = list()
    for i, l in enumerate(string.split('\n')):
        if 1 <= i <= num_signals:
            field = l.split(' ')[1]
            if 'x' in field:
                field = field.split('x')[0]
            if ':' in field:
                field = field.split(':')[0]
            if '+' in field:
                field = field.split('+')[0]
            value = field
            values.append(value)
    return values

# Get signal units from a header file.
def get_adc_gains(string):
    num_signals = get_num_signals(string)
    values = list()
    for i, l in enumerate(string.split('\n')):
        if 1 <= i <= num_signals:
            field = l.split(' ')[2]
            if '/' in field:
                field = field.split('/')[0]
            if '(' in field and ')' in field:
                field = field.split('(')[0]
            value = float(field)
            values.append(value)
    return values

# Get signal units from a header file.
def get_baselines(string):
    num_signals = get_num_signals(string)
    values = list()
    for i, l in enumerate(string.split('\n')):
        if 1 <= i <= num_signals:
            field = l.split(' ')[2]
            if '/' in field:
                field = field.split('/')[0]
            if '(' in field and ')' in field:
                field = field.split('(')[1].split(')')[0]
            value = int(field)
            values.append(value)
    return values

# Get signal units from a header file.
def get_signal_units(string):
    num_signals = get_num_signals(string)
    values = list()
    for i, l in enumerate(string.split('\n')):
        if 1 <= i <= num_signals:
            field = l.split(' ')[2]
            if '/' in field:
                value = field.split('/')[1]
            else:
                value = 'mV'
            values.append(value)
    return values

# Get the number of samples from a header file.
def get_signal_names(string):
    num_signals = get_num_signals(string)
    values = list()
    for i, l in enumerate(string.split('\n')):
        if 1 <= i <= num_signals:
            value = l.split(' ')[8]
            values.append(value)
    return values

# Get a variable from a string.
def get_variable(string, variable_name):
    variable = None
    for l in string.split('\n'):
        if l.startswith(variable_name):
            variable = l[len(variable_name):].strip()
    return variable

# Get variables from a text file.
def get_variables(string, variable_name, sep=','):
    variables = list()
    for l in string.split('\n'):
        if l.startswith(variable_name):
            variables += [variable.strip() for variable in l[len(variable_name):].strip().split(sep)]
    return variables

# Get the diagnosis or diagnoses from a header or a similar string.
def get_diagnosis(string):
    diagnosis = get_variables(string, '#Dx:')
    if len(diagnosis) > 0:
        return diagnosis
    else:
        raise Exception('No diagnosis available: are you trying to load the diagnoses from the held-out dataset?')

# Get the diagnosis or diagnoses from a header or a similar string.
def get_diagnoses(string):
    return get_diagnosis(string)

# Get the image or images from a header or a similar string.
def get_image(string):
    return get_variables(string, '#Image:')

# Get the image or images from a header or a similar string.
def get_images(string):
    return get_image(string)

# Get the header file for a record.
def get_header_file(record):
    if not record.endswith('.hea'):
        header_file = record + '.hea'
    else:
        header_file = record
    return header_file

# Get the signal file(s) for a record.
def get_signal_files(record):
    header_file = get_header_file(record)
    header = load_text(header_file)

    signal_files = list()
    for i, l in enumerate(header.split('\n')):
        arrs = [arr.strip() for arr in l.split(' ')]
        if i==0 and not l.startswith('#'):
            num_channels = int(arrs[1])
        elif i<=num_channels and not l.startswith('#'):
            signal_file = arrs[0]
            if signal_file not in signal_files:
                signal_files.append(signal_file)
        else:
            break

    return signal_files

# Get the image files for a record.
def get_image_files(record):
    header_file = get_header_file(record)
    header = load_text(header_file)
    image_files = get_variables(header, '#Image:')
    return image_files

### Evaluation functions

# Construct the binary one-vs-rest confusion matrices, where the columns are the expert labels and the rows are the classifier
# for the given classes.
def compute_one_vs_rest_confusion_matrix(labels, outputs, classes):
    assert np.shape(labels) == np.shape(outputs)

    num_instances = len(labels)
    num_classes = len(classes)

    A = np.zeros((num_classes, 2, 2))
    for i in range(num_instances):
        for j in range(num_classes):
            if labels[i, j] == 1 and outputs[i, j] == 1: # TP
                A[j, 0, 0] += 1
            elif labels[i, j] == 0 and outputs[i, j] == 1: # FP
                A[j, 0, 1] += 1
            elif labels[i, j] == 1 and outputs[i, j] == 0: # FN
                A[j, 1, 0] += 1
            elif labels[i, j] == 0 and outputs[i, j] == 0: # TN
                A[j, 1, 1] += 1

    return A

# Compute macro F-measure.
def compute_f_measure(labels, outputs):
    # Compute confusion matrix.
    classes = sorted(set.union(*map(set, labels)))
    labels = compute_one_hot_encoding(labels, classes)
    outputs = compute_one_hot_encoding(outputs, classes)
    A = compute_one_vs_rest_confusion_matrix(labels, outputs, classes)

    num_classes = len(classes)
    per_class_f_measure = np.zeros(num_classes)
    for k in range(num_classes):
        tp, fp, fn, tn = A[k, 0, 0], A[k, 0, 1], A[k, 1, 0], A[k, 1, 1]
        if 2 * tp + fp + fn > 0:
            per_class_f_measure[k] = float(2 * tp) / float(2 * tp + fp + fn)
        else:
            per_class_f_measure[k] = float('nan')

    if np.any(np.isfinite(per_class_f_measure)):
        macro_f_measure = np.nanmean(per_class_f_measure)
    else:
        macro_f_measure = float('nan')

    return macro_f_measure, per_class_f_measure, classes

# Reorder channels in signal.
def reorder_signal(input_signal, input_channels, output_channels):
    if input_signal is None:
        return None

    if input_channels == output_channels and len(set(input_channels)) == len(set(output_channels)) == len(output_channels):
        output_signal = input_signal
    else:
        input_channels = [channel.strip().casefold() for channel in input_channels]
        output_channels = [channel.strip().casefold() for channel in output_channels]

        num_samples = np.shape(input_signal)[0]
        num_channels = len(output_channels)
        data_type = input_signal.dtype
        output_signal = np.zeros((num_samples, num_channels), dtype=data_type)

        for i, output_channel in enumerate(output_channels):
            for j, input_channel in enumerate(input_channels):
                if input_channel == output_channel:
                    output_signal[:, i] += input_signal[:, j]

    return output_signal

# Pad or truncate signal.
def trim_signal(input_signal, num_samples):
    if input_signal is None:
        return None

    cur_samples, num_channels = np.shape(input_signal)
    data_type = input_signal.dtype

    if cur_samples == num_samples:
        output_signal = input_signal
    else:
        output_signal = np.zeros((num_samples, num_channels), dtype=data_type)
        if cur_samples < num_samples: # Zero-pad the signals.
            output_signal[:cur_samples, :] = input_signal
        else: # Truncate the signals.
            output_signal = input_signal[:num_samples, :]

    return output_signal

# Compute SNR.
def compute_snr(label_signal, output_signal):
    if label_signal is None or output_signal is None:
        return None

    assert(np.all(np.shape(label_signal) == np.shape(output_signal)))

    label_signal[np.isnan(label_signal)] = 0
    output_signal[np.isnan(output_signal)] = 0

    noise_signal = output_signal - label_signal

    x = np.sum(label_signal**2)
    y = np.sum(noise_signal**2)

    if y > 0:
        snr = 10 * np.log10(x / y)
    else:
        snr = float('inf')

    return snr

### Other helper functions

# Check if a variable is a number or represents a number.
def is_number(x):
    try:
        float(x)
        return True
    except (ValueError, TypeError):
        return False

# Check if a variable is an integer or represents an integer.
def is_integer(x):
    if is_number(x):
        return float(x).is_integer()
    else:
        return False

# Check if a variable is a finite number or represents a finite number.
def is_finite_number(x):
    if is_number(x):
        return np.isfinite(float(x))
    else:
        return False

# Check if a variable is a NaN (not a number) or represents a NaN.
def is_nan(x):
    if is_number(x):
        return np.isnan(float(x))
    else:
        return False

# Cast a value to an integer if an integer, a float if a non-integer float, and an unknown value otherwise.
def cast_int_float_unknown(x):
    if is_integer(x):
        x = int(x)
    elif is_finite_number(x):
        x = float(x)
    elif is_number(x):
        x = 'Unknown'
    else:
        raise NotImplementedError(f'Unable to cast {x}.')
    return x

# Construct the one-hot encoding of data for the given classes.
def compute_one_hot_encoding(data, classes):
    num_instances = len(data)
    num_classes = len(classes)

    one_hot_encoding = np.zeros((num_instances, num_classes), dtype=np.bool_)
    unencoded_data = list()
    for i, x in enumerate(data):
        for y in x:
            for j, z in enumerate(classes):
                if (y == z) or (is_nan(y) and is_nan(z)):
                    one_hot_encoding[i, j] = 1

    return one_hot_encoding
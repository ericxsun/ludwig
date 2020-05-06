import os
import shutil
import sys

import numpy as np

from ludwig.api import LudwigModel
from ludwig.globals import MODEL_HYPERPARAMETERS_FILE_NAME, \
    TRAIN_SET_METADATA_FILE_NAME, MODEL_WEIGHTS_FILE_NAME
from ludwig.utils.data_utils import load_json


class LudwigNeuropodModelWrapper:
    def __init__(self, data_root):
        self.ludwig_model = LudwigModel.load(data_root)

    def __call__(self, **kwargs):
        print('__call__', file=sys.stderr)
        predicted = self.ludwig_model.predict(data_dict=kwargs,
                                              return_type=dict)
        print(predicted, file=sys.stderr)
        to_return = {}
        for output_feature_name in predicted:
            to_return[output_feature_name] = np.array(
                predicted[output_feature_name]['predictions'], dtype='str'
            )
        print(to_return, file=sys.stderr)
        return to_return


def get_model(data_root):
    print('get_model()', data_root, file=sys.stderr)
    return LudwigNeuropodModelWrapper(data_root)


def build_neuropod(
        ludwig_model_path,
        neuropod_path="/Users/piero/Desktop/neuropod",
        python_root="/Users/piero/Development/ludwig"
):
    from neuropod.backends.python.packager import create_python_neuropod

    data_paths = [
        {
            "path": os.path.join(
                ludwig_model_path, MODEL_HYPERPARAMETERS_FILE_NAME
            ),
            "packaged_name": MODEL_HYPERPARAMETERS_FILE_NAME
        },
        {
            "path": os.path.join(
                ludwig_model_path, TRAIN_SET_METADATA_FILE_NAME
            ),
            "packaged_name": TRAIN_SET_METADATA_FILE_NAME
        },
        {
            "path": os.path.join(
                ludwig_model_path, 'checkpoint'
            ),
            "packaged_name": 'checkpoint'
        },
    ]
    for filename in os.listdir(ludwig_model_path):
        if MODEL_WEIGHTS_FILE_NAME in filename:
            data_paths.append(
                {
                    "path": os.path.join(
                        ludwig_model_path, filename
                    ),
                    "packaged_name": filename
                }
            )

    ludwig_model_definition = load_json(
        os.path.join(
            ludwig_model_path,
            MODEL_HYPERPARAMETERS_FILE_NAME
        )
    )
    input_spec = []
    for feature in ludwig_model_definition['input_features']:
        input_spec.append({
            "name": feature['name'],
            "dtype": "str",
            "shape": (None,)
        })
    output_spec = []
    for feature in ludwig_model_definition['output_features']:
        output_spec.append({
            "name": feature['name'],
            "dtype": "str",
            "shape": (None,)
        })

    if os.path.exists(neuropod_path):
        if os.path.isfile(neuropod_path):
            os.remove(neuropod_path)
        else:
            shutil.rmtree(neuropod_path, ignore_errors=True)

    create_python_neuropod(
        neuropod_path=neuropod_path,
        model_name="ludwig_model",
        data_paths=data_paths,
        code_path_spec=[{
            "python_root": python_root,
            "dirs_to_package": [
                "ludwig"  # Package everything in the python_root
            ],
        }],
        entrypoint_package="ludwig.neuropod",
        entrypoint="get_model",
        # test_deps=['torch', 'numpy'],
        skip_virtualenv=True,
        input_spec=input_spec,
        output_spec=output_spec
    )
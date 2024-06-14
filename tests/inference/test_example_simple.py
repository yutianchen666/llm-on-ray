#
# Copyright 2023 The LLM-on-Ray Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import subprocess
import pytest
import os
from basic_set import start_serve


def script_with_args(
    script_name, base_url, model_name, streaming_response, max_new_tokens, temperature, top_p, top_k
):
    current_path = os.path.dirname(os.path.abspath(__file__))

    os.path.join(current_path, "../../.github/workflows/config/" + model_name + "-ci.yaml")

    example_query_single_path = os.path.join(
        current_path, f"../../examples/inference/api_server_simple/{script_name}"
    )

    cmd_single = [
        "python",
        example_query_single_path,
        "--model_endpoint",
        base_url + model_name,
    ]

    if streaming_response:
        cmd_single.append("--streaming_response")

    if max_new_tokens is not None:
        cmd_single.extend(["--max_new_tokens", str(max_new_tokens)])

    if temperature is not None:
        cmd_single.extend(["--temperature", str(temperature)])

    if top_p is not None:
        cmd_single.extend(["--top_p", str(top_p)])

    if top_k is not None:
        cmd_single.extend(["--top_k", str(top_k)])

    try:
        result_query_single = subprocess.run(cmd_single, capture_output=True, text=True, check=True)

        # Print the output of subprocess.run for checking if output is expected
        print("\n" + "Model in simple output message: " + "\n", result_query_single.stdout)

        assert isinstance(result_query_single.stdout, str), print(
            "\n" + "Simple output is nor string" + "\n"
        )

        assert len(result_query_single.stdout) > 0, print("\n" + "Simple output length is 0" + "\n")

    except subprocess.CalledProcessError as e:
        if "Internal Server Error" in e.stderr:
            print(e.stderr)
            # Find the latest Internal Server Error log file
            folder_path = "/tmp/ray/session_latest/logs/serve"
            latest_file = None
            latest_time = 0.0

            for file_name in os.listdir(folder_path):
                if file_name.startswith("replica") and file_name.endswith(".log"):
                    file_path = os.path.join(folder_path, file_name)
                    file_time = os.path.getmtime(file_path)
                    if file_time > latest_time:
                        latest_time = file_time
                        latest_file = file_path
            if latest_file:
                print("latest file:", latest_file)
                with open(latest_file, "r") as file:
                    lines = file.readlines()
                    if lines:
                        print("Latest Internal Server Error logs:", lines)
                    else:
                        print("Internal Server Error logs: Empty")
            assert False, print("Internal Server Error")
        else:
            # Returncode should be 0 when there is no errors in exception
            assert e.returncode == 0, print(
                "\n" + "Simple query error stderr message: " + "\n", e.stderr
            )


executed_models = []


# Parametrize the test function with different combinations of parameters
# TODO: more models and combinations will be added and tested.
@pytest.mark.parametrize(
    "script_name,base_url,model_name,streaming_response,max_new_tokens,temperature,top_p, top_k",
    [
        (
            script_name,
            base_url,
            model_name,
            streaming_response,
            max_new_tokens,
            temperature,
            top_p,
            top_k,
        )
        for script_name in ["query_single.py", "query_dynamic_batch.py"]
        for base_url in ["http://localhost:8000/"]
        for model_name in ["gpt2"]
        for streaming_response in [None]
        for max_new_tokens in [None]
        for temperature in [None]
        for top_p in [None]
        for top_k in [None]
    ],
)
def test_script(
    script_name, base_url, model_name, streaming_response, max_new_tokens, temperature, top_p, top_k
):
    global executed_models

    # Check if this modelname has already executed start_serve
    if model_name not in executed_models:
        start_serve(model_name, simple=True)
        # Mark this modelname has already executed start_serve
        executed_models.append(model_name)

    script_with_args(
        script_name,
        base_url,
        model_name,
        streaming_response,
        max_new_tokens,
        temperature,
        top_p,
        top_k,
    )

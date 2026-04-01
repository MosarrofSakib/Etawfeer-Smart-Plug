from Utils.utils import build_model, process_ssfl_data, process_raw_data
from sklearn.model_selection import train_test_split
import flwr as fl
import pandas as pd
from pathlib import Path
import os
import argparse

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'


root_dir = Path(__file__).resolve().parent

# Define Flower client


class QUDClient(fl.client.NumPyClient):
    def __init__(self, model, model_name, save_dir, x_train, y_train, x_test, y_test) -> None:
        self.model = model
        self.model_name = model_name
        self.save_dir = os.path.join(
            save_dir, f"{model_name}_final_global_model.keras")
        self.x_train, self.y_train = x_train, y_train
        self.x_test, self.y_test = x_test, y_test

    def get_parameters(self, config):
        # return self.model.get_weights()
        raise Exception(
            "Not implemented (server-side parameter initialization)")

    def fit(self, parameters, config):
        self.model.set_weights(parameters)

        # Save the final global model
        self.model.save(self.save_dir)

        batch_size = config['batch_size']
        epochs = config["local_epochs"]

        history = self.model.fit(
            self.x_train, self.y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=0.1)

        parameters_prime = self.model.get_weights()
        len_dataset = len(self.x_train)
        results = {
            "loss": history.history["loss"][0],
            "accuracy": history.history["accuracy"][0],
            "val_loss": history.history["val_loss"][0],
            "val_accuracy": history.history["val_accuracy"][0],
        }

        return parameters_prime, len_dataset, results

    def evaluate(self, parameters, config):
        self.model.set_weights(parameters)

        batch_size = config['batch_size']
        steps = config['val_steps']

        loss, accuracy = self.model.evaluate(
            self.x_test, self.y_test, batch_size, steps=steps)
        return loss, len(self.x_test), {"accuracy": accuracy, 'loss': loss}


def main() -> None:
    root_dir = Path(__file__).resolve().parent

    dataset_root = os.path.join(root_dir, "Dataset")

    # Parse arguments
    parser = argparse.ArgumentParser(description="Flower")
    parser.add_argument(
        "--client_id",
        type=int,
        choices=[1, 2, 3],
        default=1,
        help="The dataset is divided into 3 subsets for client training",
    )

    parser.add_argument(
        "--dataset",
        type=str,
        choices=["QUD", "DRED"],
        default="DRED",
        help="Choose the dataset from the options",
    )

    parser.add_argument(
        "--model_name",
        type=str,
        default="test_model4",
        help="Six model are available: ['test_model1', 'test_model2', 'test_model3', 'test_model4', 'test_model5', 'test_model6']",
    )

    parser.add_argument(
        "--stage",
        type=str,
        choices=["Pre", "Post"],
        default="Post",
        help="Choose the training stage from the options for SSFL, pre-deployment or post-deployment.",
    )

    parser.add_argument(
        "--raw_data_path",
        type=str,
        default=None,
        help="Path to raw collected data in HA (required only for Post stage)",
    )

    args, _ = parser.parse_known_args()

    if args.stage == "Pre":
        dataset_name = f"client_{args.client_id}_data.csv"

        dataset_path = os.path.join(dataset_root, "SSFL_DATA")

        data_path = os.path.join(
            dataset_path, f"{args.dataset}/{dataset_name}")

        data = process_ssfl_data(dataset_path, data_path)

    elif args.stage == "Post":
        dataset_name = "HA_Data"
        args.dataset = dataset_name
        HA_data_path = args.raw_data_path

        ha_data = process_raw_data(HA_data_path)

        dataset_path = os.path.join(dataset_root, "SSFL_DATA")

        data = process_ssfl_data(dataset_path, ha_data)

    print(f"#### Loading data from {dataset_name}")

    # load data

    data_input = data.iloc[:, :5].values
    data_label = data.iloc[:, -1].values

    x_train, x_test, y_train, y_test = train_test_split(
        data_input, data_label, test_size=0.1, random_state=0)

    # model
    model_name = args.model_name
    input_shape = (x_train.shape[1], )
    model = build_model(input_shape, model_name)

    save_dir = os.path.join(root_dir, "Results",
                            args.dataset, f"Client_{args.client_id}", args.model_name)

    os.makedirs(save_dir, exist_ok=True)

    client = QUDClient(model=model, model_name=model_name, save_dir=save_dir, x_train=x_train,
                       y_train=y_train, x_test=x_test, y_test=y_test)

    fl.client.start_client(
        server_address='127.0.0.1:8080',
        client=client.to_client(),
        # insecure=False
    )


if __name__ == "__main__":
    main()

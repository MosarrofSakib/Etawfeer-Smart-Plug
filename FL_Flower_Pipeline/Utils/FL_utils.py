import os
import tensorflow as tf

import flwr as fl
import pandas as pd
from typing import List, Tuple, Type, Dict, Optional
from pathlib import Path


class SaveModelStrategy(fl.server.strategy.Strategy):
    def __init__(self, strategy_instance: fl.server.strategy.Strategy, client_metrics: Dict[int, Dict[str, List[float]]]):
        self.strategy_instance = strategy_instance
        self.client_metrics = client_metrics

    def aggregate_fit(
        self,
        rnd: int,
        results: List[Tuple[fl.server.client_proxy.ClientProxy, fl.common.FitRes]],
        failures: List[BaseException],
    ) -> fl.common.Parameters:
        # Aggregate training metrics
        aggregated_weights = self.strategy_instance.aggregate_fit(
            rnd, results, failures)

        # Log metrics
        if results:
            # Average client loss and accuracy for this round
            loss = sum(fit_res.metrics["loss"]
                       for _, fit_res in results) / len(results)
            accuracy = sum(fit_res.metrics["accuracy"]
                           for _, fit_res in results) / len(results)
            print(f"Round {rnd} - Loss: {loss}, Accuracy: {accuracy}")

            # Store client metrics for each round
            for i, (_, fit_res) in enumerate(results):
                client_id = i
                self.client_metrics[client_id]["loss"].append(
                    fit_res.metrics["loss"])
                self.client_metrics[client_id]["accuracy"].append(
                    fit_res.metrics["accuracy"])

        return aggregated_weights

    def initialize_parameters(self, client_manager: fl.server.client_manager.ClientManager) -> Optional[fl.common.Parameters]:
        return self.strategy_instance.initialize_parameters(client_manager)

    def configure_fit(
        self,
        server_round: int,
        parameters: fl.common.Parameters,
        client_manager: fl.server.client_manager.ClientManager,
    ) -> List[Tuple[fl.server.client_proxy.ClientProxy, fl.common.FitIns]]:
        return self.strategy_instance.configure_fit(server_round, parameters, client_manager)

    def aggregate_evaluate(
        self,
        rnd: int,
        results: List[Tuple[fl.server.client_proxy.ClientProxy, fl.common.EvaluateRes]],
        failures: List[BaseException],
    ) -> Optional[float]:
        return self.strategy_instance.aggregate_evaluate(rnd, results, failures)

    def configure_evaluate(
        self,
        server_round: int,
        parameters: fl.common.Parameters,
        client_manager: fl.server.client_manager.ClientManager,
    ) -> List[Tuple[fl.server.client_proxy.ClientProxy, fl.common.EvaluateIns]]:
        return self.strategy_instance.configure_evaluate(server_round, parameters, client_manager)

    def evaluate(
        self,
        server_round: int,
        parameters: fl.common.Parameters,
    ) -> Optional[Tuple[float, Dict[str, fl.common.Scalar]]]:
        return self.strategy_instance.evaluate(server_round, parameters)

# Universal function to initialize SaveModelStrategy with different strategies


def get_evaluate_fn(model, global_loss, global_accuracy, dataset):
    """Return an evaluation function for server-side evaluation."""
    root_dir = Path(__file__).resolve().parent.parent
    file_path_qud = os.path.join(
        root_dir, f"Dataset/data_com_glob_test.csv")

    # load data
    df_qud = pd.read_csv(file_path_qud)
    x_test = df_qud.iloc[:, :-1].values
    y_test = df_qud.iloc[:, -1].values

    def evaluate(server_round: int, parameters: fl.common.NDArrays, config: Dict[str, fl.common.Scalar]):
        model.set_weights(parameters)
        loss, accuracy = model.evaluate(x_test, y_test)

        # Log metrics
        global_loss.append(loss)
        global_accuracy.append(accuracy)

        return loss, {"accuracy": accuracy}

    return evaluate


def fit_config(server_round: int):
    config = {
        "batch_size": 32,
        "local_epochs": 10 if server_round < 2 else 5,
    }
    return config


def evaluate_config(server_round: int):
    val_steps = 5 if server_round < 4 else 10
    return {"batch_size": 32, "val_steps": val_steps}


def create_strategy(strategy_class: Type[fl.server.strategy.Strategy], client_metrics: Dict[int, Dict[str, List[float]]], *args, **kwargs) -> SaveModelStrategy:
    strategy_instance = strategy_class(*args, **kwargs)
    return SaveModelStrategy(strategy_instance, client_metrics)


def create_server_strategy(fed_strategy: str, client_metrics: Dict[int, Dict[str, List[float]]],
                           num_clients: int, model: Type[tf.keras.Model],
                           global_loss: List[float], global_accuracy: List[float], dataset: str):

    if fed_strategy == 'FedAvg':
        strategy = create_strategy(
            fl.server.strategy.FedAvg,
            client_metrics,
            min_fit_clients=num_clients,
            min_evaluate_clients=num_clients,
            min_available_clients=num_clients,
            evaluate_fn=get_evaluate_fn(
                model, global_loss, global_accuracy, dataset),
            on_fit_config_fn=fit_config,
            on_evaluate_config_fn=evaluate_config,
            initial_parameters=fl.common.ndarrays_to_parameters(
                model.get_weights()),
        )
    elif fed_strategy == "FedProx":
        strategy = create_strategy(
            fl.server.strategy.FedProx,
            client_metrics,
            min_fit_clients=num_clients,
            min_evaluate_clients=num_clients,
            min_available_clients=num_clients,
            evaluate_fn=get_evaluate_fn(
                model, global_loss, global_accuracy, dataset),
            on_fit_config_fn=fit_config,
            on_evaluate_config_fn=evaluate_config,
            initial_parameters=fl.common.ndarrays_to_parameters(
                model.get_weights()),
            proximal_mu=0.5
        )
    elif fed_strategy == "FedMedian":
        strategy = create_strategy(
            fl.server.strategy.FedMedian,
            client_metrics,
            min_fit_clients=num_clients,
            min_evaluate_clients=num_clients,
            min_available_clients=num_clients,
            evaluate_fn=get_evaluate_fn(
                model, global_loss, global_accuracy, dataset),
            on_fit_config_fn=fit_config,
            on_evaluate_config_fn=evaluate_config,
            initial_parameters=fl.common.ndarrays_to_parameters(
                model.get_weights()),
        )
    elif fed_strategy == "FedTrimmedAvg":
        strategy = create_strategy(
            fl.server.strategy.FedTrimmedAvg,
            client_metrics,
            min_fit_clients=num_clients,
            min_evaluate_clients=num_clients,
            min_available_clients=num_clients,
            evaluate_fn=get_evaluate_fn(
                model, global_loss, global_accuracy, dataset),
            on_fit_config_fn=fit_config,
            on_evaluate_config_fn=evaluate_config,
            initial_parameters=fl.common.ndarrays_to_parameters(
                model.get_weights()),
        )
    elif fed_strategy == "Krum":
        strategy = create_strategy(
            fl.server.strategy.Krum,
            client_metrics,
            min_fit_clients=num_clients,
            min_evaluate_clients=num_clients,
            min_available_clients=num_clients,
            evaluate_fn=get_evaluate_fn(
                model, global_loss, global_accuracy, dataset),
            on_fit_config_fn=fit_config,
            on_evaluate_config_fn=evaluate_config,
            initial_parameters=fl.common.ndarrays_to_parameters(
                model.get_weights()),
        )
    else:
        print("Not Apllicable!")

    return strategy
